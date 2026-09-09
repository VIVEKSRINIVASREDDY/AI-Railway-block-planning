import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Settings, RefreshCw, Layers, CheckCircle, Clock,
  Activity, BarChart3, Train, Menu, X
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import RailwayGantt from './components/RailwayGantt';
import BlockModal from './components/BlockModal';
import AiChatbot from './components/AiChatbot';

function cn(...inputs) { return twMerge(clsx(inputs)); }

const API = import.meta.env.MODE === 'development' ? 'http://localhost:8000/api' : '/api';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState('gantt');
  const [modalBlock, setModalBlock] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [kpi, sched, tasks] = await Promise.all([
        axios.get(`${API}/kpis`),
        axios.get(`${API}/schedule`),
        axios.get(`${API}/tasks`).catch(() => ({ data: { tasks: [] } })),
      ]);
      setData({
        stats: kpi.data,
        schedule: sched.data.schedule || [],
        tasks: tasks.data.tasks || [],
      });
    } catch (err) {
      if (err.response?.status !== 404) console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const runPipeline = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/generate`);
      await fetchData();
    } catch (err) {
      console.error(err);
      alert('Pipeline failed. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  // WebSocket Connection for Real-Time Live Updates
  useEffect(() => {
    const wsUrl = import.meta.env.MODE === 'development' ? 'ws://localhost:8000/api/ws/stream' : `ws://${window.location.host}/api/ws/stream`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.event === 'pipeline_updated') {
          // Soft-refresh the data when a live update happens
          fetchData();
        }
      } catch (err) {
        console.error("WS Parse error", err);
      }
    };

    return () => ws.close();
  }, []);

  const s = data?.stats;

  return (
    <div className="min-h-screen text-slate-200">

      {/* ═══ HEADER — full width ═══ */}
      <header className="w-full px-4 sm:px-6 lg:px-8 pt-4 pb-3">
        <div className="glass-panel px-5 py-4 sm:px-8 sm:py-5 relative overflow-hidden">
          <div className="absolute -top-20 -right-20 w-64 h-64 bg-indigo-500/15 rounded-full blur-[80px] pointer-events-none" />

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 relative z-10">
            <div>
              <div className="flex flex-wrap items-center gap-1.5 mb-1">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/15 text-indigo-300 border border-indigo-500/20">
                  <Train className="w-3 h-3" /> PS-26027
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/20">
                  OR-Tools + DBSCAN + XGBoost
                </span>
                {wsConnected && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/20 ml-2 animate-pulse">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-500" /> LIVE
                  </span>
                )}
              </div>
              <h1 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-white leading-tight">
                AI Block Planning System
              </h1>
              <p className="text-slate-400 text-xs sm:text-sm mt-0.5 max-w-lg">
                Multi-department maintenance scheduling for Indian Railways corridors.
              </p>
            </div>

            <button
              onClick={runPipeline}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 sm:px-5 sm:py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs sm:text-sm rounded-lg font-semibold transition-all shadow-lg shadow-indigo-600/20 disabled:opacity-50 disabled:cursor-not-allowed shrink-0 w-full sm:w-auto justify-center"
            >
              <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
              {loading ? "Running..." : "Run Pipeline"}
            </button>
          </div>
        </div>
      </header>

      {!data ? (
        /* ═══ EMPTY STATE ═══ */
        <div className="px-4 sm:px-6 lg:px-8 py-12 sm:py-16 text-center">
          <div className="glass-panel max-w-sm mx-auto p-6 sm:p-8 flex flex-col items-center">
            <Settings className="w-10 h-10 sm:w-12 sm:h-12 text-slate-500 mb-4 animate-[spin_4s_linear_infinite]" />
            <h2 className="text-lg sm:text-xl font-bold text-white mb-1">System Ready</h2>
            <p className="text-slate-400 text-xs sm:text-sm mb-5">Generate data and run optimization.</p>
            <button
              onClick={runPipeline}
              disabled={loading}
              className="w-full px-5 py-2.5 bg-white text-slate-900 hover:bg-slate-100 rounded-lg font-semibold text-sm transition-all"
            >
              {loading ? "Generating..." : "Start Optimization"}
            </button>
          </div>
        </div>
      ) : (
        /* ═══ DASHBOARD — full width ═══ */
        <div className="w-full px-4 sm:px-6 lg:px-8 pb-8 space-y-4 animate-fade-in-up">

          {/* KPI Cards — 2 cols on mobile, 4 cols on desktop */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <KpiCard
              label="Asset Availability"
              value={`${s.asset_availability_pct.toFixed(1)}%`}
              sub="Track-hours free for trains"
              icon={<Activity className="w-4 h-4 sm:w-5 sm:h-5" />}
              accent="text-emerald-400"
              bar="bg-emerald-500"
              pct={s.asset_availability_pct}
            />
            <KpiCard
              label="Block Utilization"
              value={`${s.block_utilization_pct.toFixed(1)}%`}
              sub="Window capacity used"
              icon={<BarChart3 className="w-4 h-4 sm:w-5 sm:h-5" />}
              accent="text-sky-400"
              bar="bg-sky-500"
              pct={s.block_utilization_pct}
            />
            <KpiCard
              label="Schedule Rate"
              value={`${s.schedule_rate_pct.toFixed(0)}%`}
              sub={`${s.blocks_scheduled} of ${s.total_blocks} blocks`}
              icon={<CheckCircle className="w-4 h-4 sm:w-5 sm:h-5" />}
              accent="text-amber-400"
              bar="bg-amber-500"
              pct={s.schedule_rate_pct}
            />
            <KpiCard
              label="Integration Rate"
              value={`${s.integration_rate_pct.toFixed(1)}%`}
              sub={`${s.multi_dept_blocks_scheduled} joint blocks`}
              icon={<Layers className="w-4 h-4 sm:w-5 sm:h-5" />}
              accent="text-violet-400"
              bar="bg-violet-500"
              pct={s.integration_rate_pct}
            />
          </div>

          {/* Tab Panel — full width */}
          <div className="glass-panel overflow-hidden">
            <div className="flex border-b border-white/8 px-1 overflow-x-auto">
              {[
                { id: 'gantt', label: 'Gantt Timeline', icon: <Clock className="w-4 h-4" /> },
                { id: 'blocks', label: `Block Table (${data.schedule.length})`, icon: <Layers className="w-4 h-4" /> },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center gap-1.5 px-4 py-2.5 text-xs sm:text-sm font-medium transition-all border-b-2 -mb-px whitespace-nowrap",
                    activeTab === tab.id
                      ? "border-indigo-500 text-white"
                      : "border-transparent text-slate-400 hover:text-slate-200"
                  )}
                >
                  {tab.icon}{tab.label}
                </button>
              ))}
            </div>

            <div className="p-3 sm:p-5">
              {activeTab === 'gantt' && <RailwayGantt schedule={data.schedule} tasks={data.tasks} />}
              {activeTab === 'blocks' && <DataTable data={data.schedule} onSelect={setModalBlock} />}
            </div>
          </div>
        </div>
      )}

      {modalBlock && (
        <BlockModal block={modalBlock} tasks={data?.tasks || []} onClose={() => setModalBlock(null)} />
      )}

      {/* AI Chatbot Assistant */}
      <AiChatbot />
    </div>
  );
}


/* ═══ KPI CARD ═══ */
function KpiCard({ label, value, sub, icon, accent, bar, pct }) {
  return (
    <div className="glass-card flex flex-col gap-2 sm:gap-3">
      <div className="flex items-center justify-between">
        <span className="text-[10px] sm:text-[11px] font-semibold tracking-wide text-slate-400 uppercase leading-tight">{label}</span>
        <span className={accent}>{icon}</span>
      </div>
      <div className={cn("text-2xl sm:text-3xl font-extrabold leading-none", accent)}>{value}</div>
      <div className="w-full h-1 rounded-full bg-white/5 overflow-hidden">
        <div className={cn("h-full rounded-full transition-all duration-700", bar)} style={{ width: `${Math.min(100, pct)}%` }} />
      </div>
      <span className="text-[10px] sm:text-[12px] text-slate-500 leading-tight">{sub}</span>
    </div>
  );
}


/* ═══ DATA TABLE ═══ */
function DataTable({ data, onSelect }) {
  const [q, setQ] = useState('');
  if (!data?.length) return null;

  const rows = data.filter(r => {
    if (!q) return true;
    const s = q.toLowerCase();
    return [r.block_id, r.section, r.corridor, r.departments, r.day_of_week]
      .some(f => f?.toLowerCase().includes(s));
  });

  const fmtH = h => {
    const hh = Math.floor(h), mm = Math.round((h - hh) * 60);
    return `${String(hh).padStart(2,'0')}:${String(mm).padStart(2,'0')}`;
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <input
          type="text"
          placeholder="Filter blocks..."
          value={q}
          onChange={e => setQ(e.target.value)}
          className="bg-slate-800/60 border border-white/8 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 w-full sm:w-64 focus:outline-none focus:border-indigo-500/50"
        />
        <span className="text-[11px] text-slate-500">{rows.length} of {data.length} — tap row to inspect</span>
      </div>

      {/* Mobile card view */}
      <div className="block sm:hidden space-y-2">
        {rows.slice(0, 50).map((r, i) => (
          <div
            key={i}
            onClick={() => onSelect(r)}
            className="bg-slate-800/30 border border-white/6 rounded-lg p-3 active:bg-white/5 transition-colors"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="font-mono text-xs font-semibold text-indigo-400">{r.block_id}</span>
              <span className="text-emerald-400 text-xs font-semibold">{r.total_hours.toFixed(1)}h</span>
            </div>
            <div className="text-sm text-white font-medium">{r.section}</div>
            <div className="text-[11px] text-slate-500 mt-0.5">{r.corridor} — {r.day_of_week} {fmtH(r.block_start_hour)}-{fmtH(r.block_end_hour)}</div>
            <div className="flex flex-wrap gap-1 mt-1.5">
              {r.departments.split(',').map(d => {
                const t = d.trim();
                const c = t === 'Engineering' ? 'bg-blue-500/15 text-blue-300'
                  : t === 'S&T' ? 'bg-emerald-500/15 text-emerald-300'
                  : 'bg-violet-500/15 text-violet-300';
                return <span key={d} className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${c}`}>{t}</span>;
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Desktop table view */}
      <div className="hidden sm:block overflow-x-auto rounded-lg border border-white/8">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-slate-800/50 text-[11px] text-slate-400 uppercase tracking-wider font-semibold border-b border-white/6">
              <th className="px-4 py-2.5">Block</th>
              <th className="px-4 py-2.5">Section</th>
              <th className="px-4 py-2.5">Day & Time</th>
              <th className="px-4 py-2.5">Hrs</th>
              <th className="px-4 py-2.5">Departments</th>
              <th className="px-4 py-2.5 text-center">CI</th>
              <th className="px-4 py-2.5 text-right">Tasks</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {rows.map((r, i) => (
              <tr key={i} onClick={() => onSelect(r)} className="border-b border-white/4 hover:bg-white/[0.025] cursor-pointer transition-colors">
                <td className="px-4 py-2.5 font-mono text-xs font-semibold text-indigo-400">{r.block_id}</td>
                <td className="px-4 py-2.5">
                  <div className="text-white text-sm font-medium">{r.section}</div>
                  <div className="text-[11px] text-slate-500">{r.corridor}</div>
                </td>
                <td className="px-4 py-2.5">
                  <div className="text-slate-200 text-sm">{r.day_of_week}</div>
                  <div className="text-[11px] text-slate-500 font-mono">{fmtH(r.block_start_hour)}-{fmtH(r.block_end_hour)}</div>
                </td>
                <td className="px-4 py-2.5 text-emerald-400 font-semibold text-sm">{r.total_hours.toFixed(1)}</td>
                <td className="px-4 py-2.5">
                  <div className="flex flex-wrap gap-1">
                    {r.departments.split(',').map(d => {
                      const t = d.trim();
                      const c = t === 'Engineering' ? 'bg-blue-500/15 text-blue-300'
                        : t === 'S&T' ? 'bg-emerald-500/15 text-emerald-300'
                        : 'bg-violet-500/15 text-violet-300';
                      return <span key={d} className={`px-1.5 py-0.5 rounded text-[11px] font-medium ${c}`}>{t}</span>;
                    })}
                  </div>
                </td>
                <td className="px-4 py-2.5 text-center">
                  <span className={`text-xs font-bold ${
                    (r.max_criticality||0) >= 75 ? 'text-red-400' :
                    (r.max_criticality||0) >= 50 ? 'text-amber-400' : 'text-sky-400'
                  }`}>
                    {(r.max_criticality || r.avg_criticality || 0).toFixed(0)}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-right text-slate-300 font-semibold">{r.task_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
