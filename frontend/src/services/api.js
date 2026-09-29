const BASE = '/api'

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export async function sendChat(sessionId, question) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, question }),
  })
  return handle(res)
}

export async function getSchema() {
  const res = await fetch(`${BASE}/schema`)
  return handle(res)
}

export async function getDemoQuestions() {
  const res = await fetch(`${BASE}/demo-questions`)
  return handle(res)
}

export async function resetSession(sessionId) {
  const res = await fetch(`${BASE}/session/${sessionId}/reset`, { method: 'POST' })
  return handle(res)
}

export async function runEvaluation() {
  const res = await fetch(`${BASE}/evaluation/run`)
  return handle(res)
}

export async function getDatabaseStatus() {
  const res = await fetch(`${BASE}/database/status`)
  return handle(res)
}

export async function useDemoDatabase() {
  const res = await fetch(`${BASE}/database/use-demo`, { method: 'POST' })
  return handle(res)
}

export async function getTablePreview(tableName, limit = 25) {
  const res = await fetch(`${BASE}/table/${encodeURIComponent(tableName)}/preview?limit=${limit}`)
  return handle(res)
}

export async function uploadSqliteDatabase(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/database/upload-sqlite`, { method: 'POST', body: form })
  return handle(res)
}

export const uploadDatabaseFile = uploadSqliteDatabase

export async function connectPostgres({ host, port, database, user, password }) {
  const res = await fetch(`${BASE}/database/connect-postgres`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ host, port: Number(port), database, user, password }),
  })
  return handle(res)
}
