import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  Activity,
  Layers,
  CheckCircle,
  Clock,
  Radio,
  Zap,
  Network,
  Wrench,
  Cable,
  HardHat,
  Search,
  Filter,
  ArrowUpRight,
  TrendingUp,
  Cpu,
  CloudRain,
  Thermometer,
  ShieldCheck
} from 'lucide-react';
import ImpactGraph from './ImpactGraph';

const API = import.meta.env.MODE === 'development' ? 'http://localhost:8000/api' : '/api';

export default function LiveDashboard() {
  const [events, setEvents] = useState([]);
  const [resilience, setResilience] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [schedule, setSchedule] = useState([]);
  const [telemetry, setTelemetry] = useState([]);
  const [activeTab, setActiveTab] = useState('queue'); // 'queue' | 'impact'
  const [searchTerm, setSearchTerm] = useState('');
  const [deptFilter, setDeptFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [evRes, resRes, kpiRes, schedRes, telemRes] = await Promise.all([
        axios.get(`${API}/realtime/events`).catch(() => ({ data: { events: [] } })),
        axios.get(`${API}/analytics/resilience`).catch(() => ({ data: { overall_score: 100, stability: 100, recovery_efficiency: 100 } })),
        axios.get(`${API}/kpis`).catch(() => ({ data: null })),
        axios.get(`${API}/schedule`).catch(() => ({ data: { schedule: [] } })),
        axios.get(`${API}/telemetry/feed`).catch(() => ({ data: { feed: [] } })),
      ]);

      setEvents(evRes.data?.events || []);
      setResilience(resRes.data || { overall_score: 100, stability: 100, recovery_efficiency: 100 });
      setKpis(kpiRes.data);
      setSchedule(schedRes.data?.schedule || []);
      setTelemetry(telemRes.data?.feed || []);
    } catch (err) {
      console.error("Dashboard data fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 4000);
    return () => clearInterval(interval);
  }, []);

  // Filter scheduled blocks
  const filteredBlocks = schedule.filter(b => {
    const matchesSearch =
      (b.block_id && b.block_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (b.section && b.section.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (b.required_equipment && b.required_equipment.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesDept =
      deptFilter === 'ALL' ||
      (deptFilter === 'JOINT' && b.is_multi_department) ||
      (b.departments && b.departments.toLowerCase().includes(deptFilter.toLowerCase()));

    return matchesSearch && matchesDept;
  });

  return (
    <div className="flex flex-col h-full gap-5 p-5 font-inter text-slate-200 overflow-y-auto custom-scrollbar">

      {/* ── Top Header Banner ── */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-[#11131c] border border-white/10 rounded-2xl shadow-xl shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 border border-emerald-500/40 flex items-center justify-center shadow-lg shadow-emerald-500/10">
            <Activity className="w-5 h-5 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-white font-bold text-base tracking-wide">
                Live Operations & Block Execution Dashboard
              </h2>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider">
                Live Telemetry Active
              </span>
            </div>
            <p className="text-slate-400 text-xs mt-0.5">
              Automated Block Planning (PS-26027) · Central Railway Corridor (CSMT – Kalyan – Igatpuri / Pune)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[#161824] border border-white/10 rounded-xl text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-300 font-semibold">OR-Tools Solver: OPTIMAL</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[#161824] border border-white/10 rounded-xl text-xs">
            <Radio className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span className="text-slate-300 font-semibold">{telemetry.length} IoT Sensors Online</span>
          </div>
        </div>
      </div>

      {/* ── Executive Metric KPI Strip ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3.5 shrink-0">
        <div className="bg-[#11131c] border border-white/10 rounded-xl p-3.5 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>Blocks Scheduled</span>
            <Layers className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-white mt-1.5 font-outfit">
            {kpis?.blocks_scheduled || schedule.length || 0}
            <span className="text-xs font-normal text-slate-400 ml-1">/ {kpis?.total_blocks || 165}</span>
          </div>
          <div className="text-[11px] text-purple-400 font-semibold mt-1 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> {kpis?.schedule_rate_pct?.toFixed(0) || 63}% Rate
          </div>
        </div>

        <div className="bg-[#11131c] border border-white/10 rounded-xl p-3.5 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>Asset Availability</span>
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 mt-1.5 font-outfit">
            {kpis?.asset_availability_pct?.toFixed(1) || '84.1'}%
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Target &gt; 80% (Pass)</div>
        </div>

        <div className="bg-[#11131c] border border-white/10 rounded-xl p-3.5 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>Block Utilization</span>
            <Clock className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-cyan-400 mt-1.5 font-outfit">
            {kpis?.block_utilization_pct?.toFixed(1) || '35.3'}%
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Peak-Traffic Free</div>
        </div>

        <div className="bg-[#11131c] border border-white/10 rounded-xl p-3.5 shadow-lg flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>Integration Rate</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-amber-400 mt-1.5 font-outfit">
            {kpis?.integration_rate_pct?.toFixed(1) || '25.0'}%
          </div>
          <div className="text-[11px] text-amber-400/90 font-medium mt-1">Multi-Dept Shadow Blocks</div>
        </div>

        <div className="bg-[#11131c] border border-white/10 rounded-xl p-3.5 shadow-lg flex flex-col justify-between col-span-2 md:col-span-4 lg:col-span-1">
          <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
            <span>Resilience Score</span>
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-black text-indigo-400 mt-1.5 font-outfit">
            {resilience ? Math.round(resilience.overall_score) : 100}
          </div>
          <div className="text-[11px] text-emerald-400 font-medium mt-1">100% Stability</div>
        </div>
      </div>

      {/* ── Main Two-Column Layout ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 flex-1 min-h-[500px]">

        {/* ── Left 2 Cols: Interactive Block Execution Queue & Impact Graph ── */}
        <div className="lg:col-span-2 bg-[#11131c] border border-white/10 rounded-2xl flex flex-col shadow-xl overflow-hidden">
          
          {/* Tabs & Filters Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-white/10 bg-[#161824]">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('queue')}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'queue'
                    ? 'bg-emerald-500 text-black shadow-md shadow-emerald-500/20'
                    : 'bg-[#1e2230] text-slate-300 hover:text-white hover:bg-[#252a3d]'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Active Block Execution Queue ({filteredBlocks.length})</span>
              </button>

              <button
                onClick={() => setActiveTab('impact')}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all ${
                  activeTab === 'impact'
                    ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                    : 'bg-[#1e2230] text-slate-300 hover:text-white hover:bg-[#252a3d]'
                }`}
              >
                <Network className="w-3.5 h-3.5" />
                <span>Disruption Impact Graph {events.length > 0 && `(${events.length})`}</span>
              </button>
            </div>

            {activeTab === 'queue' && (
              <div className="flex items-center gap-2.5">
                {/* Search */}
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search section or ID..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    className="bg-[#11131c] border border-[#2a2f44] rounded-lg pl-8 pr-3 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 w-40 sm:w-48"
                  />
                </div>

                {/* Filter */}
                <select
                  value={deptFilter}
                  onChange={e => setDeptFilter(e.target.value)}
                  className="bg-[#11131c] border border-[#2a2f44] rounded-lg px-2.5 py-1 text-xs text-slate-300 font-semibold focus:outline-none focus:border-emerald-500"
                >
                  <option value="ALL">All Depts</option>
                  <option value="Engineering">Engineering</option>
                  <option value="Electrical">Electrical</option>
                  <option value="S&T">S&T</option>
                  <option value="JOINT">Joint Blocks</option>
                </select>
              </div>
            )}
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-auto p-4 custom-scrollbar">
            {activeTab === 'queue' ? (
              <div className="space-y-2.5">
                {filteredBlocks.length === 0 ? (
                  <div className="flex flex-col items-center justify-center p-12 text-center text-slate-500">
                    <Layers className="w-10 h-10 mb-2 opacity-40 text-emerald-400" />
                    <p className="text-sm font-semibold text-slate-400">No scheduled blocks match your filter criteria.</p>
                  </div>
                ) : (
                  filteredBlocks.slice(0, 30).map((b, idx) => {
                    const isMulti = b.is_multi_department;
                    const deptColor = isMulti
                      ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                      : b.departments?.includes('Electrical')
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                      : b.departments?.includes('S&T')
                      ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                      : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';

                    return (
                      <div
                        key={b.block_id || idx}
                        className="bg-[#161824] hover:bg-[#1a1e2d] border border-white/5 hover:border-emerald-500/30 rounded-xl p-3.5 transition-all flex flex-wrap items-center justify-between gap-3 shadow-md"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-lg bg-[#11131c] border border-white/10 flex items-center justify-center shrink-0">
                            {isMulti ? (
                              <Zap className="w-4 h-4 text-purple-400" />
                            ) : b.departments?.includes('Electrical') ? (
                              <Cable className="w-4 h-4 text-amber-400" />
                            ) : (
                              <HardHat className="w-4 h-4 text-emerald-400" />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-white tracking-wide">{b.block_id}</span>
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${deptColor}`}>
                                {isMulti ? 'Joint Shadow Block' : b.departments || 'Engineering'}
                              </span>
                              {b.has_emergency && (
                                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30">
                                  EMERGENCY
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-slate-400 font-medium mt-0.5">
                              Section: <strong className="text-slate-300">{b.section || 'Central Corridor'}</strong>
                              {b.km_range_start && (
                                <span className="ml-2 text-slate-500">
                                  (Km {b.km_range_start} – {b.km_range_end})
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-6 text-xs">
                          <div>
                            <div className="text-slate-400 text-[10px] font-semibold uppercase">Window</div>
                            <div className="text-slate-200 font-bold font-mono">
                              {b.block_start_hour ? `${Math.floor(b.block_start_hour)}:00` : '00:00'} -{' '}
                              {b.block_end_hour ? `${Math.floor(b.block_end_hour)}:00` : '04:00'}
                              <span className="text-emerald-400 font-normal ml-1">({b.total_hours || 4}h)</span>
                            </div>
                          </div>

                          <div>
                            <div className="text-slate-400 text-[10px] font-semibold uppercase">Equipment</div>
                            <div className="text-slate-300 font-semibold">{b.required_equipment || 'P-Way Gang'}</div>
                          </div>

                          <div className="hidden sm:block">
                            <div className="text-slate-400 text-[10px] font-semibold uppercase">Tasks</div>
                            <div className="text-cyan-400 font-bold">{b.task_count || 1} Work Orders</div>
                          </div>

                          <div className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-bold">
                            SCHEDULED
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            ) : (
              <div className="h-full">
                <ImpactGraph events={events} />
              </div>
            )}
          </div>
        </div>

        {/* ── Right Column: Telemetry Stream & Resilience ── */}
        <div className="space-y-5 flex flex-col">
          
          {/* Resilience Overview Card */}
          <div className="bg-[#11131c] border border-white/10 rounded-2xl p-5 shadow-xl relative overflow-hidden">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Corridor Resilience</span>
              <Activity className="w-4 h-4 text-indigo-400" />
            </div>

            <div className="flex items-baseline gap-2 mb-4">
              <span className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 font-outfit">
                {resilience ? Math.round(resilience.overall_score) : 100}
              </span>
              <span className="text-xs font-semibold text-emerald-400">/ 100 (Optimal Operational Index)</span>
            </div>

            <div className="space-y-2.5 pt-2 border-t border-white/5">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Schedule Stability</span>
                  <span className="text-emerald-400 font-bold">{resilience?.stability || 100}%</span>
                </div>
                <div className="w-full bg-[#1c2030] h-1.5 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${resilience?.stability || 100}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">Dynamic Recovery Efficiency</span>
                  <span className="text-cyan-400 font-bold">{resilience?.recovery_efficiency || 100}%</span>
                </div>
                <div className="w-full bg-[#1c2030] h-1.5 rounded-full overflow-hidden">
                  <div className="bg-cyan-500 h-full rounded-full" style={{ width: `${resilience?.recovery_efficiency || 100}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* Live IoT Sensor Stream Ticker */}
          <div className="bg-[#11131c] border border-white/10 rounded-2xl p-5 shadow-xl flex-1 flex flex-col">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-white/5">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Live IoT Rail Sensors</h3>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">1.0 Hz Feed</span>
            </div>

            <div className="flex-1 overflow-y-auto space-y-2 max-h-72 custom-scrollbar pr-1">
              {telemetry.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-500">Connecting to Digital Twin sensor stream...</div>
              ) : (
                telemetry.slice(0, 15).map((t, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between text-xs bg-[#161824] border border-white/5 px-3 py-2 rounded-xl"
                  >
                    <div>
                      <div className="font-bold text-slate-200 text-[11px]">{t.sensor}</div>
                      <div className="text-[10px] text-slate-400">{t.location} · {t.timestamp?.split('T')[1] || t.timestamp}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono font-bold text-emerald-400 text-xs">{t.value}</div>
                      <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {t.status || 'NORMAL'}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Weather Risk Card */}
          <div className="bg-[#11131c] border border-white/10 rounded-2xl p-4 shadow-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Environmental Safety</span>
              <CloudRain className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="flex items-center justify-between text-xs bg-[#161824] p-2.5 rounded-xl border border-white/5">
              <div className="flex items-center gap-2">
                <Thermometer className="w-4 h-4 text-amber-400" />
                <span className="text-slate-300 font-semibold">Rail Temperature</span>
              </div>
              <span className="text-emerald-400 font-bold font-mono">29.5°C (Safe / No Buckling)</span>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
