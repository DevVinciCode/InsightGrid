import { useEffect, useRef, useState } from 'react'
import {
  sendChat,
  getDemoQuestions,
  resetSession,
  getDatabaseStatus,
  useDemoDatabase,
} from './services/api'
import ChartView from './components/ChartView'
import ResultTable from './components/ResultTable'
import DevPanel from './components/DevPanel'
import DatabaseConnectModal from './components/DatabaseConnectModal'
import DatasetExplorer from './components/DatasetExplorer'
import DatasetHeroBanner from './components/DatasetHeroBanner'
import TablePreviewModal from './components/TablePreviewModal'

const SESSION_ID = 'demo-session-' + Math.random().toString(36).slice(2, 8)

function StatusBadge({ status }) {
  const map = {
    answered: 'bg-emerald-100 text-emerald-700',
    blocked: 'bg-red-100 text-red-700',
    error: 'bg-amber-100 text-amber-700',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${map[status] || 'bg-slate-100 text-slate-700'}`}>
      {status}
    </span>
  )
}

function MessageBubble({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-xs px-4 py-2.5 max-w-[80%] text-sm shadow-xs">
          {msg.text}
        </div>
      </div>
    )
  }

  const turn = msg.turn
  return (
    <div className="flex justify-start">
      <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-xs px-5 py-4 max-w-[95%] w-full text-sm shadow-2xs">
        <div className="flex items-center gap-2 mb-2.5">
          <StatusBadge status={turn.answer_status} />
          <span className="text-slate-500 font-medium text-xs">{turn.reasoning_summary}</span>
        </div>

        {turn.answer_status === 'blocked' && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3.5 my-2">
            <p className="text-red-700 font-medium text-xs">
              Query validation notice:
            </p>
            {turn.validation_issues?.map((i, idx) => (
              <span key={idx} className="block text-xs text-red-600 mt-1">
                • {i.message}
              </span>
            ))}
          </div>
        )}
        {turn.answer_status === 'error' && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 my-2 text-amber-800 text-xs">
            The query failed to execute against the database. Check the developer panel below for the database error message and retry log.
          </div>
        )}

        {turn.answer_status === 'answered' && (
          <>
            {/* Single value KPI metric if only 1 row */}
            {turn.rows?.length === 1 && turn.columns?.length <= 2 && (
              <div className="my-3 bg-gradient-to-r from-indigo-50/80 via-white to-slate-50 border border-indigo-100 rounded-2xl p-4 flex items-center gap-4 shadow-2xs">
                <div className="w-12 h-12 rounded-xl bg-indigo-600 text-white flex items-center justify-center text-xl font-bold shadow-xs">
                  📈
                </div>
                <div>
                  <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                    {turn.columns[turn.columns.length - 1]?.replace(/_/g, ' ')}
                  </span>
                  <div className="text-2xl font-bold font-mono text-slate-900 mt-0.5">
                    {typeof turn.rows[0][turn.columns.length - 1] === 'number'
                      ? turn.rows[0][turn.columns.length - 1].toLocaleString()
                      : String(turn.rows[0][turn.columns.length - 1] ?? '—')}
                  </div>
                  {turn.columns.length === 2 && (
                    <span className="text-xs text-slate-500 font-medium">
                      for {String(turn.rows[0][0])}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Visual Analytics ChartView if 2+ rows */}
            {turn.rows?.length > 1 && (
              <div className="my-2">
                <ChartView columns={turn.columns} rows={turn.rows} spec={turn.visualization || {}} />
              </div>
            )}

            <div className="mt-3">
              <ResultTable columns={turn.columns} rows={turn.rows} truncated={turn.truncated} />
            </div>
            {turn.visualization?.structure_mismatch && (
              <p className="text-xs text-amber-600 mt-2 bg-amber-50 px-2.5 py-1.5 rounded-lg border border-amber-200/60">
                ℹ️ {turn.visualization.structure_mismatch}
              </p>
            )}
          </>
        )}

        <DevPanel turn={turn} />
      </div>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [demoQuestions, setDemoQuestions] = useState({ questions: [], ambiguous_examples: [] })
  const [dbStatus, setDbStatus] = useState(null)
  const [dbModalOpen, setDbModalOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [previewTable, setPreviewTable] = useState(null)
  const [toast, setToast] = useState(null)
  const bottomRef = useRef(null)

  function refreshDbAndQuestions() {
    getDatabaseStatus()
      .then((status) => setDbStatus(status))
      .catch(() => {})
    getDemoQuestions()
      .then((q) => setDemoQuestions(q))
      .catch(() => {})
  }

  useEffect(() => {
    refreshDbAndQuestions()
  }, [])

  function showToast(msg) {
    setToast(msg)
    setTimeout(() => setToast(null), 6000)
  }

  function handleDatabaseConnected(status) {
    setDbStatus(status)
    setDbModalOpen(false)
    setMessages([])
    resetSession(SESSION_ID)
    getDemoQuestions().then(setDemoQuestions).catch(() => {})
    showToast(`Connected to ${status.label} (${status.tables?.length || 0} tables indexed)`)
  }

  async function handleUseDemo() {
    try {
      const status = await useDemoDatabase()
      handleDatabaseConnected(status)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function ask(question) {
    if (!question.trim() || loading) return
    setMessages((m) => [...m, { role: 'user', text: question }])
    setInput('')
    setLoading(true)
    try {
      const turn = await sendChat(SESSION_ID, question)
      setMessages((m) => [...m, { role: 'agent', turn }])
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          role: 'agent',
          turn: {
            answer_status: 'error',
            reasoning_summary: e.message,
            columns: [],
            rows: [],
            visualization: { chart_type: 'table' },
            validation_issues: [],
            verification_flags: [],
            confidence: {
              note: '',
              intent_confidence: 0,
              schema_confidence: 0,
              join_confidence: 0,
              sql_confidence: 0,
              result_confidence: 0,
            },
            provenance: {
              question,
              retrieved_documents: [],
              filters_applied: [],
              reasoning_summary: '',
            },
            sql: '',
            retry_log: [],
            truncated: false,
            intent: {},
          },
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-screen flex flex-col bg-slate-100 text-slate-800">
      {/* Top Navbar */}
      <header className="border-b border-slate-200 bg-white px-5 py-2.5 flex justify-between items-center z-10 shrink-0 shadow-2xs">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-500 hover:text-slate-800 transition cursor-pointer"
            title={sidebarOpen ? 'Hide dataset sidebar' : 'Show dataset sidebar'}
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d={sidebarOpen ? 'M4 6h16M4 12h10M4 18h16' : 'M4 6h16M4 12h16M4 18h16'}
              />
            </svg>
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-slate-900 text-sm tracking-tight">InsightGrid</h1>
              <span className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.2 rounded font-mono">
                v0.2.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Conversational Text-to-SQL + RAG | Developed by Dev Dogra</p>
          </div>
        </div>

        {/* Database Status & Action Buttons */}
        <div className="flex items-center gap-2.5">
          {dbStatus && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="flex items-center gap-2 text-xs bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-full px-3 py-1 text-slate-700 transition cursor-pointer"
              title="Click to view schema in sidebar"
            >
              <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
              <span className="font-mono text-[11px] max-w-[160px] truncate">{dbStatus.label}</span>
              <span className="text-[10px] text-slate-400">
                ({dbStatus.tables?.length || 0} tables)
              </span>
            </button>
          )}

          <button
            className="text-xs bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-full px-3.5 py-1 transition cursor-pointer shadow-xs"
            onClick={() => setDbModalOpen(true)}
          >
            + Connect DB / Dataset
          </button>

          <button
            className="text-xs text-slate-500 hover:text-slate-800 px-2 py-1 rounded-md hover:bg-slate-100 transition cursor-pointer"
            onClick={() => {
              resetSession(SESSION_ID)
              setMessages([])
            }}
            title="Clear message history and conversation context"
          >
            Reset
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Dataset Explorer Sidebar */}
        {sidebarOpen && (
          <DatasetExplorer
            dbStatus={dbStatus}
            onOpenConnectModal={() => setDbModalOpen(true)}
            onUseDemo={handleUseDemo}
            onPreviewTable={(tName) => setPreviewTable(tName)}
            onAskQuestion={ask}
          />
        )}

        {/* Chat / Query Panel */}
        <main className="flex-1 flex flex-col overflow-hidden bg-slate-50/60 relative">
          {/* Toast Notification */}
          {toast && (
            <div className="absolute top-3 right-6 z-20 bg-slate-900 text-white px-4 py-2.5 rounded-xl shadow-lg text-xs flex items-center gap-2 animate-in fade-in slide-in-from-top-2 duration-200">
              <span>🎉</span>
              <span>{toast}</span>
              <button
                onClick={() => setToast(null)}
                className="text-slate-400 hover:text-white ml-2 cursor-pointer"
              >
                ✕
              </button>
            </div>
          )}

          {/* Conversation Feed */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            {messages.length === 0 && (
              <DatasetHeroBanner
                dbStatus={dbStatus}
                demoQuestions={demoQuestions}
                onAskQuestion={ask}
                onPreviewTable={(tName) => setPreviewTable(tName)}
                onOpenConnectModal={() => setDbModalOpen(true)}
              />
            )}

            {messages.map((m, i) => (
              <MessageBubble key={i} msg={m} />
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-xs text-slate-400 px-3 py-2 bg-white/60 border border-slate-200/50 rounded-xl w-fit animate-pulse">
                <span className="w-3.5 h-3.5 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></span>
                <span>Synthesizing SQL and executing query against {dbStatus?.label || 'database'}…</span>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Bottom Chat Input Form */}
          <div className="border-t border-slate-200 bg-white p-3.5 shrink-0 shadow-xs">
            <form
              className="max-w-4xl mx-auto flex gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                ask(input)
              }}
            >
              <input
                className="flex-1 border border-slate-200 rounded-full px-5 py-2.5 text-sm focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 bg-slate-50/50"
                placeholder={`Ask any analytical question about ${dbStatus?.label || 'your database'}...`}
                value={input}
                onChange={(e) => setInput(e.target.value)}
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-full px-6 py-2.5 text-sm transition disabled:opacity-50 cursor-pointer shadow-xs"
              >
                Ask
              </button>
            </form>
          </div>
        </main>
      </div>

      {/* Connect Database Modal */}
      {dbModalOpen && (
        <DatabaseConnectModal
          onClose={() => setDbModalOpen(false)}
          onConnected={handleDatabaseConnected}
        />
      )}

      {/* Table Data Preview Modal */}
      {previewTable && (
        <TablePreviewModal
          tableName={previewTable}
          onClose={() => setPreviewTable(null)}
          onAskAboutTable={ask}
        />
      )}
    </div>
  )
}
