import { useState, useMemo } from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const PALETTE = [
  '#6366f1', // indigo
  '#06b6d4', // cyan
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ec4899', // pink
  '#8b5cf6', // purple
  '#3b82f6', // blue
  '#f43f5e', // rose
]

function formatNumber(num) {
  if (num === null || num === undefined || isNaN(num)) return '—'
  const val = Number(num)
  if (Math.abs(val) >= 1_000_000) {
    return (val / 1_000_000).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 }) + 'M'
  }
  if (Math.abs(val) >= 1_000) {
    return (val / 1_000).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 }) + 'k'
  }
  return val.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null
  return (
    <div className="bg-slate-900 text-white rounded-xl px-3.5 py-2.5 shadow-xl text-xs border border-slate-700 backdrop-blur-xs">
      <p className="font-semibold text-slate-300 mb-1 border-b border-slate-800 pb-1">{label || payload[0]?.name}</p>
      {payload.map((entry, idx) => (
        <div key={idx} className="flex items-center justify-between gap-4 py-0.5">
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color || entry.payload?.fill || '#6366f1' }} />
            {entry.name || 'Value'}:
          </span>
          <span className="font-mono font-bold text-white">
            {typeof entry.value === 'number' ? entry.value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : entry.value}
          </span>
        </div>
      ))}
    </div>
  )
}

export default function ChartView({ columns, rows, spec }) {
  if (!rows || rows.length === 0 || !columns || columns.length === 0) return null

  // 1. Identify numeric vs categorical columns
  const colAnalysis = useMemo(() => {
    return columns.map((col, idx) => {
      let numericCount = 0
      rows.forEach((r) => {
        const val = r[idx]
        if (val !== null && val !== undefined && val !== '' && !isNaN(Number(val))) {
          numericCount++
        }
      })
      const isNum = numericCount / rows.length >= 0.7
      return { col, idx, isNum }
    })
  }, [columns, rows])

  const numCols = colAnalysis.filter((c) => c.isNum).map((c) => c.col)
  const catCols = colAnalysis.filter((c) => !c.isNum).map((c) => c.col)

  // 2. Select initial X and Y columns
  const initialX = useMemo(() => {
    if (spec?.x && columns.includes(spec.x)) return spec.x
    if (catCols.length > 0) return catCols[0]
    return columns[0]
  }, [spec, columns, catCols])

  const initialY = useMemo(() => {
    if (spec?.y && columns.includes(spec.y) && spec.y !== initialX) return spec.y
    if (numCols.length > 0) {
      const match = numCols.find((c) => c !== initialX)
      if (match) return match
    }
    return columns.length > 1 ? columns[1] : columns[0]
  }, [spec, columns, numCols, initialX])

  const [selectedX, setSelectedX] = useState(initialX)
  const [selectedY, setSelectedY] = useState(initialY)

  // Default chart type from spec or heuristic
  const defaultChartType = useMemo(() => {
    const rawType = spec?.chart_type?.toLowerCase() || 'bar'
    if (rawType === 'table') {
      if (rows.length > 1 && numCols.length > 0) {
        return 'bar'
      }
      return 'table'
    }
    if (['line', 'area', 'bar', 'horizontal_bar', 'donut', 'pie'].includes(rawType)) {
      return rawType === 'pie' ? 'donut' : rawType
    }
    const isTime = /(date|month|year|period|day|time)/i.test(selectedX)
    return isTime ? 'area' : 'bar'
  }, [spec, rows.length, numCols.length, selectedX])

  const [chartType, setChartType] = useState(defaultChartType)

  // 3. Shape data for Recharts
  const chartData = useMemo(() => {
    const xIdx = columns.indexOf(selectedX)
    const yIdx = columns.indexOf(selectedY)

    return rows.map((r, i) => {
      const xVal = xIdx >= 0 ? r[xIdx] : `Item ${i + 1}`
      const rawY = yIdx >= 0 ? r[yIdx] : 0
      const yVal = rawY !== null && !isNaN(Number(rawY)) ? Number(rawY) : 0
      return {
        name: String(xVal ?? '—'),
        [selectedY]: yVal,
        value: yVal, // for pie/donut
      }
    })
  }, [columns, rows, selectedX, selectedY])

  // 4. Compute Summary KPI Metrics
  const metrics = useMemo(() => {
    const values = chartData.map((d) => d[selectedY]).filter((v) => typeof v === 'number' && !isNaN(v))
    if (values.length === 0) return null

    const total = values.reduce((a, b) => a + b, 0)
    const avg = total / values.length
    let maxItem = chartData[0]
    let minItem = chartData[0]

    chartData.forEach((d) => {
      if (d[selectedY] > (maxItem?.[selectedY] ?? -Infinity)) maxItem = d
      if (d[selectedY] < (minItem?.[selectedY] ?? Infinity)) minItem = d
    })

    // Trend Delta for 2 points (e.g. May vs June)
    let deltaPct = null
    if (chartData.length === 2 && chartData[0][selectedY] > 0) {
      const v0 = chartData[0][selectedY]
      const v1 = chartData[1][selectedY]
      deltaPct = ((v1 - v0) / v0) * 100
    }

    return { total, avg, maxItem, minItem, count: values.length, deltaPct }
  }, [chartData, selectedY])

  // CSV Export
  function exportCSV() {
    const headers = columns.join(',')
    const csvRows = rows.map((r) => r.map((c) => `"${String(c ?? '').replace(/"/g, '""')}"`).join(','))
    const blob = new Blob([[headers, ...csvRows].join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `query_result_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="w-full bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden my-3 animate-in fade-in duration-200">
      {/* Top Chart Header & Controls */}
      <div className="px-5 py-3.5 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-3 bg-slate-50/50">
        <div>
          <h3 className="font-semibold text-slate-800 text-sm">
            {spec?.title || `${selectedY.replace(/_/g, ' ')} by ${selectedX.replace(/_/g, ' ')}`}
          </h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Interactive visualization with {rows.length} data point{rows.length !== 1 ? 's' : ''}
          </p>
        </div>

        {/* Chart Type Toggle Tabs */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <div className="flex bg-slate-200/70 p-0.5 rounded-xl text-xs font-medium">
            <button
              onClick={() => setChartType('bar')}
              className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
                chartType === 'bar' ? 'bg-white text-indigo-600 shadow-2xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Bar Chart"
            >
              📊 Bar
            </button>
            <button
              onClick={() => setChartType('line')}
              className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
                chartType === 'line' ? 'bg-white text-indigo-600 shadow-2xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Line Chart"
            >
              📈 Line
            </button>
            <button
              onClick={() => setChartType('area')}
              className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
                chartType === 'area' ? 'bg-white text-indigo-600 shadow-2xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Area Chart"
            >
              🌊 Area
            </button>
            <button
              onClick={() => setChartType('donut')}
              className={`px-2.5 py-1 rounded-lg transition cursor-pointer ${
                chartType === 'donut' ? 'bg-white text-indigo-600 shadow-2xs font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
              title="Donut Chart"
            >
              🍩 Donut
            </button>
          </div>

          {/* Axis Dropdowns */}
          {columns.length > 2 && (
            <div className="flex items-center gap-1.5 text-xs text-slate-500 pl-1">
              <select
                value={selectedY}
                onChange={(e) => setSelectedY(e.target.value)}
                className="bg-white border border-slate-200 rounded-lg px-2 py-1 text-xs focus:outline-none focus:border-indigo-400 font-mono text-slate-700"
              >
                {numCols.map((c) => (
                  <option key={c} value={c}>
                    Metric: {c}
                  </option>
                ))}
              </select>
            </div>
          )}

          <button
            onClick={exportCSV}
            className="text-[11px] p-1.5 text-slate-500 hover:text-indigo-600 hover:bg-white rounded-lg border border-slate-200 transition cursor-pointer shrink-0"
            title="Export CSV"
          >
            📥 CSV
          </button>
        </div>
      </div>

      {/* KPI Metric Summary Strip */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 px-5 py-2.5 bg-slate-50/30 border-b border-slate-100 text-xs">
          <div className="bg-white border border-slate-100 rounded-xl px-3 py-2">
            <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">Total</span>
            <span className="font-bold text-slate-800 font-mono text-sm">
              {formatNumber(metrics.total)}
            </span>
          </div>

          <div className="bg-white border border-slate-100 rounded-xl px-3 py-2">
            <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">Average</span>
            <span className="font-bold text-slate-800 font-mono text-sm">
              {formatNumber(metrics.avg)}
            </span>
          </div>

          <div className="bg-white border border-slate-100 rounded-xl px-3 py-2 truncate">
            <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">Peak</span>
            <span className="font-bold text-emerald-600 font-mono text-sm truncate block" title={`${metrics.maxItem?.name}: ${metrics.maxItem?.[selectedY]}`}>
              {formatNumber(metrics.maxItem?.[selectedY])} <span className="text-[10px] text-slate-400 font-normal">({metrics.maxItem?.name})</span>
            </span>
          </div>

          <div className="bg-white border border-slate-100 rounded-xl px-3 py-2">
            <span className="text-[10px] text-slate-400 block uppercase tracking-wider font-semibold">
              {metrics.deltaPct !== null ? 'Period Delta' : 'Data Points'}
            </span>
            {metrics.deltaPct !== null ? (
              <span className={`font-bold font-mono text-sm ${metrics.deltaPct >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                {metrics.deltaPct >= 0 ? '▲ +' : '▼ '}
                {metrics.deltaPct.toFixed(1)}%
              </span>
            ) : (
              <span className="font-bold text-slate-800 font-mono text-sm">
                {metrics.count} points
              </span>
            )}
          </div>
        </div>
      )}

      {/* Main Chart Canvas */}
      <div className="p-5 h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'area' ? (
            <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 25 }}>
              <defs>
                <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11, fill: '#64748b' }}
                stroke="#cbd5e1"
                angle={chartData.length > 6 ? -25 : 0}
                textAnchor={chartData.length > 6 ? 'end' : 'middle'}
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#64748b' }}
                stroke="#cbd5e1"
                tickFormatter={formatNumber}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey={selectedY}
                stroke="#6366f1"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#areaGradient)"
              />
            </AreaChart>
          ) : chartType === 'line' ? (
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11, fill: '#64748b' }}
                stroke="#cbd5e1"
                angle={chartData.length > 6 ? -25 : 0}
                textAnchor={chartData.length > 6 ? 'end' : 'middle'}
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#64748b' }}
                stroke="#cbd5e1"
                tickFormatter={formatNumber}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey={selectedY}
                stroke="#6366f1"
                strokeWidth={2.5}
                dot={{ r: 4, fill: '#6366f1', strokeWidth: 2, stroke: '#fff' }}
                activeDot={{ r: 6, fill: '#4f46e5' }}
              />
            </LineChart>
          ) : chartType === 'donut' ? (
            <PieChart>
              <Tooltip content={<CustomTooltip />} />
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={95}
                paddingAngle={3}
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={PALETTE[index % PALETTE.length]}
                    stroke="#fff"
                    strokeWidth={2}
                  />
                ))}
              </Pie>
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(val) => <span className="text-xs text-slate-600 font-medium">{val}</span>}
              />
            </PieChart>
          ) : (
            /* Bar Chart (Default) */
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis
                dataKey="name"
                tick={{ fontSize: 11, fill: '#64748b' }}
                stroke="#cbd5e1"
                angle={chartData.length > 6 ? -25 : 0}
                textAnchor={chartData.length > 6 ? 'end' : 'middle'}
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#64748b' }}
                stroke="#cbd5e1"
                tickFormatter={formatNumber}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey={selectedY}
                fill="#6366f1"
                radius={[6, 6, 0, 0]}
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={chartData.length <= 8 ? PALETTE[index % PALETTE.length] : '#6366f1'}
                  />
                ))}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  )
}
