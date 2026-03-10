export default function StatsBar({ total, coded, uncoded }) {
  return (
    <div className="flex gap-0 bg-[#161616] border-b border-[#2a2a2a]">
      <div className="flex-1 px-6 py-3 border-r border-[#2a2a2a]">
        <div className="text-xs text-gray-400 uppercase tracking-widest">Total</div>
        <div className="text-2xl font-bold text-white">{total}</div>
      </div>
      <div className="flex-1 px-6 py-3 border-r border-[#2a2a2a]">
        <div className="text-xs text-gray-400 uppercase tracking-widest">🔴 Uncoded</div>
        <div className={`text-2xl font-bold ${uncoded > 0 ? 'text-red-400' : 'text-gray-500'}`}>{uncoded}</div>
      </div>
      <div className="flex-1 px-6 py-3">
        <div className="text-xs text-gray-400 uppercase tracking-widest">🟢 Coded</div>
        <div className="text-2xl font-bold text-green-400">{coded}</div>
      </div>
    </div>
  )
}
