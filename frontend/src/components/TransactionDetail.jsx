import { useState } from 'react'

export default function TransactionDetail({ txn, projects, onSave, onClose }) {
  const [code, setCode] = useState(txn.project_code || '')
  const [saving, setSaving] = useState(false)
  const [codeError, setCodeError] = useState('')

  const handleSave = async () => {
    const trimmed = code.trim().toUpperCase()
    if (!trimmed) { setCodeError('Enter a project code'); return }
    const valid = projects.find(p => p.code === trimmed)
    if (!valid) { setCodeError(`"${trimmed}" not found in project list`); return }
    setSaving(true)
    setCodeError('')
    await onSave(txn.id, trimmed)
    setSaving(false)
  }

  const merchant = txn.merchant_name || txn.description || 'Unknown Merchant'
  const isCoded = !!txn.project_code

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-lg font-bold">{merchant}</h2>
          <p className="text-gray-400 text-sm mt-1">{txn.date}</p>
        </div>
        <button onClick={onClose} className="text-gray-500 hover:text-white text-xl transition">✕</button>
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <Detail label="Amount" value={`$${parseFloat(txn.amount).toFixed(2)}`} highlight />
        <Detail label="Card" value={txn.card_last4 ? `****${txn.card_last4}` : '—'} />
        <Detail label="Employee" value={txn.employees?.name || '—'} />
        <Detail label="Coded By" value={txn.coded_by || '—'} />
        {txn.coded_at && (
          <Detail label="Coded At" value={new Date(txn.coded_at).toLocaleDateString()} />
        )}
        <Detail label="Reminders Sent" value={txn.reminder_count ?? 0} />
      </div>

      {/* Receipt */}
      {txn.receipt_url && (
        <div className="mb-6">
          <label className="text-xs text-gray-500 uppercase tracking-widest block mb-2">Receipt</label>
          <a href={txn.receipt_url} target="_blank" rel="noopener noreferrer">
            <img
              src={txn.receipt_url}
              alt="Receipt"
              className="max-h-64 rounded border border-[#333] object-contain hover:opacity-80 transition"
            />
          </a>
          <a
            href={txn.receipt_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-400 hover:underline mt-1 block"
          >
            Open full size ↗
          </a>
        </div>
      )}

      {/* Project Code Assignment */}
      <div className="bg-[#1a1a1a] rounded-lg p-4 border border-[#2a2a2a]">
        <label className="text-xs text-gray-500 uppercase tracking-widest block mb-3">
          {isCoded ? 'Change Project Code' : 'Assign Project Code'}
        </label>

        {/* Current code badge */}
        {isCoded && (
          <div className="mb-3">
            <span className="bg-green-900 text-green-300 text-sm font-bold px-3 py-1 rounded">
              Current: {txn.project_code}
            </span>
          </div>
        )}

        {/* Quick-select buttons */}
        <div className="flex flex-wrap gap-2 mb-3">
          {projects.slice(0, 12).map(p => (
            <button
              key={p.code}
              onClick={() => { setCode(p.code); setCodeError('') }}
              title={p.name}
              className={`text-xs px-2.5 py-1 rounded border transition ${
                code === p.code
                  ? 'bg-green-700 border-green-600 text-white'
                  : 'bg-[#222] border-[#333] text-gray-300 hover:border-green-700 hover:text-white'
              }`}
            >
              {p.code}
            </button>
          ))}
        </div>

        {/* Manual input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={code}
            onChange={e => { setCode(e.target.value.toUpperCase()); setCodeError('') }}
            onKeyDown={e => e.key === 'Enter' && handleSave()}
            placeholder="Type code..."
            className="flex-1 bg-[#111] border border-[#333] rounded px-3 py-2 text-sm font-mono uppercase
              focus:outline-none focus:border-green-600 placeholder-gray-600"
          />
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-green-700 hover:bg-green-600 disabled:opacity-50 px-5 py-2 rounded text-sm font-medium transition"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>

        {codeError && (
          <p className="text-red-400 text-xs mt-2">{codeError}</p>
        )}

        {/* Project name hint */}
        {code && projects.find(p => p.code === code) && (
          <p className="text-green-400 text-xs mt-2">
            ✓ {projects.find(p => p.code === code).name}
          </p>
        )}
      </div>
    </div>
  )
}

function Detail({ label, value, highlight }) {
  return (
    <div className="bg-[#1a1a1a] rounded p-3">
      <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">{label}</div>
      <div className={`font-medium ${highlight ? 'text-yellow-300 font-mono text-lg' : 'text-gray-200'}`}>
        {value}
      </div>
    </div>
  )
}
