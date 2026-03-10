// All API calls to the FastAPI backend
const BASE = import.meta.env.VITE_API_URL || '/api'

async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  // Transactions
  getTransactions: (params = {}) => {
    const q = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([_, v]) => v != null && v !== ''))
    ).toString()
    return apiFetch(`/transactions${q ? '?' + q : ''}`)
  },

  updateCode: (txnId, code) =>
    apiFetch(`/transactions/${txnId}/code`, {
      method: 'PATCH',
      body: JSON.stringify({ code })
    }),

  // Projects
  getProjects: () => apiFetch('/projects'),

  // Employees
  getEmployees: () => apiFetch('/employees'),

  // Export
  exportCSV: (dateFrom, dateTo) => {
    const params = new URLSearchParams()
    if (dateFrom) params.set('date_from', dateFrom)
    if (dateTo) params.set('date_to', dateTo)
    window.location.href = `${BASE}/export/csv?${params}`
  },

  // Admin
  manualSync: () => apiFetch('/admin/sync', { method: 'POST' }),
  syncAccounts: () => apiFetch('/admin/sync-accounts', { method: 'POST' }),
}
