export default function TransactionList({ transactions, onSelect, selectedId }) {
  return (
    <table className="w-full text-sm">
      <thead className="sticky top-0 bg-[#181818] border-b border-[#2a2a2a] z-10">
        <tr className="text-left text-xs text-gray-500 uppercase tracking-wider">
          <th className="px-6 py-3">Date</th>
          <th className="px-6 py-3">Merchant</th>
          <th className="px-6 py-3">Amount</th>
          <th className="px-6 py-3">Card</th>
          <th className="px-6 py-3">Employee</th>
          <th className="px-6 py-3">Code</th>
          <th className="px-6 py-3">Receipt</th>
        </tr>
      </thead>
      <tbody>
        {transactions.map(txn => {
          const isCoded = !!txn.project_code
          const isSelected = txn.id === selectedId
          return (
            <tr
              key={txn.id}
              onClick={() => onSelect(txn)}
              className={`border-b border-[#1e1e1e] cursor-pointer transition-colors
                ${isSelected ? 'bg-[#1e2a1e]' : 'hover:bg-[#1a1a1a]'}
              `}
            >
              <td className="px-6 py-3 text-gray-400 whitespace-nowrap">{txn.date}</td>
              <td className="px-6 py-3 font-medium max-w-[200px] truncate">
                {txn.merchant_name || txn.description || '—'}
              </td>
              <td className="px-6 py-3 text-yellow-300 font-mono">
                ${parseFloat(txn.amount).toFixed(2)}
              </td>
              <td className="px-6 py-3 text-gray-500 font-mono text-xs">
                {txn.card_last4 ? `****${txn.card_last4}` : '—'}
              </td>
              <td className="px-6 py-3 text-gray-400">
                {txn.employees?.name || '—'}
              </td>
              <td className="px-6 py-3">
                {isCoded ? (
                  <span className="bg-green-900 text-green-300 text-xs font-bold px-2 py-0.5 rounded">
                    {txn.project_code}
                  </span>
                ) : (
                  <span className="bg-red-900 text-red-300 text-xs px-2 py-0.5 rounded">
                    Uncoded
                  </span>
                )}
              </td>
              <td className="px-6 py-3 text-center">
                {txn.receipt_url ? '📷' : <span className="text-gray-700">—</span>}
              </td>
            </tr>
          )
        })}
      </tbody>
    </table>
  )
}
