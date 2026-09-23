import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Network, Train, Layers, Hammer, Users, ArrowDown, ChevronRight, Zap } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) { return twMerge(clsx(inputs)); }

const API = import.meta.env.MODE === 'development' ? 'http://localhost:8000/api' : '/api';

export default function ImpactGraph({ events }) {
  const [impactData, setImpactData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedEventId, setSelectedEventId] = useState(null);

  // If there are events, auto-select the latest critical event
  useEffect(() => {
    if (events && events.length > 0 && !selectedEventId) {
      const criticalEvent = events.find(e => ['CRITICAL', 'HIGH'].includes(e.severity)) || events[0];
      setSelectedEventId(criticalEvent.event_id);
    }
  }, [events]);

  useEffect(() => {
    if (selectedEventId) {
      const fetchImpact = async () => {
        try {
          setLoading(true);
          const res = await axios.get(`${API}/analytics/impact/${selectedEventId}`);
          setImpactData(res.data);
        } catch (err) {
          console.error(err);
        } finally {
          setLoading(false);
        }
      };
      fetchImpact();
    }
  }, [selectedEventId]);

  if (!events || events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-slate-500">
        <Network className="w-12 h-12 mb-4 opacity-50" />
        <h3 className="text-lg font-bold">No Active Disruptions</h3>
        <p className="text-sm">The railway is operating normally. Inject an incident to see impact analytics.</p>
      </div>
    );
  }

  // Node type icons
  const icons = {
    event: Zap,
    train: Train,
    section: Network,
    block: Layers,
    task: Hammer,
    crew: Users,
  };
  
  const colors = {
    event: "text-rose-400 bg-rose-500/10 border-rose-500/30",
    train: "text-amber-400 bg-amber-500/10 border-amber-500/30",
    section: "text-sky-400 bg-sky-500/10 border-sky-500/30",
    block: "text-purple-400 bg-purple-500/10 border-purple-500/30",
    task: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    crew: "text-indigo-400 bg-indigo-500/10 border-indigo-500/30",
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0a0f] border border-[#222] rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#222] bg-[#111]">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-purple-400" />
          <h2 className="text-sm font-bold text-slate-200">Cascading Impact Analysis</h2>
        </div>
        
        <select 
          className="bg-black border border-[#333] rounded px-2 py-1 text-xs focus:border-purple-500 outline-none"
          value={selectedEventId || ''}
          onChange={e => setSelectedEventId(e.target.value)}
        >
          {events.map(e => (
            <option key={e.event_id} value={e.event_id}>
              {e.event_type} - {e.timestamp.split('T')[1]}
            </option>
          ))}
        </select>
      </div>

      {/* Main Area */}
      <div className="flex-1 overflow-auto p-6 flex flex-col items-center">
        {loading ? (
          <div className="animate-pulse flex flex-col gap-4 items-center mt-12">
            <div className="w-32 h-10 bg-[#222] rounded-lg"></div>
            <div className="w-px h-8 bg-[#333]"></div>
            <div className="w-48 h-10 bg-[#222] rounded-lg"></div>
          </div>
        ) : impactData ? (
          <div className="w-full max-w-2xl mx-auto flex flex-col items-center gap-2 relative">
            
            <div className="mb-6 text-center text-sm font-semibold text-rose-400 bg-rose-500/10 px-4 py-2 rounded-lg border border-rose-500/20">
              {impactData.summary}
            </div>

            {/* Render nodes hierarchically */}
            {['event', 'train', 'section', 'block', 'task', 'crew'].map(level => {
              const levelNodes = impactData.nodes.filter(n => n.type === level);
              if (levelNodes.length === 0) return null;
              
              return (
                <div key={level} className="flex flex-col items-center w-full">
                  <div className="flex justify-center gap-6 w-full flex-wrap">
                    {levelNodes.map(node => {
                      const Icon = icons[node.type] || Network;
                      return (
                        <div key={node.id} className={cn(
                          "flex items-center gap-3 px-4 py-3 rounded-xl border animate-fade-in-up min-w-[200px] shadow-lg",
                          colors[node.type]
                        )}>
                          <Icon className="w-5 h-5 shrink-0" />
                          <div className="flex flex-col">
                            <span className="text-[10px] font-bold uppercase opacity-70">{node.type}</span>
                            <span className="text-sm font-semibold">{node.label}</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                  
                  {/* Arrow to next level if there are more nodes below */}
                  {level !== 'crew' && (
                    <div className="h-8 w-px bg-gradient-to-b from-slate-500 to-transparent my-2"></div>
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          <div className="text-slate-500">Select an event to view its impact.</div>
        )}
      </div>
    </div>
  );
}
