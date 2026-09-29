import { useState } from 'react'

const TABS = ['Intent', 'Retrieved Context', 'SQL', 'Validation', 'Confidence', 'Provenance']

function ConfidenceBar({ label, value }) {
  const pct = Math.round(value * 100)
  const color = pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-500'
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs text-slate-500 mb-0.5">
        <span>{label}</span><span>{pct}%</span>
      </div>
      <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function DevPanel({ turn }) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState('Intent')
  if (!turn) return null

  return (
    <div className="mt-3 border border-slate-200 rounded-xl bg-white">
      <button
        className="w-full flex justify-between items-center px-4 py-2 text-sm font-medium text-slate-600"
        onClick={() => setOpen(!open)}
      >
        <span>Research / Developer Panel</span>
        <span>{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="border-t border-slate-100">
          <div className="flex gap-1 px-3 pt-2 flex-wrap">
            {TABS.map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`text-xs px-2.5 py-1 rounded-full ${
                  tab === t ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
          <div className="p-4 text-xs font-mono whitespace-pre-wrap text-slate-700 max-h-72 overflow-auto">
            {tab === 'Intent' && JSON.stringify(turn.intent, null, 2)}
            {tab === 'Retrieved Context' &&
              turn.provenance.retrieved_documents
                .map((d) => `[${d.kind} | score=${d.score.toFixed(2)}]\n${d.text}`)
                .join('\n\n---\n\n')}
            {tab === 'SQL' && turn.sql}
            {tab === 'Validation' &&
              (turn.validation_issues.length
                ? turn.validation_issues.map((i) => `[${i.level}/${i.severity}] ${i.message}`).join('\n')
                : 'No issues.')}
            {tab === 'Confidence' && (
              <div className="font-sans">
                <p className="text-slate-400 mb-2 italic">{turn.confidence.note}</p>
                <ConfidenceBar label="Intent" value={turn.confidence.intent_confidence} />
                <ConfidenceBar label="Schema" value={turn.confidence.schema_confidence} />
                <ConfidenceBar label="Join" value={turn.confidence.join_confidence} />
                <ConfidenceBar label="SQL" value={turn.confidence.sql_confidence} />
                <ConfidenceBar label="Result" value={turn.confidence.result_confidence} />
                {turn.verification_flags.length > 0 && (
                  <div className="mt-3 text-amber-600">
                    {turn.verification_flags.map((f, i) => <p key={i}>⚠ {f}</p>)}
                  </div>
                )}
                {turn.retry_log.length > 0 && (
                  <div className="mt-3 text-slate-500">
                    <p className="font-medium mb-1">Retry log:</p>
                    {turn.retry_log.map((l, i) => <p key={i}>{l}</p>)}
                  </div>
                )}
              </div>
            )}
            {tab === 'Provenance' && (
              <div className="font-sans space-y-1">
                <p><b>Question:</b> {turn.provenance.question}</p>
                <p><b>Tables/columns used:</b> derived from SQL above</p>
                <p><b>Filters applied:</b> {JSON.stringify(turn.provenance.filters_applied)}</p>
                <p><b>Reasoning:</b> {turn.provenance.reasoning_summary}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
