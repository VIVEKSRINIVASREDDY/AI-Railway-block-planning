import { useState, useEffect } from 'react';
import axios from 'axios';
import { Truck, AlertTriangle, CheckCircle, MapPin, Clock, Wrench, RefreshCw } from 'lucide-react';

const API = import.meta.env.MODE === 'development' ? 'http://localhost:8000/api' : '/api';

const DEPT_STYLES = {
  Engineering: { bg: 'bg-blue-500/10',   border: 'border-blue-500/30',   text: 'text-blue-400',   dot: 'bg-blue-500' },
  Electrical:  { bg: 'bg-violet-500/10', border: 'border-violet-500/30', text: 'text-violet-400', dot: 'bg-violet-500' },
  'S&T':       { bg: 'bg-emerald-500/10',border: 'border-emerald-500/30',text: 'text-emerald-400',dot: 'bg-emerald-500' },
};

const STATUS_STYLES = {
  deployed: { label: 'Deployed',  color: 'text-emerald-400', badge: 'bg-emerald-500/10 border-emerald-500/30', dot: 'bg-emerald-500 animate-pulse' },
  idle:     { label: 'Available', color: 'text-slate-400',   badge: 'bg-slate-500/10 border-slate-500/30',    dot: 'bg-slate-500' },
};

export default function FleetManager() {
  const [fleet, setFleet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  const fetchFleet = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/fleet`);
      setFleet(res.data);
    } catch (err) {
      setFleet(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchFleet(); }, []);

  const machines = fleet?.machines || [];
  const conflicts = fleet?.conflicts || [];

  const filtered = filter === 'all' ? machines :
    filter === 'deployed' ? machines.filter(m => m.status === 'deployed') :
    filter === 'idle' ? machines.filter(m => m.status === 'idle') :
    machines.filter(m => m.dept === filter);

  const depts = ['all', 'deployed', 'idle', 'Engineering', 'Electrical', 'S&T'];

  const fmtH = h => `${String(Math.floor(h)).padStart(2,'0')}:${String(Math.round((h - Math.floor(h)) * 60)).padStart(2,'0')}`;

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="p-2 bg-amber-500/10 border border-amber-500/20 rounded-xl">
          <Truck className="w-5 h-5 text-amber-400"/>
        </div>
        <div>
          <h3 className="text-white font-bold text-sm">Machinery Fleet Allocation</h3>
          <p className="text-slate-500 text-xs">Track-level machinery deployment & conflict detection</p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-slate-500">{machines.filter(m => m.status === 'deployed').length}/{machines.length} deployed</span>
          <button onClick={fetchFleet} className="p-1.5 text-slate-500 hover:text-white hover:bg-white/5 rounded-lg transition-all">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`}/>
          </button>
        </div>
      </div>

      {/* Conflict Alerts */}
      {conflicts.length > 0 && (
        <div className="space-y-2">
          {conflicts.map((c, i) => (
            <div key={i} className="flex items-start gap-3 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5"/>
              <div>
                <div className="text-red-400 font-semibold text-xs mb-0.5">⚠️ Fleet Conflict Detected</div>
                <div className="text-slate-300 text-xs">{c.message}</div>
                <div className="text-slate-500 text-[10px] mt-1">Blocks: {c.block_a} ↔ {c.block_b} · Distance: {c.km_diff} km</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {conflicts.length === 0 && fleet && (
        <div className="flex items-center gap-2 bg-emerald-500/5 border border-emerald-500/20 rounded-xl px-4 py-2.5">
          <CheckCircle className="w-4 h-4 text-emerald-400"/>
          <span className="text-emerald-400 text-xs font-semibold">No fleet conflicts detected</span>
          <span className="text-slate-500 text-xs ml-auto">All machinery optimally assigned</span>
        </div>
      )}

      {/* Filter bar */}
      <div className="flex gap-2 flex-wrap">
        {depts.map(d => (
          <button
            key={d}
            onClick={() => setFilter(d)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
              filter === d
                ? 'bg-white/10 border-white/20 text-white'
                : 'bg-transparent border-[#222] text-slate-500 hover:border-[#333] hover:text-slate-300'
            }`}
          >
            {d === 'all' ? `All (${machines.length})` :
             d === 'deployed' ? `Deployed (${machines.filter(m=>m.status==='deployed').length})` :
             d === 'idle' ? `Available (${machines.filter(m=>m.status==='idle').length})` : d}
          </button>
        ))}
      </div>

      {/* Machine Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-[#111] border border-[#1a1a1a] rounded-2xl p-4 animate-pulse h-28"/>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {filtered.map(m => {
            const dStyle = DEPT_STYLES[m.dept] || DEPT_STYLES.Engineering;
            const sStyle = STATUS_STYLES[m.status] || STATUS_STYLES.idle;
            const hasConflict = conflicts.some(c => c.machine_a === m.name || c.machine_b === m.name);

            return (
              <div
                key={m.id}
                className={`relative bg-[#0d0d0d] border rounded-2xl p-4 transition-all hover:border-[#333] group ${
                  hasConflict ? 'border-red-500/40 shadow-[0_0_15px_rgba(239,68,68,0.1)]' : 'border-[#1a1a1a]'
                }`}
              >
                {hasConflict && (
                  <div className="absolute top-3 right-3">
                    <AlertTriangle className="w-3.5 h-3.5 text-red-400 animate-pulse"/>
                  </div>
                )}

                <div className="flex items-start gap-3 mb-3">
                  <div className={`text-2xl w-10 h-10 rounded-xl ${dStyle.bg} border ${dStyle.border} flex items-center justify-center shrink-0`}>
                    {m.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-white font-bold text-sm truncate">{m.name}</div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className={`text-[10px] font-semibold ${dStyle.text}`}>{m.dept}</span>
                      <span className="text-slate-700">·</span>
                      <span className="text-[10px] text-slate-600 font-mono">{m.id}</span>
                    </div>
                  </div>
                  <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full border text-[10px] font-semibold ${sStyle.badge}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${sStyle.dot}`}/>
                    {sStyle.label}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-[#111] rounded-lg p-2 text-center">
                    <MapPin className="w-3 h-3 text-slate-600 mx-auto mb-1"/>
                    <div className="text-[11px] font-bold text-slate-300">Km {m.location_km}</div>
                    <div className="text-[9px] text-slate-600">Location</div>
                  </div>
                  <div className="bg-[#111] rounded-lg p-2 text-center">
                    <Clock className="w-3 h-3 text-slate-600 mx-auto mb-1"/>
                    <div className="text-[11px] font-bold text-slate-300">{m.available_from}</div>
                    <div className="text-[9px] text-slate-600">Avail. from</div>
                  </div>
                  <div className="bg-[#111] rounded-lg p-2 text-center">
                    <Wrench className="w-3 h-3 text-slate-600 mx-auto mb-1"/>
                    <div className="text-[11px] font-bold text-slate-300 truncate">
                      {m.assigned_block ? m.assigned_block.block_id?.substring(0,8) + '…' : '—'}
                    </div>
                    <div className="text-[9px] text-slate-600">Block</div>
                  </div>
                </div>

                {m.assigned_block && (
                  <div className="mt-2 bg-[#0a0a0a] border border-[#1a1a1a] rounded-lg px-3 py-1.5 flex items-center justify-between">
                    <span className="text-[10px] text-slate-600">Deployed:</span>
                    <span className="text-[10px] text-slate-400">
                      {m.assigned_block.section?.substring(0,20)} · {m.assigned_block.day}
                      {m.assigned_block.start_hour != null && ` · ${fmtH(m.assigned_block.start_hour)}–${fmtH(m.assigned_block.end_hour)}`}
                    </span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="text-center py-10 text-slate-600 text-sm">No machines match the selected filter.</div>
      )}
    </div>
  );
}
