import { useRef, useState } from 'react'
import { useDemoDatabase, uploadSqliteDatabase, connectPostgres } from '../services/api'

const TABS = ['Demo Database', 'Upload Dataset (SQLite / CSV)', 'Connect PostgreSQL']

export default function DatabaseConnectModal({ onClose, onConnected }) {
  const [tab, setTab] = useState('Upload Dataset (SQLite / CSV)')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const fileInputRef = useRef(null)

  const [pg, setPg] = useState({ host: 'localhost', port: '5432', database: '', user: '', password: '' })

  async function handleUseDemo() {
    setBusy(true)
    setError('')
    try {
      const status = await useDemoDatabase()
      onConnected(status)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  async function processFile(file) {
    if (!file) return
    setBusy(true)
    setError('')
    try {
      const status = await uploadSqliteDatabase(file)
      onConnected(status)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (file) processFile(file)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) processFile(file)
  }

  async function handlePgSubmit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const status = await connectPostgres(pg)
      onConnected(status)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-100 bg-slate-50/70">
          <div>
            <h2 className="font-semibold text-slate-800 text-base">Connect or Upload Dataset</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Select a data source to query using natural language
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1.5 px-6 pt-3.5 bg-white border-b border-slate-100 overflow-x-auto">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => {
                setTab(t)
                setError('')
              }}
              className={`text-xs px-3.5 py-2 rounded-lg font-medium transition whitespace-nowrap cursor-pointer ${
                tab === t
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="p-6">
          {error && (
            <div className="text-xs text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-4 flex items-center gap-2">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {tab === 'Demo Database' && (
            <div className="space-y-4">
              <div className="bg-indigo-50/50 border border-indigo-100 rounded-xl p-4 text-xs text-indigo-900">
                <p className="font-semibold text-sm text-indigo-950 mb-1">Bundled E-Commerce Database</p>
                <p className="text-indigo-700 leading-relaxed">
                  Contains 3 pre-loaded tables: <code>customers</code> (200 records), <code>products</code> (23 records), and <code>orders</code> (5,680 records) with customer cities, segments, categories, revenues, and profits.
                </p>
              </div>
              <button
                onClick={handleUseDemo}
                disabled={busy}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl py-2.5 text-sm font-medium transition disabled:opacity-50 cursor-pointer shadow-xs"
              >
                {busy ? 'Switching to Demo DB…' : 'Restore Demo Database'}
              </button>
            </div>
          )}

          {tab === 'Upload Dataset (SQLite / CSV)' && (
            <div className="space-y-4">
              <div
                onDragOver={(e) => {
                  e.preventDefault()
                  setDragOver(true)
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => !busy && fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-6 text-center transition cursor-pointer flex flex-col items-center justify-center gap-2 ${
                  dragOver
                    ? 'border-indigo-500 bg-indigo-50/50'
                    : 'border-slate-200 hover:border-indigo-400 bg-slate-50/50 hover:bg-slate-50'
                } ${busy ? 'opacity-50 pointer-events-none' : ''}`}
              >
                <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center text-2xl mb-1 shadow-2xs">
                  📁
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    {busy ? 'Uploading & Indexing Schema…' : 'Click to select or drag & drop dataset'}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Supports SQLite (<code>.db</code>, <code>.sqlite</code>, <code>.sqlite3</code>) and tabular <code>.csv</code> files
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".db,.sqlite,.sqlite3,.csv"
                  onChange={handleFileChange}
                  disabled={busy}
                  className="hidden"
                />
              </div>

              {busy && (
                <div className="flex items-center justify-center gap-2 text-xs text-indigo-600 font-medium py-1 animate-pulse">
                  <span className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin"></span>
                  Processing dataset, discovering schema, and rebuilding RAG index...
                </div>
              )}

              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200/80 text-[11px] text-slate-600 space-y-1">
                <div className="font-semibold text-slate-700 flex items-center gap-1.5">
                  <span>✨</span>
                  <span>Instant Discovery & Querying</span>
                </div>
                <p className="text-slate-500">
                  Tables, column types, and relationships are automatically extracted and indexed into the RAG vector store for natural-language text-to-SQL generation.
                </p>
              </div>
            </div>
          )}

          {tab === 'Connect PostgreSQL' && (
            <form onSubmit={handlePgSubmit} className="space-y-3">
              <div className="grid grid-cols-3 gap-2">
                <div className="col-span-2">
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Host</label>
                  <input
                    className="w-full border border-slate-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-indigo-400"
                    placeholder="localhost"
                    value={pg.host}
                    onChange={(e) => setPg({ ...pg, host: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Port</label>
                  <input
                    className="w-full border border-slate-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-indigo-400"
                    placeholder="5432"
                    value={pg.port}
                    onChange={(e) => setPg({ ...pg, port: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-600 mb-1">Database Name</label>
                <input
                  className="w-full border border-slate-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-indigo-400"
                  placeholder="production_db"
                  value={pg.database}
                  onChange={(e) => setPg({ ...pg, database: e.target.value })}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Username</label>
                  <input
                    className="w-full border border-slate-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-indigo-400"
                    placeholder="postgres"
                    value={pg.user}
                    onChange={(e) => setPg({ ...pg, user: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-600 mb-1">Password</label>
                  <input
                    type="password"
                    className="w-full border border-slate-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-indigo-400"
                    placeholder="••••••••"
                    value={pg.password}
                    onChange={(e) => setPg({ ...pg, password: e.target.value })}
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={busy}
                className="w-full bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl py-2.5 text-sm font-medium transition disabled:opacity-50 cursor-pointer shadow-xs mt-2"
              >
                {busy ? 'Connecting to PostgreSQL…' : 'Connect PostgreSQL Database'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
