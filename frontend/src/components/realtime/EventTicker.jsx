import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { AlertTriangle, Clock, Zap } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) { return twMerge(clsx(inputs)); }

const API = import.meta.env.VITE_API_URL || (import.meta.env.MODE === 'development' ? 'http://127.0.0.1:8000/api' : '/api');

export default function EventTicker() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const res = await axios.get(`${API}/realtime/events`);
        setEvents(res.data.events);
      } catch (err) {
        console.error(err);
      }
    };
    
    fetchEvents();
    // Poll every 5 seconds since this is a prototype
    const interval = setInterval(fetchEvents, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full bg-[#0a0a0f] border-t border-b border-[#222] py-2 px-4 flex items-center overflow-hidden h-12 shrink-0">
      <div className="flex items-center gap-2 pr-4 border-r border-[#333] shrink-0">
        <Zap className="w-4 h-4 text-emerald-400 animate-pulse" />
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Live Feed</span>
      </div>
      
      <div className="flex-1 overflow-hidden relative ml-4">
        {events.length === 0 ? (
          <div className="text-sm text-slate-500 italic">Listening for real-time events...</div>
        ) : (
          <div className="flex animate-marquee whitespace-nowrap gap-8">
            {events.map((e, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <span className="text-xs font-mono text-slate-500">{e.timestamp.split('T')[1]}</span>
                <span className={cn(
                  "text-[10px] font-bold px-1.5 py-0.5 rounded-sm uppercase",
                  e.severity === 'CRITICAL' ? "bg-red-500/20 text-red-400" :
                  e.severity === 'HIGH' ? "bg-orange-500/20 text-orange-400" :
                  e.severity === 'MEDIUM' ? "bg-yellow-500/20 text-yellow-400" :
                  "bg-slate-500/20 text-slate-400"
                )}>
                  {e.severity}
                </span>
                <span className="text-sm font-medium text-slate-200">
                  <span className="text-emerald-400 font-bold">[{e.source}]</span> {e.description}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
