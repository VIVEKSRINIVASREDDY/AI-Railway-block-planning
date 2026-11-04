import { useState, useMemo } from 'react';
import Plot from 'react-plotly.js';
import {
  Calendar, Clock, Filter, Search, Maximize2, Minimize2,
  Info, AlertTriangle, BarChart3
} from 'lucide-react';
import BlockModal from './BlockModal';

const CORRIDORS = ['Central Railway (CSMT-Kalyan-Igatpuri) [FLAGSHIP]', 'All Corridors', 'Delhi-Kanpur (SYNTHETIC)', 'Chennai-Vijayawada (SYNTHETIC)', 'Howrah-Dhanbad (SYNTHETIC)'];
const DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun','All'];
const DAY_FULL = { All:'All', Mon:'Monday', Tue:'Tuesday', Wed:'Wednesday', Thu:'Thursday', Fri:'Friday', Sat:'Saturday', Sun:'Sunday' };

const DEPT_COLORS = {
  Engineering: { bg: 'from-blue-600 to-blue-500', border: 'border-blue-400/40', dot: 'bg-blue-500' },
  'S&T':       { bg: 'from-emerald-600 to-emerald-500', border: 'border-emerald-400/40', dot: 'bg-emerald-500' },
  Electrical:  { bg: 'from-violet-600 to-violet-500', border: 'border-violet-400/40', dot: 'bg-violet-500' },
  Joint:       { bg: 'from-amber-500 to-orange-500', border: 'border-amber-400/40', dot: 'bg-amber-500' },
};

export default function RailwayGantt({ schedule = [], tasks = [] }) {
  const [corridor, setCorridor] = useState('Central Railway (CSMT-Kalyan-Igatpuri) [FLAGSHIP]');
  const [day, setDay] = useState('Mon');
  const [dept, setDept] = useState('all');
  const [search, setSearch] = useState('');
  const [view, setView] = useState('timeline');
  const [expanded, setExpanded] = useState(false);
  const [selectedBlock, setSelectedBlock] = useState(null);

  const dayFull = DAY_FULL[day] || day;

  const filtered = useMemo(() => {
    return schedule.filter(b => {
      if (corridor.startsWith('Central Railway') && b.corridor !== 'Mumbai-Pune') return false;
      if (corridor.includes('Delhi-Kanpur') && b.corridor !== 'Delhi-Kanpur') return false;
      if (corridor.includes('Chennai-Vijayawada') && b.corridor !== 'Chennai-Vijayawada') return false;
      if (corridor.includes('Howrah-Dhanbad') && b.corridor !== 'Howrah-Dhanbad') return false;
      if (day !== 'All' && b.day_of_week !== dayFull) return false;
      if (dept === 'joint' && !b.is_multi_department) return false;
      if (dept !== 'all' && dept !== 'joint' && !b.departments.includes(dept)) return false;
      if (search.trim()) {
        const q = search.toLowerCase();
        if (![b.block_id, b.section, b.corridor, b.task_ids].some(f => f?.toLowerCase().includes(q))) return false;
      }
      return true;
    });
  }, [schedule, corridor, day, dayFull, dept, search]);

  const sections = useMemo(() => {
    const map = {};
    filtered.forEach(b => {
      const k = `${b.corridor}|${b.section}`;
      if (!map[k]) map[k] = { corridor: b.corridor, section: b.section, blocks: [] };
      map[k].blocks.push(b);
    });
    return Object.values(map).sort((a, b) => a.corridor.localeCompare(b.corridor) || a.section.localeCompare(b.section));
  }, [filtered]);

  const dayCounts = useMemo(() => {
    const c = {};
    DAYS.forEach(d => { c[d] = d === 'All' ? schedule.length : schedule.filter(b => b.day_of_week === DAY_FULL[d]).length; });
    return c;
  }, [schedule]);

  const stats = useMemo(() => {
    const n = filtered.length;
    const hrs = filtered.reduce((a, b) => a + (b.total_hours || 0), 0);
    const joint = filtered.filter(b => b.is_multi_department).length;
    return { n, hrs: hrs.toFixed(1), joint };
  }, [filtered]);

  const fmtH = h => {
    const hh = Math.floor(h), mm = Math.round((h - hh) * 60);
    return `${String(hh).padStart(2,'0')}:${String(mm).padStart(2,'0')}`;
  };

  const blockStyle = (b) => {
    if (b.is_multi_department) return DEPT_COLORS.Joint;
    const p = b.departments.split(',')[0].trim();
    return DEPT_COLORS[p] || DEPT_COLORS.Engineering;
  };

  const hasFilters = corridor !== 'All Corridors' || day !== 'All' || dept !== 'all' || search;
  const resetAll = () => { setCorridor('All Corridors'); setDay('All'); setDept('all'); setSearch(''); };

  return (
    <div className={`space-y-3 ${expanded ? 'fixed inset-0 z-40 bg-[#0a0e1a] p-3 sm:p-6 overflow-y-auto' : ''}`}>

      {/* ── Filters ── */}
      <div className="rounded-xl border border-white/8 bg-slate-900/50 p-3 sm:p-4 space-y-2.5">

        {/* Row 1: Corridor + Search + View */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
            <div className="flex items-center gap-1.5 bg-slate-800/60 border border-white/8 rounded-lg px-2.5 py-1.5">
              <Filter className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <select
                value={corridor}
                onChange={e => setCorridor(e.target.value)}
                className="bg-transparent text-xs sm:text-sm text-white focus:outline-none cursor-pointer flex-1 min-w-0"
              >
                {CORRIDORS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="w-full sm:w-44 bg-slate-800/60 border border-white/8 rounded-lg pl-8 pr-3 py-1.5 text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/40"
              />
            </div>
          </div>

          <div className="flex items-center justify-between sm:justify-end gap-2">
            <div className="inline-flex bg-slate-800/60 border border-white/8 rounded-lg p-0.5">
              {[
                { id: 'timeline', label: '24h', icon: <Clock className="w-3.5 h-3.5" /> },
                { id: 'weekly', label: 'Week', icon: <Calendar className="w-3.5 h-3.5" /> },
                { id: 'plotly', label: 'Chart', icon: <BarChart3 className="w-3.5 h-3.5" /> },
              ].map(v => (
                <button
                  key={v.id}
                  onClick={() => setView(v.id)}
                  className={`flex items-center gap-1 px-2 py-1 sm:px-2.5 rounded-md text-[11px] sm:text-xs font-medium transition-all ${
                    view === v.id ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {v.icon}<span className="hidden sm:inline">{v.label}</span>
                </button>
              ))}
            </div>
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1.5 bg-slate-800/60 border border-white/8 rounded-lg text-slate-400 hover:text-white transition-colors"
            >
              {expanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* Row 2: Day + Dept pills — scrollable on mobile */}
        <div className="flex items-center gap-1 overflow-x-auto pb-0.5 -mx-1 px-1">
          {DAYS.map(d => (
            <button
              key={d}
              onClick={() => setDay(d)}
              className={`px-2 py-1 rounded-md text-[11px] font-medium whitespace-nowrap transition-all shrink-0 ${
                day === d
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'bg-slate-800/40 text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              {d} <span className="opacity-60">{dayCounts[d]}</span>
            </button>
          ))}
          <span className="w-px h-3.5 bg-white/10 mx-0.5 shrink-0" />
          {[
            { id: 'all', label: 'All', dot: 'bg-slate-500' },
            { id: 'Engineering', label: 'Engg', dot: 'bg-blue-500' },
            { id: 'S&T', label: 'S&T', dot: 'bg-emerald-500' },
            { id: 'Electrical', label: 'Elec', dot: 'bg-violet-500' },
            { id: 'joint', label: 'Joint', dot: 'bg-amber-500' },
          ].map(d => (
            <button
              key={d.id}
              onClick={() => setDept(d.id)}
              className={`flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium transition-all shrink-0 ${
                dept === d.id ? 'bg-white/10 text-white ring-1 ring-white/20' : 'text-slate-400 hover:text-white'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${d.dot}`} />{d.label}
            </button>
          ))}
          {hasFilters && (
            <button onClick={resetAll} className="text-[11px] text-indigo-400 hover:text-indigo-300 font-medium shrink-0 ml-1">Reset</button>
          )}
        </div>
      </div>

      {/* ── Summary ── */}
      <div className="flex gap-2 text-[11px]">
        {[
          { label: 'Blocks', val: stats.n, color: 'text-white' },
          { label: 'Hours', val: stats.hrs, color: 'text-emerald-400' },
          { label: 'Joint', val: stats.joint, color: 'text-amber-400' },
        ].map(s => (
          <div key={s.label} className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900/40 border border-white/6">
            <span className="text-slate-500">{s.label}</span>
            <span className={`font-bold ${s.color}`}>{s.val}</span>
          </div>
        ))}
      </div>

      {/* ── Content ── */}
      {filtered.length === 0 ? (
        <EmptyState onReset={resetAll} />
      ) : view === 'timeline' ? (
        <Timeline sections={sections} day={day} fmtH={fmtH} blockStyle={blockStyle} onSelect={setSelectedBlock} />
      ) : view === 'weekly' ? (
        <WeeklyView data={filtered} fmtH={fmtH} blockStyle={blockStyle} onSelect={setSelectedBlock} />
      ) : (
        <PlotlyView data={filtered} />
      )}

      {selectedBlock && <BlockModal block={selectedBlock} tasks={tasks} onClose={() => setSelectedBlock(null)} />}
    </div>
  );
}

function EmptyState({ onReset }) {
  return (
    <div className="rounded-xl border border-white/8 bg-slate-900/40 p-8 sm:p-12 text-center">
      <AlertTriangle className="w-7 h-7 text-amber-400/60 mx-auto mb-2" />
      <p className="text-sm text-slate-400 mb-3">No blocks match current filters.</p>
      <button onClick={onReset} className="px-4 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-medium">Reset</button>
    </div>
  );
}


/* ══════════════════════════════════════════════════════════════════════════════
   24-HOUR TIMELINE — full width
   ══════════════════════════════════════════════════════════════════════════════ */
function Timeline({ sections, day, fmtH, blockStyle, onSelect }) {
  const hours = Array.from({ length: 25 }, (_, i) => i);

  return (
    <div className="rounded-xl border border-white/8 bg-slate-900/50 overflow-hidden">
      {day === 'All' && (
        <div className="bg-indigo-950/30 border-b border-indigo-500/15 px-3 sm:px-4 py-2 flex items-center gap-2 text-[11px] text-indigo-300/80">
          <Info className="w-3.5 h-3.5 shrink-0" />
          <span className="hidden sm:inline">Composite view across all days. Select a day above for daily dispatch.</span>
          <span className="sm:hidden">All days shown. Select a day to filter.</span>
        </div>
      )}

      {/* Mobile: card list view */}
      <div className="block sm:hidden divide-y divide-white/5">
        {sections.map((sec, i) => (
          <div key={i} className="p-3">
            <div className="text-xs font-medium text-slate-300 mb-1.5">{sec.section} <span className="text-slate-600">({sec.corridor})</span></div>
            <div className="flex flex-wrap gap-1.5">
              {sec.blocks.map(b => {
                const s = blockStyle(b);
                return (
                  <button
                    key={b.block_id}
                    onClick={() => onSelect(b)}
                    className={`px-2 py-1 rounded-md bg-gradient-to-r ${s.bg} border ${s.border} text-[10px] text-white font-bold active:scale-95 transition-transform`}
                  >
                    {b.block_id.replace('BLK-','')} · {fmtH(b.block_start_hour)}-{fmtH(b.block_end_hour)}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Desktop: 24h timeline */}
      <div className="hidden sm:block overflow-x-auto">
        <div className="min-w-[700px]">
          {/* Header */}
          <div className="grid grid-cols-[180px_1fr] lg:grid-cols-[220px_1fr] border-b border-white/8 bg-slate-950/40 sticky top-0 z-10">
            <div className="px-3 py-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider border-r border-white/6">
              Section
            </div>
            <div className="relative h-7">
              {[[7,3],[17,3]].map(([start, dur], i) => (
                <div key={i} className="absolute top-0 bottom-0 bg-red-500/[0.04] border-x border-red-500/10"
                  style={{ left: `${(start/24)*100}%`, width: `${(dur/24)*100}%` }} />
              ))}
              {hours.map(h => (
                <div key={h} className="absolute top-0 bottom-0 border-l border-white/[0.04]" style={{ left: `${(h/24)*100}%` }}>
                  {h % 3 === 0 && (
                    <span className="absolute bottom-0.5 -translate-x-1/2 text-[9px] text-slate-500 font-mono">{String(h).padStart(2,'0')}</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Rows */}
          {sections.map((sec, i) => (
            <div key={i} className="grid grid-cols-[180px_1fr] lg:grid-cols-[220px_1fr] border-b border-white/[0.04] hover:bg-white/[0.01] transition-colors">
              <div className="px-3 py-1.5 border-r border-white/6 flex flex-col justify-center min-h-[46px]">
                <div className="text-xs font-medium text-slate-200 truncate leading-tight">{sec.section}</div>
                <div className="text-[10px] text-slate-500 flex items-center justify-between mt-0.5">
                  <span className="truncate">{sec.corridor}</span>
                  <span className="text-[9px] text-slate-600 font-mono ml-1 shrink-0">{sec.blocks.length}</span>
                </div>
              </div>
              <div className="relative min-h-[46px] flex items-center">
                {hours.map(h => (
                  <div key={h} className="absolute top-0 bottom-0 border-l border-white/[0.03]" style={{ left: `${(h/24)*100}%` }} />
                ))}
                {sec.blocks.map(b => {
                  const left = (b.block_start_hour / 24) * 100;
                  const width = Math.max(1.5, (b.total_hours / 24) * 100);
                  const s = blockStyle(b);
                  return (
                    <div
                      key={b.block_id}
                      onClick={() => onSelect(b)}
                      style={{ left: `${left}%`, width: `${width}%` }}
                      className={`absolute top-1 bottom-1 rounded-md bg-gradient-to-r ${s.bg} border ${s.border} cursor-pointer transition-all hover:brightness-125 hover:z-20 hover:scale-y-110 flex items-center px-1.5 overflow-hidden`}
                      title={`${b.block_id} — ${b.day_of_week} ${fmtH(b.block_start_hour)}-${fmtH(b.block_end_hour)} (${b.total_hours}h)\nDepts: ${b.departments}`}
                    >
                      <span className="text-[9px] font-bold text-white truncate leading-none drop-shadow-sm">
                        {b.block_id.replace('BLK-','')}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="px-3 py-1.5 border-t border-white/6 flex items-center gap-3 text-[10px] text-slate-500 overflow-x-auto">
        {Object.entries(DEPT_COLORS).map(([name, c]) => (
          <span key={name} className="flex items-center gap-1 shrink-0">
            <span className={`w-2 h-2 rounded-sm ${c.dot}`} />{name}
          </span>
        ))}
        <span className="flex items-center gap-1 shrink-0">
          <span className="w-5 h-2 rounded-sm bg-red-500/10 border border-red-500/20" />Peak
        </span>
      </div>
    </div>
  );
}


/* ══════════════════════════════════════════════════════════════════════════════
   WEEKLY VIEW — responsive grid
   ══════════════════════════════════════════════════════════════════════════════ */
function WeeklyView({ data, fmtH, blockStyle, onSelect }) {
  const days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-7 gap-3">
      {days.map(d => {
        const blocks = data.filter(b => b.day_of_week === d);
        return (
          <div key={d} className="rounded-xl border border-white/8 bg-slate-900/50 p-3 flex flex-col max-h-[350px]">
            <div className="flex items-center justify-between mb-2 pb-2 border-b border-white/6">
              <h4 className="text-xs font-semibold text-white flex items-center gap-1.5">
                <Calendar className="w-3 h-3 text-indigo-400" />{d.slice(0,3)}
              </h4>
              <span className="text-[10px] text-slate-500">{blocks.length}</span>
            </div>
            <div className="overflow-y-auto space-y-1.5 flex-1">
              {blocks.length === 0 ? (
                <p className="text-[11px] text-slate-600 italic text-center py-4">No blocks</p>
              ) : blocks.map(b => {
                const s = blockStyle(b);
                return (
                  <div key={b.block_id} onClick={() => onSelect(b)}
                    className={`p-2 rounded-lg bg-gradient-to-r ${s.bg} border ${s.border} cursor-pointer transition-all hover:brightness-110 active:scale-[0.98]`}>
                    <div className="flex items-center justify-between text-[10px] text-white font-bold">
                      <span>{b.block_id}</span>
                      <span className="font-mono opacity-80">{fmtH(b.block_start_hour)}-{fmtH(b.block_end_hour)}</span>
                    </div>
                    <div className="text-[10px] text-white/80 truncate mt-0.5">{b.section}</div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}


/* ══════════════════════════════════════════════════════════════════════════════
   PLOTLY VIEW — full width
   ══════════════════════════════════════════════════════════════════════════════ */
function PlotlyView({ data }) {
  const dayOrder = { Monday:0, Tuesday:1, Wednesday:2, Thursday:3, Friday:4, Saturday:5, Sunday:6 };
  const base = new Date('2026-09-07T00:00:00');

  const processed = data.map(b => {
    const s = new Date(base); s.setDate(s.getDate() + dayOrder[b.day_of_week]);
    s.setHours(Math.floor(b.block_start_hour), Math.round((b.block_start_hour % 1) * 60));
    const e = new Date(base); e.setDate(e.getDate() + dayOrder[b.day_of_week]);
    e.setHours(Math.floor(b.block_end_hour), Math.round((b.block_end_hour % 1) * 60));
    const cat = b.is_multi_department ? 'Integrated Joint' : b.departments.split(',')[0].trim();
    return { ...b, s, e, cat };
  });

  const cats = ['Engineering', 'S&T', 'Electrical', 'Integrated Joint'];
  const colors = { Engineering: '#3b82f6', 'S&T': '#10b981', Electrical: '#8b5cf6', 'Integrated Joint': '#f59e0b' };

  const traces = cats.map(c => {
    const sub = processed.filter(d => d.cat === c);
    if (!sub.length) return null;
    return {
      type: 'bar', orientation: 'h', name: c,
      x: sub.map(d => d.e.getTime() - d.s.getTime()),
      base: sub.map(d => d.s.getTime()),
      y: sub.map(d => d.section),
      marker: { color: colors[c], line: { color: 'rgba(255,255,255,0.2)', width: 0.5 } },
      hoverinfo: 'text',
      text: sub.map(d => `<b>${d.block_id}</b><br>${d.section}<br>${d.day_of_week} ${d.block_start_hour.toFixed(1)}-${d.block_end_hour.toFixed(1)}h<br>${d.departments}`)
    };
  }).filter(Boolean);

  const uniqueY = [...new Set(processed.map(d => d.section))];
  const h = Math.max(400, uniqueY.length * 28 + 80);

  return (
    <div className="rounded-xl border border-white/8 bg-slate-900/50 p-2 sm:p-3 overflow-x-auto">
      <Plot
        data={traces}
        layout={{
          paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
          font: { family: 'Inter', color: '#94a3b8', size: 11 },
          barmode: 'overlay', autosize: true, height: h,
          margin: { l: 140, r: 16, t: 30, b: 50 },
          xaxis: { type: 'date', gridcolor: 'rgba(255,255,255,0.04)', tickformat: '%a %H:%M', dtick: 43200000 },
          yaxis: { autorange: 'reversed', gridcolor: 'rgba(255,255,255,0.04)', tickfont: { size: 10, color: '#cbd5e1' } },
          legend: { orientation: 'h', y: 1.06, x: 0.5, xanchor: 'center', font: { color: '#e2e8f0', size: 11 } },
        }}
        useResizeHandler style={{ width: '100%' }}
        config={{ displayModeBar: true, modeBarButtonsToRemove: ['lasso2d','select2d'], displaylogo: false }}
      />
    </div>
  );
}
