export default function Filters({ filters, setFilters, employees }) {
  const set = (key, val) => setFilters(f => ({ ...f, [key]: val }))

  return (
    <div className="flex flex-wrap gap-3 px-6 py-3 bg-[#141414] border-b border-[#2a2a2a] items-center">
      {/* Status filter */}
      <div className="flex gap-1 bg-[#1a1a1a] rounded p-1">
        {[
          { label: 'All', uncoded: false, coded: false },
          { label: '🔴 Uncoded', uncoded: true, coded: false },
          { label: '🟢 Coded', uncoded: false, coded: true },
        ].map(opt => (
          <button
            key={opt.label}
            onClick={() => setFilters(f => ({ ...f, uncoded_only: opt.uncoded, coded_only: opt.coded }))}
            className={`px-3 py-1 rounded text-sm transition ${
              filters.uncoded_only === opt.uncoded && filters.coded_only === opt.coded
                ? 'bg-[#333] text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Employee filter */}
      {employees.length > 0 && (
        <select
          value={filters.employee_id}
          onChange={e => set('employee_id', e.target.value)}
          className="bg-[#1a1a1a] border border-[#333] text-sm rounded px-3 py-1.5 text-gray-300"
        >
          <option value="">All Employees</option>
          {employees.map(emp => (
            <option key={emp.id} value={emp.id}>{emp.name} (****{emp.card_last4})</option>
          ))}
        </select>
      )}

      {/* Date range */}
      <input
        type="date"
        value={filters.date_from}
        onChange={e => set('date_from', e.target.value)}
        className="bg-[#1a1a1a] border border-[#333] text-sm rounded px-3 py-1.5 text-gray-300"
        placeholder="From"
      />
      <span className="text-gray-500 text-sm">→</span>
      <input
        type="date"
        value={filters.date_to}
        onChange={e => set('date_to', e.target.value)}
        className="bg-[#1a1a1a] border border-[#333] text-sm rounded px-3 py-1.5 text-gray-300"
        placeholder="To"
      />

      {/* Clear */}
      <button
        onClick={() => setFilters({ uncoded_only: false, coded_only: false, employee_id: '', date_from: '', date_to: '' })}
        className="text-xs text-gray-500 hover:text-gray-300 transition ml-auto"
      >
        Clear filters
      </button>
    </div>
  )
}
