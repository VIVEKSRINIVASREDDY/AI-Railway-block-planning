import { useState } from 'react';
import axios from 'axios';
import { Zap, RefreshCw, CheckCircle, Radio, AlertOctagon, ChevronRight, HardHat, Cable, ShieldAlert, Waves, Wrench } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || (import.meta.env.MODE === 'development' ? 'http://127.0.0.1:8000/api' : '/api');

// Incident types with vivid distinct colors, badges, and icons
const INCIDENT_TYPES = [
  {
    id: 'Broken Rail',
    label: 'Broken Rail',
    dept: 'Engineering',
    icon: HardHat,
    accent: '#ef4444',
    badgeClass: 'bg-red-500/20 text-red-400 border-red-500/30',
    activeClass: 'bg-red-950/40 border-red-500 text-white shadow-[0_0_20px_rgba(239,68,68,0.25)] ring-1 ring-red-500/50'
  },
  {
    id: 'OHE Wire Snap',
    label: 'OHE Wire Snap',
    dept: 'Electrical',
    icon: Cable,
    accent: '#f59e0b',
    badgeClass: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    activeClass: 'bg-amber-950/40 border-amber-500 text-white shadow-[0_0_20px_rgba(245,158,11,0.25)] ring-1 ring-amber-500/50'
  },
  {
    id: 'Signal Failure',
    label: 'Signal Failure',
    dept: 'S&T',
    icon: ShieldAlert,
    accent: '#eab308',
    badgeClass: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    activeClass: 'bg-yellow-950/40 border-yellow-500 text-white shadow-[0_0_20px_rgba(234,179,8,0.25)] ring-1 ring-yellow-500/50'
  },
  {
    id: 'Track Flooding',
    label: 'Track Flooding',
    dept: 'Engineering',
    icon: Waves,
    accent: '#06b6d4',
    badgeClass: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    activeClass: 'bg-cyan-950/40 border-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.25)] ring-1 ring-cyan-500/50'
  },
  {
    id: 'Point Machine Fault',
    label: 'Point Machine Fault',
    dept: 'S&T',
    icon: Wrench,
    accent: '#a855f7',
    badgeClass: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    activeClass: 'bg-purple-950/40 border-purple-500 text-white shadow-[0_0_20px_rgba(168,85,247,0.25)] ring-1 ring-purple-500/50'
  },
];

const SEVERITIES = [
  { id: 'low',    label: 'Minor',    activeClass: 'border-emerald-500 text-emerald-300 bg-emerald-950/50 shadow-md shadow-emerald-500/20 ring-1 ring-emerald-500/50', dot: 'bg-emerald-400' },
  { id: 'medium', label: 'Moderate', activeClass: 'border-amber-500 text-amber-300 bg-amber-950/50 shadow-md shadow-amber-500/20 ring-1 ring-amber-500/50', dot: 'bg-amber-400' },
  { id: 'high',   label: 'Critical', activeClass: 'border-rose-500 text-rose-300 bg-rose-950/50 shadow-md shadow-rose-500/30 ring-1 ring-rose-500/60 animate-pulse', dot: 'bg-rose-400' },
];

const PRESETS = [
  { id: 'monsoon', label: 'Monsoon Flash Flood (Kalyan)', type: 'Track Flooding', km: 54, sev: 'high', line: 'DN SLOW' },
  { id: 'buckling', label: 'Heat Buckling Risk (Thal Ghat)', type: 'Broken Rail', km: 125, sev: 'high', line: 'UP FAST' },
  { id: 'fracture', label: 'Peak Hour Rail Fracture (Thane)', type: 'Broken Rail', km: 34, sev: 'high', line: 'UP FAST' },
];

export default function IncidentSimulator({ onIncidentInjected }) {
  const [selectedType, setSelectedType] = useState('Broken Rail');
  const [severity, setSeverity] = useState('medium');
  const [kmMarker, setKmMarker] = useState(120);
  const [lineTrack, setLineTrack] = useState('UP FAST');
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [log, setLog] = useState([]);
  const [isSandboxMode, setIsSandboxMode] = useState(true);
  const [showApplyConfirm, setShowApplyConfirm] = useState(false);

  const applyPreset = (p) => {
    setSelectedType(p.type);
    setKmMarker(p.km);
    setSeverity(p.sev);
    setLineTrack(p.line);
    addLog(`Applied Preset: ${p.label}`, 'info');
  };

  const addLog = (msg, type = 'info') => {
    setLog(prev => [{
      time: new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      msg,
      type
    }, ...prev].slice(0, 20));
  };

  const injectIncident = async () => {
    if (status === 'loading') return;
    setStatus('loading');
    setResult(null);
    addLog(`Injecting: ${selectedType} at Km ${kmMarker} — ${severity.toUpperCase()} severity`, 'warn');

    try {
      const res = await axios.post(`${API}/inject-incident`, {
        incident_type: selectedType,
        km_marker: kmMarker,
        severity,
      });
      setStatus('success');
      setResult(res.data);
      addLog(`Re-optimized & Saved: ${res.data.stats?.blocks_scheduled} blocks scheduled to database`, 'success');
      addLog(`Integration rate: ${res.data.stats?.integration_rate_pct?.toFixed(1)}%`, 'info');
      if (onIncidentInjected) onIncidentInjected(res.data);
    } catch (err) {
      setStatus('error');
      const msg = err.response?.data?.detail || err.message;
      addLog(`Error: ${msg}`, 'error');
    } finally {
      setTimeout(() => setStatus('idle'), 5000);
    }
  };

  const incType = INCIDENT_TYPES.find(t => t.id === selectedType);
  const sevInfo = SEVERITIES.find(s => s.id === severity);

  return (
    <div className="space-y-6 font-inter text-slate-200">

      {/* Header with High Visibility */}
      <div className="flex items-center justify-between p-4 bg-[#11131c] border border-white/10 rounded-2xl shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-red-500/20 border border-red-500/40 rounded-xl shadow-md shadow-red-500/10">
            <AlertOctagon className="w-5 h-5 text-red-400" />
          </div>
          <div>
            <h3 className="text-white font-bold text-base tracking-wide flex items-center gap-2">
              Incident Response Simulator
              <span className="text-xs font-normal text-emerald-400 bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                AI Auto-Replanning Active
              </span>
            </h3>
            <p className="text-slate-400 text-xs mt-0.5">Inject an unexpected line disruption into a sandbox simulation or live plan.</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsSandboxMode(!isSandboxMode)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-bold transition-all ${
              isSandboxMode
                ? 'bg-indigo-950/60 border-indigo-500/50 text-indigo-300'
                : 'bg-red-950/60 border-red-500/50 text-red-300'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${isSandboxMode ? 'bg-indigo-400' : 'bg-red-500 animate-ping'}`}/>
            <span>{isSandboxMode ? 'SANDBOX MODE' : 'LIVE OPS MODE'}</span>
          </button>
        </div>
      </div>

      {/* Scenario Presets Strip */}
      <div className="p-3 bg-[#11131c] border border-white/10 rounded-xl flex items-center gap-3 overflow-x-auto">
        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider shrink-0">Scenario Presets:</span>
        {PRESETS.map(p => (
          <button
            key={p.id}
            onClick={() => applyPreset(p)}
            className="px-3 py-1.5 rounded-lg bg-[#181a26] hover:bg-[#202434] border border-[#2a2e44] text-xs font-semibold text-slate-200 shrink-0 transition-colors"
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Left — Incident Type Selection */}
        <div className="bg-[#11131c] border border-white/10 rounded-2xl p-5 shadow-xl">
          <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
            Select Incident Type
          </label>
          <div className="flex flex-col gap-2.5">
            {INCIDENT_TYPES.map(t => {
              const IconComp = t.icon;
              const isSelected = selectedType === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setSelectedType(t.id)}
                  className={`flex items-center gap-3.5 px-4 py-3 rounded-xl border text-left transition-all duration-200 ${
                    isSelected
                      ? t.activeClass
                      : 'bg-[#161824] border-[#262a3d] text-slate-300 hover:border-slate-500 hover:bg-[#1c2030]'
                  }`}
                >
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 border"
                    style={{
                      backgroundColor: `${t.accent}20`,
                      borderColor: `${t.accent}50`,
                      color: t.accent
                    }}
                  >
                    <IconComp className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold tracking-tight text-white">{t.label}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border ${t.badgeClass}`}>
                        {t.dept}
                      </span>
                    </div>
                  </div>
                  {isSelected && (
                    <ChevronRight className="w-5 h-5 text-white shrink-0 animate-pulse" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Right — Controls & Parameters */}
        <div className="space-y-5">

          {/* Severity & Location Box */}
          <div className="bg-[#11131c] border border-white/10 rounded-2xl p-5 shadow-xl space-y-5">
            
            {/* Severity */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5">
                Disruption Severity
              </label>
              <div className="flex gap-2.5">
                {SEVERITIES.map(s => (
                  <button
                    key={s.id}
                    onClick={() => setSeverity(s.id)}
                    className={`flex-1 flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl border text-xs font-bold transition-all duration-150 ${
                      severity === s.id
                        ? s.activeClass
                        : 'bg-[#161824] border-[#262a3d] text-slate-400 hover:text-slate-200 hover:border-slate-600'
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full ${severity === s.id ? s.dot : 'bg-slate-600'}`}/>
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Line Selection */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5">
                Corridor Line / Track
              </label>
              <div className="grid grid-cols-2 gap-2">
                {['UP FAST', 'DN FAST', 'UP SLOW', 'DN SLOW'].map(line => (
                  <button
                    key={line}
                    onClick={() => setLineTrack(line)}
                    className={`px-3 py-2 rounded-xl border text-xs font-bold transition-all ${
                      lineTrack === line
                        ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                        : 'bg-[#161824] border-[#262a3d] text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {line}
                  </button>
                ))}
              </div>
            </div>

            {/* Km Marker */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Location on Corridor
                </label>
                <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30">
                  Km {kmMarker}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={256}
                step={1}
                value={kmMarker}
                onChange={e => setKmMarker(Number(e.target.value))}
                className="w-full h-2.5 bg-[#202434] rounded-lg appearance-none cursor-pointer accent-red-500"
              />
              <div className="flex justify-between text-xs font-semibold text-slate-400 mt-2">
                <span>Km 0 (CSMT)</span>
                <span>Km 54 (Kalyan)</span>
                <span>Km 137 (Igatpuri)</span>
                <span>Km 256 (Manmad)</span>
              </div>
            </div>

            {/* Incident Summary Card */}
            <div className="bg-[#161824] border border-[#2a2f44] rounded-xl p-4 space-y-2.5">
              <div className="text-xs text-slate-400 uppercase font-bold tracking-wider mb-2 flex items-center justify-between">
                <span>Incident Preview</span>
                <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">Ready to Inject</span>
              </div>
              {[
                { k: 'Disruption Type', v: selectedType },
                { k: 'Track / Line', v: lineTrack },
                { k: 'Corridor Marker', v: `Km ${kmMarker} (Central Railway)` },
                { k: 'Department Assigned', v: incType?.dept },
                { k: 'Safety Severity', v: sevInfo?.label },
                { k: 'Simulation Target', v: isSandboxMode ? 'Isolated Sandbox Copy' : 'Active Operational Plan' },
              ].map(row => (
                <div key={row.k} className="flex justify-between items-center text-xs py-0.5 border-b border-white/5 last:border-0">
                  <span className="text-slate-400 font-medium">{row.k}</span>
                  <span className="text-white font-bold">{row.v}</span>
                </div>
              ))}
            </div>

            {/* Inject Button */}
            <button
              onClick={injectIncident}
              disabled={status === 'loading'}
              className={`w-full flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl font-bold text-sm tracking-wide transition-all shadow-xl ${
                status === 'loading'
                  ? 'bg-slate-800 border border-slate-700 text-slate-400 cursor-not-allowed'
                  : status === 'success'
                  ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white border border-emerald-400/40 shadow-emerald-600/30'
                  : 'bg-gradient-to-r from-red-600 via-rose-600 to-red-700 hover:from-red-500 hover:to-rose-500 text-white border border-red-400/30 shadow-red-600/30 hover:shadow-red-600/50'
              }`}
            >
              {status === 'loading' ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin text-white" />
                  <span>Re-optimizing & Saving Schedule...</span>
                </>
              ) : status === 'success' ? (
                <>
                  <CheckCircle className="w-5 h-5 text-emerald-300" />
                  <span>Schedule Re-optimized & Saved to Database!</span>
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5 text-yellow-300 fill-yellow-300" />
                  <span>Inject Incident & Re-plan Corridor</span>
                </>
              )}
            </button>

          </div>

          {/* Success Result Stats Panel */}
          {result?.stats && (
            <div className="bg-[#11131c] border border-emerald-500/40 rounded-2xl p-4 shadow-xl animate-fade-in-up">
              <div className="flex items-center gap-2 mb-3 text-emerald-400 font-bold text-xs">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span>Re-planning Results (Saved Permanently to Database)</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {[
                  { label: 'Blocks Scheduled', value: result.stats.blocks_scheduled, color: 'text-emerald-400' },
                  { label: 'Integration Rate', value: `${result.stats.integration_rate_pct?.toFixed(1)}%`, color: 'text-cyan-400' },
                  { label: 'Schedule Rate',    value: `${result.stats.schedule_rate_pct?.toFixed(0)}%`, color: 'text-purple-400' },
                  { label: 'Asset Avail.',     value: `${result.stats.asset_availability_pct?.toFixed(1)}%`, color: 'text-amber-400' },
                ].map(m => (
                  <div key={m.label} className="bg-[#161824] border border-white/5 rounded-xl p-3 text-center">
                    <div className={`text-base font-extrabold ${m.color}`}>{m.value}</div>
                    <div className="text-slate-400 text-[11px] font-medium mt-0.5">{m.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>

      {/* Activity Log with Crisp Readability */}
      {log.length > 0 && (
        <div className="bg-[#11131c] border border-white/10 rounded-2xl p-4 shadow-xl">
          <div className="flex items-center gap-2 mb-3">
            <Radio className="w-4 h-4 text-emerald-400 animate-pulse"/>
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">Live System Event Log</span>
          </div>
          <div className="space-y-2 max-h-36 overflow-y-auto custom-scrollbar pr-1">
            {log.map((entry, i) => (
              <div key={i} className="flex items-start gap-3 text-xs bg-[#161824] border border-white/5 px-3 py-2 rounded-lg">
                <span className="text-slate-400 font-mono text-[11px] shrink-0">{entry.time}</span>
                <span className={`font-medium ${
                  entry.type === 'success' ? 'text-emerald-400 font-bold' :
                  entry.type === 'error'   ? 'text-rose-400 font-bold' :
                  entry.type === 'warn'    ? 'text-amber-400 font-semibold' : 'text-slate-300'
                }`}>
                  {entry.msg}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
