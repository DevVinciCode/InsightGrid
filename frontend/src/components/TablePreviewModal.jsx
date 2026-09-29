import { useEffect, useState } from 'react'
import { getTablePreview } from '../services/api'

export default function TablePreviewModal({ tableName, onClose, onAskAboutTable }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [searchTerm, setSearchTerm] = useState('')
  const [activeTab, setActiveTab] = useState('data') // 'data' | 'schema'

  useEffect(() => {
    if (!tableName) return
    setLoading(true)
    setError('')
    getTablePreview(tableName, 30)
      .then(setData)
      .catch((err) => setError(err.message || 'Failed to load preview'))
      .finally(() => setLoading(false))
  }, [tableName])

  const filteredRows = data?.rows?.filter((row) =>
    searchTerm === ''
      ? true
      : row.some((val) => String(val ?? '').toLowerCase().includes(searchTerm.toLowerCase()))
  ) || []

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/70">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-mono font-bold text-sm">
              ⊞
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-slate-800 text-base">{tableName}</h3>
                {data && (
                  <span className="text-xs bg-indigo-100 text-indigo-700 font-medium px-2 py-0.5 rounded-full">
                    {data.row_count.toLocaleString()} rows
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {data?.description || `Live table in connected database with ${data?.columns?.length || 0} columns`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {onAskAboutTable && (
              <button
                onClick={() => {
                  onClose()
                  onAskAboutTable(`Show me a summary of the ${tableName} table`)
                }}
                className="text-xs bg-indigo-50 text-indigo-600 hover:bg-indigo-100 border border-indigo-200 px-3 py-1.5 rounded-lg font-medium transition cursor-pointer"
              >
                ✨ Query this table
              </button>
            )}
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition cursor-pointer"
              title="Close modal"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Tab switch & filter */}
        <div className="flex items-center justify-between px-6 py-2.5 bg-white border-b border-slate-100 text-xs">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('data')}
              className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
                activeTab === 'data'
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Data Sample (first 30 rows)
            </button>
            <button
              onClick={() => setActiveTab('schema')}
              className={`px-3 py-1.5 rounded-lg font-medium transition cursor-pointer ${
                activeTab === 'schema'
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Columns & Schema ({data?.columns?.length || 0})
            </button>
          </div>

          {activeTab === 'data' && (
            <input
              type="text"
              placeholder="Filter preview rows..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="border border-slate-200 rounded-lg px-3 py-1 text-xs focus:outline-none focus:border-indigo-400 w-52"
            />
          )}
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-auto p-6 bg-slate-50/30">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400 text-sm">
              <div className="w-7 h-7 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mb-3" />
              Loading table data...
            </div>
          )}

          {error && (
            <div className="bg-red-50 text-red-700 border border-red-200 p-4 rounded-xl text-sm">
              {error}
            </div>
          )}

          {!loading && !error && activeTab === 'data' && (
            <div className="border border-slate-200 rounded-xl overflow-hidden shadow-xs bg-white">
              <div className="overflow-x-auto max-h-[50vh]">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-100/80 sticky top-0 border-b border-slate-200 text-slate-600 font-medium">
                    <tr>
                      <th className="px-3 py-2 text-slate-400 font-mono w-10 text-center">#</th>
                      {data?.columns?.map((col) => (
                        <th key={col} className="px-3 py-2 font-mono whitespace-nowrap">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredRows.length === 0 ? (
                      <tr>
                        <td
                          colSpan={(data?.columns?.length || 0) + 1}
                          className="px-4 py-8 text-center text-slate-400"
                        >
                          No matching rows found
                        </td>
                      </tr>
                    ) : (
                      filteredRows.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-50 transition">
                          <td className="px-3 py-2 text-slate-400 font-mono text-center bg-slate-50/50">
                            {idx + 1}
                          </td>
                          {row.map((cell, cIdx) => (
                            <td
                              key={cIdx}
                              className="px-3 py-2 text-slate-700 font-mono whitespace-nowrap max-w-xs truncate"
                              title={String(cell ?? '')}
                            >
                              {cell === null ? (
                                <span className="text-slate-300 italic">null</span>
                              ) : (
                                String(cell)
                              )}
                            </td>
                          ))}
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {!loading && !error && activeTab === 'schema' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {data?.column_details?.map((col) => (
                <div
                  key={col.name}
                  className="bg-white border border-slate-200 rounded-xl p-3.5 flex flex-col justify-between hover:border-slate-300 transition"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-slate-800 text-xs">
                        {col.name}
                      </span>
                      {col.primary_key && (
                        <span className="text-[10px] bg-amber-100 text-amber-800 font-semibold px-1.5 py-0.5 rounded">
                          PK
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] font-mono text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md font-medium">
                      {col.type || 'TEXT'}
                    </span>
                  </div>
                  {col.sample_values && col.sample_values.length > 0 && (
                    <div className="text-[11px] text-slate-500 mt-1">
                      <span className="text-slate-400">Samples: </span>
                      <span className="font-mono text-slate-600">
                        {col.sample_values.map((v) => JSON.stringify(v)).join(', ')}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50/50 flex justify-between items-center text-xs text-slate-500">
          <span>
            Showing up to 30 sample rows from table <code className="text-slate-700 font-semibold">{tableName}</code>
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-lg font-medium transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
