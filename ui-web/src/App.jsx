import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Settings, RefreshCw, Layers, CheckCircle, Clock,
  Activity, BarChart3, Train, ArrowRight, Map, Zap, Truck,
  PanelLeftClose, PanelLeft, Columns2, ChevronDown, Home
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import RailwayGantt from './components/RailwayGantt';
import BlockModal from './components/BlockModal';
import AiChatbot from './components/AiChatbot';
import AnalyticsCharts from './components/AnalyticsCharts';
import RailwayMap from './components/RailwayMap';
import IncidentSimulator from './components/IncidentSimulator';
import FleetManager from './components/FleetManager';
import ReportExporter from './components/ReportExporter';

function cn(...inputs) { return twMerge(clsx(inputs)); }

const API = import.meta.env.MODE === 'development' ? 'http://localhost:8000/api' : '/api';

/* ────────────────────── Navigation Structure ────────────────────── */
const NAV_SECTIONS = [
  {
    category: 'Overview',
    items: [
      { id: 'home',      label: 'Home',            icon: Home },
    ],
  },
  {
    category: 'Operations Desk',
    items: [
      { id: 'gantt',     label: 'Gantt Dispatch',  icon: Clock },
      { id: 'map',       label: 'Live Track Map',  icon: Map,   badge: 'live' },
      { id: 'incidents', label: 'Incident Sim',    icon: Zap,   badge: 'alert' },
    ],
  },
  {
    category: 'Data Science',
    items: [
      { id: 'charts', label: 'Analytics Hub', icon: BarChart3 },
    ],
  },
  {
    category: 'Asset Management',
    items: [
      { id: 'fleet',  label: 'Fleet Manager',      icon: Truck },
      { id: 'blocks', label: 'Maint. Blocks',      icon: Layers, badge: 'count' },
    ],
  },
];

const ALL_TABS = NAV_SECTIONS.flatMap(s => s.items);

/* ════════════════════════ MAIN APP ════════════════════════ */
export default function App() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState('home');
  const [modalBlock, setModalBlock] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [incidentAlert, setIncidentAlert] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [cockpitMode, setCockpitMode] = useState(false);
  const [cockpitLeft, setCockpitLeft] = useState('map');
  const [cockpitRight, setCockpitRight] = useState('gantt');

  /* ── Data fetching ── */
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

  /* ── WebSocket ── */
  useEffect(() => {
    const wsUrl = import.meta.env.MODE === 'development'
      ? 'ws://localhost:8000/api/ws/stream'
      : `ws://${window.location.host}/api/ws/stream`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => setWsConnected(false);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.event === 'pipeline_updated') fetchData();
        if (msg.event === 'incident_injected') {
          setIncidentAlert({ type: msg.incident_type, km: msg.km_marker, severity: msg.severity });
          fetchData();
          setTimeout(() => setIncidentAlert(null), 5000);
        }
      } catch (err) {}
    };

    return () => ws.close();
  }, []);

  /* ── Derived ── */
  const s = data?.stats;
  const blockCount = data?.schedule?.length ?? 0;
  const activeLabel = ALL_TABS.find(t => t.id === activeTab)?.label || 'Dashboard';

  /* ── Panel renderer (shared by single-view and cockpit panes) ── */
  const renderPanel = (tabId) => {
    if (!data || tabId === 'home') {
      return (
        <div className="flex flex-col items-center justify-center min-h-[500px] animate-fade-in-up py-10 px-4">
          <div className="flex flex-wrap items-center justify-center gap-2 mb-6">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] sm:text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Train className="w-3.5 h-3.5" /> PS-26027
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] sm:text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              OR-Tools + DBSCAN + XGBoost
            </span>
            {wsConnected && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] sm:text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" /> LIVE
              </span>
            )}
          </div>

          <h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold text-white tracking-tight leading-[1.1] mb-6 font-outfit text-center">
            Smart Railway <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-purple-500 to-rose-500 bg-[length:200%_auto] animate-gradient-x">
              Block Command Center
            </span>
          </h1>

          <p className="text-slate-400 text-base sm:text-lg max-w-2xl mx-auto mb-10 leading-relaxed text-center">
            Predict maintenance needs, optimize corridor schedules, coordinate across
            Engineering, S&T, and Electrical — with live maps, incident simulation, and AI insights.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto">
            <button
              onClick={runPipeline}
              disabled={loading}
              className="group flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl font-bold text-black bg-[#10b981] hover:bg-[#34d399] transition-all shadow-[0_0_30px_rgba(16,185,129,0.3)] hover:shadow-[0_0_40px_rgba(16,185,129,0.4)] disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-auto text-[15px]"
            >
              {loading ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <>Start Optimizing <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" /></>
              )}
            </button>
            {data && (
              <button
                onClick={() => {
                  setActiveTab('map');
                  if (cockpitMode) setCockpitMode(false);
                }}
                className="flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl font-bold text-white bg-[#111111] hover:bg-[#1a1a1a] border border-[#222] hover:border-[#333] transition-all w-full sm:w-auto text-[15px]"
              >
                View Map
              </button>
            )}
          </div>

          {/* ── KPI Cards Section ── */}
          {data && s && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-5 mt-16 sm:mt-24 w-full max-w-5xl">
              <KpiBox icon={<Activity />}    value={`${s.asset_availability_pct.toFixed(1)}%`}    label="Asset Availability"  color="text-purple-400"  animation="animate-pulse" />
              <KpiBox icon={<BarChart3 />}   value={`${s.block_utilization_pct.toFixed(1)}%`}     label="Block Utilization"   color="text-emerald-400" animation="animate-float" />
              <KpiBox icon={<CheckCircle />} value={`${s.schedule_rate_pct.toFixed(0)}%`}         label="Schedule Rate"       color="text-sky-400"     animation="animate-pulse" />
              <KpiBox icon={<Layers />}      value={`${s.integration_rate_pct.toFixed(1)}%`}      label="Integration Rate"    color="text-pink-400"    animation="animate-float-delayed" />
            </div>
          )}
        </div>
      );
    }
    switch (tabId) {
      case 'gantt':     return <RailwayGantt schedule={data.schedule} tasks={data.tasks} />;
      case 'map':       return <RailwayMap />;
      case 'incidents': return <IncidentSimulator onIncidentInjected={fetchData} />;
      case 'fleet':     return <FleetManager />;
      case 'charts':    return <AnalyticsCharts schedule={data.schedule} tasks={data.tasks} />;
      case 'blocks':    return (
        <div className="space-y-4">
          <ReportExporter schedule={data.schedule} stats={data.stats} />
          <DataTable data={data.schedule} onSelect={setModalBlock} />
        </div>
      );
      default: return null;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-black text-slate-200 font-inter selection:bg-purple-500/30">

      {/* ══════════════════════ SIDEBAR ══════════════════════ */}
      <aside
        className={cn(
          "sidebar-panel flex flex-col h-full border-r border-[#141418] transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] shrink-0 z-40 overflow-hidden",
          sidebarOpen ? "w-[256px]" : "w-[68px]"
        )}
      >
        {/* ── Logo ── */}
        <div
          className={cn(
            "flex items-center gap-3 h-16 border-b border-[#141418] shrink-0 transition-all duration-300",
            sidebarOpen ? "px-5" : "justify-center px-0"
          )}
        >
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-emerald-500/80 to-teal-600/80 flex items-center justify-center shadow-lg shadow-emerald-500/10 shrink-0">
            <Train className="w-5 h-5 text-white" />
          </div>
          <div
            className={cn(
              "flex flex-col overflow-hidden transition-all duration-300",
              sidebarOpen ? "opacity-100 w-auto" : "opacity-0 w-0"
            )}
          >
            <span className="text-white font-bold text-[15px] tracking-wide font-outfit whitespace-nowrap">
              RailOpt
            </span>
            <span className="text-[10px] text-slate-600 font-medium -mt-0.5 whitespace-nowrap">
              Command Center
            </span>
          </div>
        </div>

        {/* ── Navigation Groups ── */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-5 custom-scrollbar">
          {NAV_SECTIONS.map((section) => (
            <div key={section.category}>
              {/* Category label */}
              {sidebarOpen ? (
                <div className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#3a3a48] px-3 mb-2 truncate">
                  {section.category}
                </div>
              ) : (
                <div className="w-6 h-px bg-[#1a1a22] mx-auto mb-2 mt-1" />
              )}

              {/* Items */}
              <div className="space-y-0.5">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = !cockpitMode && activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        setActiveTab(item.id);
                        if (cockpitMode) setCockpitMode(false);
                      }}
                      title={!sidebarOpen ? item.label : undefined}
                      className={cn(
                        "sidebar-nav-item group w-full flex items-center gap-3 rounded-xl text-[13px] font-medium transition-all duration-200",
                        sidebarOpen ? "px-3 py-2.5" : "px-0 py-2.5 justify-center",
                        isActive
                          ? "sidebar-nav-active bg-emerald-500/[0.08] text-emerald-400"
                          : "text-[#707080] hover:text-[#c0c0cc] hover:bg-white/[0.03]"
                      )}
                    >
                      <div className="relative shrink-0">
                        <Icon className="w-[18px] h-[18px]" />
                        {item.badge === 'live' && wsConnected && (
                          <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-emerald-400 animate-pulse ring-2 ring-[#070709]" />
                        )}
                        {item.badge === 'alert' && incidentAlert && (
                          <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-amber-400 animate-pulse ring-2 ring-[#070709]" />
                        )}
                      </div>

                      {sidebarOpen && (
                        <span className="truncate flex-1 text-left">{item.label}</span>
                      )}

                      {sidebarOpen && item.badge === 'live' && wsConnected && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 uppercase tracking-wider">
                          Live
                        </span>
                      )}
                      {sidebarOpen && item.badge === 'count' && (
                        <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-[#1a1a22] text-[#808090]">
                          {blockCount}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* ── Bottom Controls ── */}
        <div className="border-t border-[#141418] p-3 space-y-1 shrink-0">
          {/* Cockpit Mode Toggle */}
          <button
            onClick={() => setCockpitMode(!cockpitMode)}
            title={!sidebarOpen ? 'Cockpit Mode' : undefined}
            className={cn(
              "w-full flex items-center gap-3 rounded-xl text-[13px] font-medium transition-all duration-200",
              sidebarOpen ? "px-3 py-2.5" : "px-0 py-2.5 justify-center",
              cockpitMode
                ? "bg-purple-500/10 text-purple-400"
                : "text-[#505060] hover:text-[#909098] hover:bg-white/[0.03]"
            )}
          >
            <Columns2 className="w-[18px] h-[18px] shrink-0" />
            {sidebarOpen && <span className="truncate">Cockpit Mode</span>}
          </button>

          {/* Collapse Toggle */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className={cn(
              "w-full flex items-center gap-3 rounded-xl text-[13px] font-medium text-[#505060] hover:text-[#909098] hover:bg-white/[0.03] transition-all duration-200",
              sidebarOpen ? "px-3 py-2.5" : "px-0 py-2.5 justify-center"
            )}
          >
            {sidebarOpen ? (
              <>
                <PanelLeftClose className="w-[18px] h-[18px] shrink-0" />
                <span className="truncate">Collapse</span>
              </>
            ) : (
              <PanelLeft className="w-[18px] h-[18px] shrink-0" />
            )}
          </button>
        </div>
      </aside>

      {/* ══════════════════════ MAIN AREA ══════════════════════ */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">

        {/* ── Top Bar ── */}
        <header className="flex items-center justify-between h-16 px-6 border-b border-[#141418] bg-[#050508]/80 backdrop-blur-xl shrink-0 gap-4">
          {/* Page title */}
          <div className="flex items-center gap-3 shrink-0">
            <h2 className="text-white font-semibold text-lg font-outfit tracking-tight">
              {cockpitMode ? 'Cockpit View' : activeLabel}
            </h2>
            {cockpitMode && (
              <span className="text-[10px] font-bold px-2 py-1 rounded-full bg-purple-500/10 text-purple-400 uppercase tracking-wider">
                Split
              </span>
            )}
          </div>

          {/* KPI chips — center */}
          {data && s && (
            <div className="hidden lg:flex items-center gap-2 flex-1 justify-center min-w-0">
              <KpiChip label="Avail" value={`${s.asset_availability_pct.toFixed(1)}%`} color="text-purple-400" />
              <KpiChip label="Util"  value={`${s.block_utilization_pct.toFixed(1)}%`}  color="text-emerald-400" />
              <KpiChip label="Sched" value={`${s.schedule_rate_pct.toFixed(0)}%`}       color="text-sky-400" />
              <KpiChip label="Integ" value={`${s.integration_rate_pct.toFixed(1)}%`}    color="text-pink-400" />
            </div>
          )}

          {/* Actions — right */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="flex items-center gap-1.5">
              <div className={cn("w-2 h-2 rounded-full", wsConnected ? "bg-emerald-400 animate-pulse" : "bg-rose-500")} />
              <span className="text-[11px] text-slate-500 font-medium hidden sm:inline">
                {wsConnected ? 'Live' : 'Offline'}
              </span>
            </div>
            <button
              onClick={runPipeline}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-[13px] font-semibold text-black bg-emerald-500 hover:bg-emerald-400 transition-colors disabled:opacity-50 shadow-lg shadow-emerald-500/20"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <ArrowRight className="w-4 h-4" />
              )}
              <span className="hidden sm:inline">{loading ? 'Running...' : 'Generate'}</span>
            </button>
          </div>
        </header>

        {/* ── Emergency Alert Banner ── */}
        {incidentAlert && (
          <div className="bg-red-600/90 backdrop-blur border-b border-red-500 px-4 py-2 flex items-center justify-center gap-3 animate-fade-in-up shrink-0">
            <div className="w-2 h-2 rounded-full bg-white animate-ping" />
            <span className="text-white font-bold text-sm">
              EMERGENCY: {incidentAlert.type} at Km {incidentAlert.km?.toFixed(0)} — Re-optimizing...
            </span>
            <span className="text-red-200 text-xs">
              ({incidentAlert.severity?.toUpperCase()})
            </span>
          </div>
        )}

        {/* ── Content Area ── */}
        <main className="flex-1 overflow-auto">
          {cockpitMode ? (
            /* ── Split-Screen Cockpit ── */
            <div className="grid grid-cols-2 h-full">
              {/* Left Pane */}
              <div className="flex flex-col border-r border-[#141418] overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-2.5 bg-[#08080a] border-b border-[#141418] shrink-0">
                  <div className="w-1.5 h-4 rounded-full bg-emerald-500/60 shrink-0" />
                  <select
                    value={cockpitLeft}
                    onChange={(e) => setCockpitLeft(e.target.value)}
                    className="cockpit-select bg-[#111115] border border-[#222230] rounded-lg px-2.5 py-1.5 text-xs text-slate-300 font-medium focus:outline-none focus:border-emerald-500/50 transition-colors"
                  >
                    {ALL_TABS.map((t) => (
                      <option key={t.id} value={t.id}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div className="flex-1 overflow-auto p-4">
                  {renderPanel(cockpitLeft)}
                </div>
              </div>
              {/* Right Pane */}
              <div className="flex flex-col overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-2.5 bg-[#08080a] border-b border-[#141418] shrink-0">
                  <div className="w-1.5 h-4 rounded-full bg-purple-500/60 shrink-0" />
                  <select
                    value={cockpitRight}
                    onChange={(e) => setCockpitRight(e.target.value)}
                    className="cockpit-select bg-[#111115] border border-[#222230] rounded-lg px-2.5 py-1.5 text-xs text-slate-300 font-medium focus:outline-none focus:border-purple-500/50 transition-colors"
                  >
                    {ALL_TABS.map((t) => (
                      <option key={t.id} value={t.id}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div className="flex-1 overflow-auto p-4">
                  {renderPanel(cockpitRight)}
                </div>
              </div>
            </div>
          ) : (
            /* ── Single-View Mode ── */
            <div className="p-6">
              {renderPanel(activeTab)}
            </div>
          )}
        </main>
      </div>

      {/* ── Modal + Chatbot ── */}
      {modalBlock && (
        <BlockModal
          block={modalBlock}
          tasks={data?.tasks || []}
          onClose={() => setModalBlock(null)}
        />
      )}
      <AiChatbot />
    </div>
  );
}

/* ════════════════════════ KPI Chip ════════════════════════ */
function KpiChip({ label, value, color }) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0a0a0d] border border-[#1a1a22] shrink-0">
      <span className={cn("text-sm font-bold tracking-tight", color)}>{value}</span>
      <span className="text-[10px] text-slate-600 font-medium uppercase tracking-wider">{label}</span>
    </div>
  );
}

/* ════════════════════════ DataTable ════════════════════════ */
function DataTable({ data, onSelect }) {
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

/* ════════════════════════ KPI Box ════════════════════════ */
function KpiBox({ icon, value, label, color, animation }) {
  return (
    <div className="flex flex-col items-center justify-center p-6 sm:p-8 rounded-2xl bg-[#0a0a0a] border border-[#1a1a1a] hover:border-[#333] transition-colors group">
      <div className={cn("mb-3 opacity-90 transition-transform group-hover:scale-110", color, animation)}>
        {icon}
      </div>
      <div className="text-2xl sm:text-4xl font-extrabold text-white mb-1.5 font-outfit tracking-tight">
        {value}
      </div>
      <div className="text-[10px] sm:text-xs text-slate-500 font-semibold tracking-wide uppercase">
        {label}
      </div>
    </div>
  );
}
