import { useState, useEffect, useCallback } from 'react'
import TransactionList from './components/TransactionList'
import TransactionDetail from './components/TransactionDetail'
import StatsBar from './components/StatsBar'
import Filters from './components/Filters'
import { api } from './lib/api'

export default function App() {
  const [transactions, setTransactions] = useState([])
  const [projects, setProjects] = useState([])
  const [employees, setEmployees] = useState([])
  const [selectedTxn, setSelectedTxn] = useState(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [filters, setFilters] = useState({
    uncoded_only: false,
    coded_only: false,
    employee_id: '',
    date_from: '',
    date_to: ''
  })
  const [toast, setToast] = useState(null)

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }

  const loadTransactions = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.getTransactions(filters)
      setTransactions(data.transactions)
    } catch (e) {
      showToast('Failed to load transactions', 'error')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    loadTransactions()
    api.getProjects().then(d => setProjects(d.projects)).catch(() => {})
    api.getEmployees().then(d => setEmployees(d.employees)).catch(() => {})
  }, [loadTransactions])

  const handleCodeSave = async (txnId, code) => {
    try {
      await api.updateCode(txnId, code)
      showToast(`Coded as ${code} ✓`)
      setSelectedTxn(null)
      loadTransactions()
    } catch (e) {
      showToast('Failed to save code', 'error')
    }
  }

  const handleSync = async () => {
    setSyncing(true)
    try {
      const res = await api.manualSync()
      showToast(`Sync done — ${res.reminders_sent} reminder(s) sent`)
      loadTransactions()
    } catch (e) {
      showToast('Sync failed', 'error')
    } finally {
      setSyncing(false)
    }
  }

  const coded = transactions.filter(t => t.project_code)
  const uncoded = transactions.filter(t => !t.project_code)

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-white">
      {/* Header */}
      <header className="bg-[#1a1a1a] border-b border-[#2a2a2a] px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-wide">💳 Masterson Transaction Tracker</h1>
          <p className="text-xs text-gray-400 mt-0.5">Capital One Spark — Project Code Management</p>
        </div>
        <div className="flex gap-3 items-center">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="bg-[#2a2a2a] hover:bg-[#333] border border-[#444] text-sm px-4 py-2 rounded transition disabled:opacity-50"
          >
            {syncing ? '⏳ Syncing...' : '🔄 Sync Now'}
          </button>
          <button
            onClick={() => api.exportCSV(filters.date_from, filters.date_to)}
            className="bg-green-700 hover:bg-green-600 text-sm px-4 py-2 rounded transition"
          >
            ⬇ Export CSV
          </button>
        </div>
      </header>

      {/* Stats */}
      <StatsBar total={transactions.length} coded={coded.length} uncoded={uncoded.length} />

      {/* Filters */}
      <Filters
        filters={filters}
        setFilters={setFilters}
        employees={employees}
      />

      {/* Main content */}
      <div className="flex h-[calc(100vh-220px)]">
        {/* Transaction list */}
        <div className={`overflow-y-auto ${selectedTxn ? 'w-1/2' : 'w-full'}`}>
          {loading ? (
            <div className="flex items-center justify-center h-48 text-gray-500">Loading...</div>
          ) : transactions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-gray-500 gap-2">
              <span className="text-4xl">✅</span>
              <span>No transactions match your filters</span>
            </div>
          ) : (
            <TransactionList
              transactions={transactions}
              onSelect={setSelectedTxn}
              selectedId={selectedTxn?.id}
            />
          )}
        </div>

        {/* Detail panel */}
        {selectedTxn && (
          <div className="w-1/2 border-l border-[#2a2a2a] overflow-y-auto">
            <TransactionDetail
              txn={selectedTxn}
              projects={projects}
              onSave={handleCodeSave}
              onClose={() => setSelectedTxn(null)}
            />
          </div>
        )}
      </div>

      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 px-5 py-3 rounded shadow-lg text-sm font-medium transition-all
          ${toast.type === 'error' ? 'bg-red-700' : 'bg-green-700'}`}>
          {toast.msg}
        </div>
      )}
    </div>
  )
}
