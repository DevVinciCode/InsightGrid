import { useState } from 'react'

export default function DatasetExplorer({
  dbStatus,
  onOpenConnectModal,
  onUseDemo,
  onPreviewTable,
  onAskQuestion,
}) {
  const [expandedTables, setExpandedTables] = useState({})
  const [search, setSearch] = useState('')

  function toggleTable(tName) {
    setExpandedTables((prev) => ({ ...prev, [tName]: !prev[tName] }))
  }

  const summaries = dbStatus?.table_summaries || []
  const filteredSummaries = summaries.filter((t) =>
    search === '' ? true : t.name.toLowerCase().includes(search.toLowerCase())
  )

  const isDemo = dbStatus?.kind === 'demo'

  return (
    <aside className="w-80 bg-white border-r border-slate-200 flex flex-col h-full shrink-0 select-none">
      {/* Header */}
      <div className="p-4 border-b border-slate-100 bg-slate-50/50">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-800">Dataset Explorer</span>
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
          </div>
          <button
            onClick={onOpenConnectModal}
            className="text-[11px] bg-indigo-50 hover:bg-indigo-100 text-indigo-600 font-medium px-2.5 py-1 rounded-md border border-indigo-200 transition cursor-pointer"
          >
            + Connect DB
          </button>
        </div>

        {/* Active Database Card */}
        <div className="bg-white border border-slate-200/90 rounded-xl p-3 shadow-xs">
          <div className="flex items-start justify-between">
            <div className="overflow-hidden pr-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 truncate">
                <span className="text-slate-400">📁</span>
                <span className="truncate" title={dbStatus?.label || 'Database'}>
                  {dbStatus?.label || 'Loading...'}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[10px] uppercase tracking-wider font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                  {isDemo ? 'Demo SQLite' : dbStatus?.kind === 'postgresql' ? 'PostgreSQL' : 'Uploaded Dataset'}
                </span>
              </div>
            </div>
            {!isDemo && (
              <button
                onClick={onUseDemo}
                className="text-[10px] text-slate-500 hover:text-indigo-600 hover:underline shrink-0 cursor-pointer"
                title="Revert back to standard demo dataset"
              >
                Use Demo
              </button>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2 mt-2.5 pt-2 border-t border-slate-100 text-[11px] text-slate-600">
            <div>
              <span className="text-slate-400 block text-[10px]">Tables</span>
              <span className="font-semibold text-slate-800 font-mono">
                {summaries.length}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">Total Records</span>
              <span className="font-semibold text-slate-800 font-mono">
                {dbStatus?.total_rows ? dbStatus.total_rows.toLocaleString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Table Search */}
      <div className="px-3 pt-3 pb-2 border-b border-slate-100">
        <input
          type="text"
          placeholder="Filter tables..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full text-xs px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400"
        />
      </div>

      {/* Tables list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {filteredSummaries.length === 0 ? (
          <div className="p-4 text-center text-xs text-slate-400">
            {summaries.length === 0 ? 'No tables found in this dataset.' : 'No matching tables.'}
          </div>
        ) : (
          filteredSummaries.map((table) => {
            const isExpanded = !!expandedTables[table.name]
            return (
              <div
                key={table.name}
                className="bg-white border border-slate-100 hover:border-slate-200 rounded-xl overflow-hidden shadow-2xs transition"
              >
                {/* Table Header Row */}
                <div className="flex items-center justify-between p-2.5 hover:bg-slate-50/70 transition">
                  <button
                    onClick={() => toggleTable(table.name)}
                    className="flex items-center gap-2 text-left flex-1 min-w-0 cursor-pointer"
                  >
                    <span className="text-[10px] text-slate-400 font-mono">
                      {isExpanded ? '▼' : '▶'}
                    </span>
                    <span className="text-xs font-mono font-medium text-slate-800 truncate" title={table.name}>
                      {table.name}
                    </span>
                    <span className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded font-mono shrink-0">
                      {table.row_count.toLocaleString()}
                    </span>
                  </button>

                  <div className="flex items-center gap-1 shrink-0 ml-1">
                    <button
                      onClick={() => onPreviewTable(table.name)}
                      className="text-[11px] p-1 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition cursor-pointer"
                      title={`Preview data rows from ${table.name}`}
                    >
                      👁
                    </button>
                  </div>
                </div>

                {/* Expanded Columns Drawer */}
                {isExpanded && (
                  <div className="bg-slate-50/80 px-3 py-2 border-t border-slate-100 text-[11px] space-y-1">
                    <div className="flex items-center justify-between text-[10px] text-slate-400 pb-1 mb-1 border-b border-slate-200/60 font-semibold uppercase">
                      <span>Columns ({table.columns.length})</span>
                      <button
                        onClick={() => onAskQuestion(`Show me the first 10 rows from ${table.name}`)}
                        className="text-indigo-600 hover:underline capitalize"
                      >
                        Sample rows
                      </button>
                    </div>
                    {table.columns.map((colName) => (
                      <div
                        key={colName}
                        onClick={() => onAskQuestion(`Show values of column ${colName} from table ${table.name}`)}
                        className="flex items-center justify-between py-0.5 text-slate-600 hover:text-indigo-600 cursor-pointer group"
                      >
                        <span className="font-mono text-[11px] truncate" title={colName}>
                          • {colName}
                        </span>
                        <span className="text-[9px] text-slate-400 opacity-0 group-hover:opacity-100 transition">
                          query ↗
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-100 bg-slate-50 text-[11px] text-slate-400 flex items-center justify-between">
        <span>NLP RAG Schema Sync</span>
        <span className="text-emerald-600 font-medium font-mono text-[10px]">● Synced</span>
      </div>
    </aside>
  )
}
