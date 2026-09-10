import { useState, useRef } from 'react';
import axios from 'axios';
import { Zap, RefreshCw, CheckCircle, Radio, AlertOctagon, ChevronRight } from 'lucide-react';

const API = import.meta.env.MODE === 'development' ? 'http://localhost:8000/api' : '/api';

// Incident types — no emojis, muted accent colors
const INCIDENT_TYPES = [
  { id: 'Broken Rail',         label: 'Broken Rail',         dept: 'Engineering', accent: '#7c3f3f', active: 'bg-[#2a1515] border-[#5c2020] text-[#c97070]' },
  { id: 'OHE Wire Snap',       label: 'OHE Wire Snap',       dept: 'Electrical',  accent: '#7a6020', active: 'bg-[#221a0a] border-[#594510] text-[#b89040]' },
  { id: 'Signal Failure',      label: 'Signal Failure',      dept: 'S&T',         accent: '#5a5020', active: 'bg-[#1a180a] border-[#484010] text-[#9a9040]' },
  { id: 'Track Flooding',      label: 'Track Flooding',      dept: 'Engineering', accent: '#1e4060', active: 'bg-[#0a1520] border-[#163050] text-[#4a80a0]' },
  { id: 'Point Machine Fault', label: 'Point Machine Fault', dept: 'S&T',         accent: '#4a2a6a', active: 'bg-[#18102a] border-[#3a1e58] text-[#8060a8]' },
];

const SEVERITIES = [
  { id: 'low',    label: 'Minor',    activeClass: 'border-[#2a5040] text-[#5a9070] bg-[#0d1a14]', dot: 'bg-[#4a7060]' },
  { id: 'medium', label: 'Moderate', activeClass: 'border-[#5a4010] text-[#9a7030] bg-[#1a1408]', dot: 'bg-[#7a6020]' },
  { id: 'high',   label: 'Critical', activeClass: 'border-[#5a1a1a] text-[#a04040] bg-[#180a0a]', dot: 'bg-[#803030] animate-pulse' },
];

export default function IncidentSimulator({ onIncidentInjected }) {
  const [selectedType, setSelectedType] = useState('Broken Rail');
  const [severity, setSeverity] = useState('medium');
  const [kmMarker, setKmMarker] = useState(120);
  const [status, setStatus] = useState('idle');
  const [result, setResult] = useState(null);
  const [log, setLog] = useState([]);

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
    addLog(`Injecting: ${selectedType} at Km ${kmMarker} — ${severity} severity`, 'warn');

    try {
      const res = await axios.post(`${API}/inject-incident`, {
        incident_type: selectedType,
        km_marker: kmMarker,
        severity,
      });
      setStatus('success');
      setResult(res.data);
      addLog(`Re-optimized: ${res.data.stats?.blocks_scheduled} blocks scheduled`, 'success');
      addLog(`Integration rate: ${res.data.stats?.integration_rate_pct?.toFixed(1)}%`, 'info');
      if (onIncidentInjected) onIncidentInjected(res.data);
    } catch (err) {
      setStatus('error');
      const msg = err.response?.data?.detail || err.message;
      addLog(`Error: ${msg}`, 'error');
    } finally {
      setTimeout(() => setStatus('idle'), 4000);
    }
  };

  const incType = INCIDENT_TYPES.find(t => t.id === selectedType);
  const sevInfo = SEVERITIES.find(s => s.id === severity);

  return (
    <div className="space-y-5 font-inter">

      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-[#1a1010] border border-[#3a1e1e] rounded-xl">
          <AlertOctagon className="w-4 h-4 text-[#8a4040]" />
        </div>
        <div>
          <h3 className="text-[#c8c8cc] font-semibold text-sm tracking-tight">Incident Response Simulator</h3>
          <p className="text-[#555560] text-xs mt-0.5">Inject a live disruption — AI re-optimises the schedule in real time</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5 px-2.5 py-1 bg-[#1a1010] border border-[#3a1e1e] rounded-full">
          <span className="w-1.5 h-1.5 rounded-full bg-[#8a3535] animate-pulse"/>
          <span className="text-[10px] text-[#8a4040] font-semibold tracking-widest uppercase">Ops Mode</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">

        {/* Left — Incident Type */}
        <div>
          <label className="block text-[10px] font-semibold text-[#555560] uppercase tracking-widest mb-2.5">
            Incident Type
          </label>
          <div className="flex flex-col gap-1.5">
            {INCIDENT_TYPES.map(t => (
              <button
                key={t.id}
                onClick={() => setSelectedType(t.id)}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl border text-left transition-all ${
                  selectedType === t.id
                    ? t.active
                    : 'bg-[#0e0e10] border-[#1e1e22] text-[#555560] hover:border-[#2e2e35] hover:text-[#888890]'
                }`}
              >
                {/* Colored indicator bar instead of emoji */}
                <div
                  className="w-0.5 h-8 rounded-full shrink-0"
                  style={{ backgroundColor: selectedType === t.id ? t.accent : '#2a2a30' }}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold tracking-tight">{t.label}</div>
                  <div className="text-[10px] opacity-60 mt-0.5">{t.dept}</div>
                </div>
                {selectedType === t.id && (
                  <ChevronRight className="w-3.5 h-3.5 ml-auto opacity-50" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Right — Controls */}
        <div className="space-y-4">

          {/* Severity */}
          <div>
            <label className="block text-[10px] font-semibold text-[#555560] uppercase tracking-widest mb-2.5">
              Severity
            </label>
            <div className="flex gap-2">
              {SEVERITIES.map(s => (
                <button
                  key={s.id}
                  onClick={() => setSeverity(s.id)}
                  className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-semibold transition-all ${
                    severity === s.id
                      ? s.activeClass
                      : 'bg-[#0e0e10] border-[#1e1e22] text-[#444448] hover:border-[#2e2e35]'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${severity === s.id ? s.dot : 'bg-[#333338]'}`}/>
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Km Marker */}
          <div>
            <label className="block text-[10px] font-semibold text-[#555560] uppercase tracking-widest mb-2.5">
              Location — Km Marker:{' '}
              <span className="text-[#a0a0a8] font-bold">{kmMarker}</span>
            </label>
            <input
              type="range" min={0} max={256} step={1}
              value={kmMarker}
              onChange={e => setKmMarker(Number(e.target.value))}
              className="w-full cursor-pointer"
              style={{ accentColor: '#6a3535' }}
            />
            <div className="flex justify-between text-[10px] text-[#3a3a40] mt-1.5">
              <span>Km 0 — CSMT</span>
              <span>Km 128</span>
              <span>Km 256 — Manmad</span>
            </div>
          </div>

          {/* Preview panel */}
          <div className="bg-[#090909] border border-[#181820] rounded-xl p-3.5 space-y-2">
            <div className="text-[10px] text-[#404048] uppercase font-semibold tracking-widest mb-2.5">
              Incident Preview
            </div>
            {[
              { k: 'Type',         v: selectedType },
              { k: 'Location',     v: `Km ${kmMarker}` },
              { k: 'Dept Affected',v: incType?.dept },
              { k: 'Severity',     v: sevInfo?.label },
            ].map(row => (
              <div key={row.k} className="flex justify-between items-center text-xs">
                <span className="text-[#444450]">{row.k}</span>
                <span className="text-[#909098] font-medium">{row.v}</span>
              </div>
            ))}
          </div>

          {/* Inject Button */}
          <button
            onClick={injectIncident}
            disabled={status === 'loading'}
            className={`w-full flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all border tracking-tight ${
              status === 'loading'
                ? 'bg-[#111114] border-[#222228] text-[#444450] cursor-not-allowed'
                : status === 'success'
                ? 'bg-[#0f2018] border-[#1e4030] text-[#5a9070]'
                : 'bg-[#1a0e0e] border-[#3a1a1a] text-[#b05050] hover:bg-[#221010] hover:border-[#4a2020]'
            }`}
          >
            {status === 'loading' ? (
              <><RefreshCw className="w-4 h-4 animate-spin opacity-60" />Re-Optimising Schedule...</>
            ) : status === 'success' ? (
              <><CheckCircle className="w-4 h-4" />Schedule Updated</>
            ) : (
              <><Zap className="w-4 h-4" />Inject Incident</>
            )}
          </button>

          {/* Result stats */}
          {result?.stats && (
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: 'Blocks Scheduled', value: result.stats.blocks_scheduled },
                { label: 'Integration Rate', value: `${result.stats.integration_rate_pct?.toFixed(1)}%` },
                { label: 'Schedule Rate',    value: `${result.stats.schedule_rate_pct?.toFixed(0)}%` },
                { label: 'Asset Avail.',     value: `${result.stats.asset_availability_pct?.toFixed(1)}%` },
              ].map(m => (
                <div key={m.label} className="bg-[#0a1210] border border-[#182820] rounded-xl p-2.5 text-center">
                  <div className="text-[#5a8a70] font-semibold text-sm">{m.value}</div>
                  <div className="text-[#3a4840] text-[10px] mt-0.5">{m.label}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Activity Log */}
      {log.length > 0 && (
        <div className="bg-[#070709] border border-[#141418] rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-2.5">
            <Radio className="w-3 h-3 text-[#3a6050] animate-pulse"/>
            <span className="text-[10px] font-semibold text-[#404048] uppercase tracking-widest">System Log</span>
          </div>
          <div className="space-y-1.5 max-h-32 overflow-y-auto custom-scrollbar">
            {log.map((entry, i) => (
              <div key={i} className="flex items-start gap-2.5 text-[11px]">
                <span className="text-[#303038] font-mono shrink-0">{entry.time}</span>
                <span className={
                  entry.type === 'success' ? 'text-[#4a7a60]' :
                  entry.type === 'error'   ? 'text-[#8a4040]' :
                  entry.type === 'warn'    ? 'text-[#7a6030]' : 'text-[#505058]'
                }>{entry.msg}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
