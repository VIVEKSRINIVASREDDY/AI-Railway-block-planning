import { X, Clock, MapPin, AlertTriangle, CheckCircle, Layers, List } from 'lucide-react';

export default function BlockModal({ block, tasks = [], onClose }) {
  if (!block) return null;

  const blockTasks = tasks.filter(t =>
    t.block_id === block.block_id ||
    (block.task_ids && block.task_ids.split(',').map(s => s.trim()).includes(t.task_id))
  );

  const winDur = (block.window_end_hour - block.window_start_hour) || block.total_hours;
  const util = Math.min(100, Math.round((block.total_hours / winDur) * 100));

  const fmtH = h => {
    const hh = Math.floor(h), mm = Math.round((h - hh) * 60);
    return `${String(hh).padStart(2,'0')}:${String(mm).padStart(2,'0')}`;
  };

  const ci = block.max_criticality || block.avg_criticality || 0;
  const tier = ci >= 75 ? { l: 'Critical', c: 'text-red-400 bg-red-500/15 border-red-500/20' }
    : ci >= 50 ? { l: 'High', c: 'text-amber-400 bg-amber-500/15 border-amber-500/20' }
    : ci >= 25 ? { l: 'Medium', c: 'text-sky-400 bg-sky-500/15 border-sky-500/20' }
    : { l: 'Low', c: 'text-emerald-400 bg-emerald-500/15 border-emerald-500/20' };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-[#0f1629] border border-white/10 rounded-2xl shadow-2xl overflow-hidden max-h-[85vh] flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/8 flex items-center justify-between bg-gradient-to-r from-[#0f1629] to-indigo-950/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-600/20 border border-indigo-500/25 flex items-center justify-center text-indigo-400 text-sm font-black">
              {block.block_id.replace('BLK-','#')}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white">{block.block_id}</h3>
                <span className={`px-2 py-0.5 text-[11px] font-semibold rounded-md border ${tier.c}`}>{tier.l}</span>
                {block.is_multi_department && (
                  <span className="px-2 py-0.5 text-[11px] font-semibold rounded-md border bg-amber-500/15 text-amber-300 border-amber-500/20 flex items-center gap-0.5">
                    <Layers className="w-3 h-3" />Joint
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-400 flex items-center gap-1 mt-0.5">
                <MapPin className="w-3 h-3 text-indigo-400" />
                {block.corridor} &bull; <span className="text-slate-200 font-medium">{block.section}</span>
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/8 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 overflow-y-auto space-y-4">
          {/* Metric cards */}
          <div className="grid grid-cols-4 gap-3">
            <Stat icon={<Clock className="w-3.5 h-3.5 text-sky-400" />} label="Schedule" value={block.day_of_week} sub={`${fmtH(block.block_start_hour)} - ${fmtH(block.block_end_hour)}`} />
            <Stat icon={<Clock className="w-3.5 h-3.5 text-emerald-400" />} label="Duration" value={`${block.total_hours.toFixed(1)}h`} sub={`Window: ${winDur.toFixed(1)}h`} />
            <Stat icon={<CheckCircle className="w-3.5 h-3.5 text-violet-400" />} label="Utilization" value={`${util}%`} bar={util} />
            <Stat icon={<AlertTriangle className="w-3.5 h-3.5 text-amber-400" />} label="Criticality" value={ci.toFixed(1)} sub="out of 100" />
          </div>

          {/* Location info */}
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div className="bg-white/[0.03] rounded-lg px-3 py-2">
              <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-0.5">Chainage</div>
              <div className="text-slate-200 font-medium text-sm">
                KM {block.km_range_start?.toFixed(1) ?? '0.0'} → {block.km_range_end?.toFixed(1) ?? '0.0'}
              </div>
            </div>
            <div className="bg-white/[0.03] rounded-lg px-3 py-2">
              <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-0.5">COA Window</div>
              <div className="text-indigo-300 font-mono text-sm">{block.window_id || '—'}</div>
            </div>
            <div className="bg-white/[0.03] rounded-lg px-3 py-2">
              <div className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-0.5">Departments</div>
              <div className="flex gap-1 mt-0.5">
                {block.departments.split(',').map((d, i) => {
                  const t = d.trim();
                  const c = t === 'Engineering' ? 'bg-blue-500/15 text-blue-300'
                    : t === 'S&T' ? 'bg-emerald-500/15 text-emerald-300'
                    : 'bg-violet-500/15 text-violet-300';
                  return <span key={i} className={`px-1.5 py-0.5 rounded text-[11px] font-medium ${c}`}>{t}</span>;
                })}
              </div>
            </div>
          </div>

          {/* Tasks table */}
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <List className="w-3.5 h-3.5 text-indigo-400" />
              Defect Tasks ({blockTasks.length || block.task_count || '?'})
            </h4>

            {blockTasks.length > 0 ? (
              <div className="rounded-lg border border-white/6 overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-white/[0.03] text-[10px] text-slate-500 uppercase tracking-wider font-semibold border-b border-white/6">
                      <th className="px-3 py-2">Task</th>
                      <th className="px-3 py-2">Dept</th>
                      <th className="px-3 py-2">Defect</th>
                      <th className="px-3 py-2 text-center">Sev</th>
                      <th className="px-3 py-2 text-center">Overdue</th>
                      <th className="px-3 py-2 text-right">Hours</th>
                    </tr>
                  </thead>
                  <tbody>
                    {blockTasks.map((t, i) => (
                      <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.015]">
                        <td className="px-3 py-2 font-mono font-medium text-indigo-300">{t.task_id}</td>
                        <td className="px-3 py-2">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                            t.department === 'Engineering' ? 'bg-blue-500/15 text-blue-300' :
                            t.department === 'S&T' ? 'bg-emerald-500/15 text-emerald-300' :
                            'bg-violet-500/15 text-violet-300'
                          }`}>{t.department}</span>
                        </td>
                        <td className="px-3 py-2 text-slate-200">{t.defect_type || 'Preventive'}</td>
                        <td className="px-3 py-2 text-center">
                          <span className={`font-bold ${t.severity >= 4 ? 'text-red-400' : t.severity === 3 ? 'text-amber-400' : 'text-slate-400'}`}>
                            {t.severity}/5
                          </span>
                        </td>
                        <td className="px-3 py-2 text-center text-slate-300">
                          {t.days_overdue > 0 ? `${t.days_overdue}d` : '—'}
                        </td>
                        <td className="px-3 py-2 text-right text-slate-200 font-medium">{t.required_hours?.toFixed(1) ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5 text-xs text-slate-500 text-center">
                Task IDs: <span className="text-slate-300 font-mono">{block.task_ids || 'N/A'}</span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-white/8 flex justify-end">
          <button onClick={onClose} className="px-4 py-1.5 bg-white/8 hover:bg-white/12 text-white rounded-lg text-sm font-medium transition-colors">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function Stat({ icon, label, value, sub, bar }) {
  return (
    <div className="bg-white/[0.03] border border-white/5 rounded-lg p-3">
      <div className="text-[10px] text-slate-500 font-medium flex items-center gap-1 mb-1">{icon}{label}</div>
      <div className="text-sm font-bold text-white">{value}</div>
      {bar != null && (
        <div className="w-full h-1 bg-white/5 rounded-full mt-1.5 overflow-hidden">
          <div className="h-full rounded-full bg-violet-500" style={{ width: `${bar}%` }} />
        </div>
      )}
      {sub && <div className="text-[11px] text-slate-500 mt-0.5">{sub}</div>}
    </div>
  );
}
