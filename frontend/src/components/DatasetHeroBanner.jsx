export default function DatasetHeroBanner({
  dbStatus,
  demoQuestions,
  onAskQuestion,
  onPreviewTable,
  onOpenConnectModal,
}) {
  const isDemo = dbStatus?.kind === 'demo'
  const summaries = dbStatus?.table_summaries || []
  const totalRows = dbStatus?.total_rows || 0

  return (
    <div className="max-w-3xl mx-auto my-6 space-y-5 animate-in fade-in duration-200">
      {/* Active Dataset Highlight Card */}
      <div className="bg-gradient-to-br from-white to-indigo-50/40 border border-indigo-100/80 rounded-2xl p-5 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-indigo-100/60">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-indigo-600 text-white flex items-center justify-center text-xl shadow-sm shrink-0">
              📊
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 border border-indigo-200/60 px-2 py-0.5 rounded-full">
                  {isDemo ? 'Demo Database' : 'Custom Uploaded Dataset'}
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] text-emerald-600 font-medium">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                  Active & Ready
                </span>
              </div>
              <h2 className="text-lg font-bold text-slate-900 mt-0.5 truncate max-w-md">
                {dbStatus?.label || 'Connected Database'}
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onOpenConnectModal}
              className="text-xs bg-white hover:bg-slate-50 text-slate-700 font-medium px-3 py-1.5 rounded-xl border border-slate-200 transition cursor-pointer shadow-2xs"
            >
              Change Dataset
            </button>
          </div>
        </div>

        {/* Tables & Record Summary */}
        <div className="pt-3">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span>
              Available Tables ({summaries.length}) •{' '}
              <strong className="text-slate-700 font-semibold">{totalRows.toLocaleString()}</strong> total rows
            </span>
            <span className="text-[11px] text-indigo-600 font-medium">Click any table to preview live rows</span>
          </div>

          <div className="flex flex-wrap gap-2">
            {summaries.length === 0 ? (
              <span className="text-xs text-slate-400">Loading tables...</span>
            ) : (
              summaries.map((table) => (
                <button
                  key={table.name}
                  onClick={() => onPreviewTable(table.name)}
                  className="group flex items-center gap-2 bg-white hover:bg-indigo-50/80 border border-slate-200 hover:border-indigo-300 rounded-xl px-3 py-1.5 text-xs transition cursor-pointer shadow-2xs"
                  title={`Click to preview rows from ${table.name}`}
                >
                  <span className="font-mono font-medium text-slate-800 group-hover:text-indigo-700">
                    {table.name}
                  </span>
                  <span className="text-[10px] bg-slate-100 group-hover:bg-indigo-100 text-slate-600 group-hover:text-indigo-700 font-mono px-1.5 py-0.2 rounded-md">
                    {table.row_count.toLocaleString()} rows
                  </span>
                  <span className="text-[10px] text-slate-400 group-hover:text-indigo-600">
                    👁
                  </span>
                </button>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Suggested Questions */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-2xs space-y-4">
        <div>
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Suggested Questions for this Dataset
            </h3>
            <span className="text-[11px] text-slate-400">Click to run immediately</span>
          </div>
          <div className="flex flex-wrap gap-2 mt-2.5">
            {demoQuestions?.questions?.map((q) => (
              <button
                key={q}
                onClick={() => onAskQuestion(q)}
                className="text-xs bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 text-slate-700 hover:text-indigo-700 rounded-xl px-3.5 py-2 transition text-left cursor-pointer shadow-2xs font-normal"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {demoQuestions?.ambiguous_examples?.length > 0 && (
          <div className="pt-2 border-t border-slate-100">
            <h4 className="text-[11px] font-medium text-amber-700 mb-2">
              Exploratory / Multi-dimensional queries:
            </h4>
            <div className="flex flex-wrap gap-2">
              {demoQuestions.ambiguous_examples.map((q) => (
                <button
                  key={q}
                  onClick={() => onAskQuestion(q)}
                  className="text-xs bg-amber-50/70 hover:bg-amber-100/80 border border-amber-200/80 text-amber-800 rounded-xl px-3 py-1.5 transition text-left cursor-pointer"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
