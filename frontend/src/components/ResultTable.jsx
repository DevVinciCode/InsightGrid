export default function ResultTable({ columns, rows, truncated }) {
  if (!columns || columns.length === 0) return null
  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-auto max-h-80">
      <table className="w-full text-sm text-left">
        <thead className="bg-slate-50 sticky top-0">
          <tr>
            {columns.map((c) => (
              <th key={c} className="px-3 py-2 font-medium text-slate-500 border-b border-slate-200">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="hover:bg-slate-50">
              {row.map((val, j) => (
                <td key={j} className="px-3 py-1.5 border-b border-slate-100 text-slate-700">
                  {val === null ? <span className="text-slate-300">null</span> : String(val)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {truncated && (
        <p className="text-xs text-amber-600 px-3 py-2 bg-amber-50">Results truncated to the row limit.</p>
      )}
    </div>
  )
}
