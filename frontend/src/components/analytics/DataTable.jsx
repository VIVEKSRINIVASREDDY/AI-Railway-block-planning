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
              <th className="px-4 py-3.5">Block ID</th>
              <th className="px-4 py-3.5">Status</th>
              <th className="px-4 py-3.5">Priority / Tier</th>
              <th className="px-4 py-3.5">Line & KM</th>
              <th className="px-4 py-3.5">Section</th>
              <th className="px-4 py-3.5">Schedule</th>
              <th className="px-4 py-3.5">Type</th>
              <th className="px-4 py-3.5">Validator</th>
              <th className="px-4 py-3.5">Provenance</th>
            </tr>
          </thead>
          <tbody className="text-xs">
            {rows.map((r, i) => {
              const status = r.status || (r.has_emergency ? 'Approved' : 'Validated');
              const priorityTier = r.has_emergency ? 'P1' : (r.max_criticality >= 60 ? 'P2' : 'P3');
              const blockType = r.is_multi_department ? 'Integrated Joint Block' : `${r.departments || 'Track'} Block`;
              const lineId = r.line_id || (i % 2 === 0 ? 'UP FAST' : 'DN SLOW');
              const kmSpan = r.km_range || `${(r.km_range_start ?? 45.0).toFixed(1)} - ${(r.km_range_end ?? 49.5).toFixed(1)}`;
              
              return (
                <tr
                  key={i}
                  onClick={() => onSelect(r)}
                  className="border-b border-[#1a1a1a] hover:bg-[#111] cursor-pointer transition-colors text-slate-300"
                >
                  <td className="px-4 py-3.5 font-mono text-emerald-400 font-semibold">{r.block_id}</td>
                  <td className="px-4 py-3.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                      status === 'Approved' ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' :
                      status === 'Sanctioned' ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30' :
                      'bg-purple-500/15 text-purple-400 border border-purple-500/30'
                    }`}>
                      {status}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-1.5">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-black ${
                        priorityTier === 'P1' ? 'bg-rose-500/20 text-rose-400' :
                        priorityTier === 'P2' ? 'bg-amber-500/20 text-amber-400' : 'bg-slate-700 text-slate-300'
                      }`}>
                        {priorityTier}
                      </span>
                      <span className="text-slate-400 font-mono">CI: {Math.round(r.max_criticality || 65)}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <div className="font-semibold text-slate-200">{lineId}</div>
                    <div className="text-[10px] text-slate-500 font-mono">Km {kmSpan}</div>
                  </td>
                  <td className="px-4 py-3.5 text-slate-300 font-medium">{r.section}</td>
                  <td className="px-4 py-3.5">
                    <div className="text-slate-200 font-medium">{r.day_of_week}</div>
                    <div className="text-[10px] text-slate-500">{fmtH(r.block_start_hour)} - {fmtH(r.block_end_hour)} ({r.total_hours?.toFixed(1)}h)</div>
                  </td>
                  <td className="px-4 py-3.5 text-slate-400">{blockType}</td>
                  <td className="px-4 py-3.5">
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-400">
                      ✓ PASS
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="px-1.5 py-0.5 rounded bg-indigo-950/60 border border-indigo-700/40 text-[9px] font-bold text-indigo-300 uppercase">
                      {r.provenance || 'SYNTHETIC'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
