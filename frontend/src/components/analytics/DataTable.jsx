import { useState } from 'react';

/* ════════════════════════ DataTable ════════════════════════ */
export default function DataTable({ data, onSelect }) {
  const [q, setQ] = useState('');
  if (!data?.length) return null;

  const rows = data.filter((r) => {
    if (!q) return true;
    const s = q.toLowerCase();
    return [r.block_id, r.section, r.corridor, r.departments, r.day_of_week].some(
      (f) => f?.toLowerCase().includes(s)
    );
  });

  const fmtH = (h) => {
    const hh = Math.floor(h),
      mm = Math.round((h - hh) * 60);
    return `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4">
      <input
        type="text"
        placeholder="Filter blocks..."
        value={q}
        onChange={(e) => setQ(e.target.value)}
        className="bg-[#111] border border-[#333] rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-600 w-full max-w-sm focus:outline-none focus:border-emerald-500/60 transition-colors"
      />
      <div className="overflow-x-auto rounded-xl border border-[#222]">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-[#0f0f0f] text-xs text-slate-500 uppercase tracking-wider font-semibold border-b border-[#222]">
              <th className="px-5 py-4">Block</th>
              <th className="px-5 py-4">Section</th>
              <th className="px-5 py-4">Day & Time</th>
              <th className="px-5 py-4">Hrs</th>
              <th className="px-5 py-4">Departments</th>
              <th className="px-5 py-4 text-right">Tasks</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {rows.map((r, i) => (
              <tr
                key={i}
                onClick={() => onSelect(r)}
                className="border-b border-[#1a1a1a] hover:bg-[#111] cursor-pointer transition-colors text-slate-300"
              >
                <td className="px-5 py-4 font-mono text-xs text-emerald-500">{r.block_id}</td>
                <td className="px-5 py-4">{r.section}</td>
                <td className="px-5 py-4">
                  {r.day_of_week}{' '}
                  <span className="text-slate-600 ml-2">
                    {fmtH(r.block_start_hour)}-{fmtH(r.block_end_hour)}
                  </span>
                </td>
                <td className="px-5 py-4 font-medium">{r.total_hours?.toFixed(1)}</td>
                <td className="px-5 py-4 text-xs text-slate-400">{r.departments}</td>
                <td className="px-5 py-4 text-right font-semibold">{r.task_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
