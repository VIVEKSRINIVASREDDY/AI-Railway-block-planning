import { useState } from 'react';
import { Activity, ShieldAlert, Cpu, Settings2, FileSpreadsheet, DownloadCloud } from 'lucide-react';
import LiveRadarMap from './LiveRadarMap';

export default function BetaDashboard() {
  const [activeTab, setActiveTab] = useState('radar');

  return (
    <div className="w-full h-full flex flex-col bg-[#0b0f19] text-slate-300">
      
      {/* Beta Header */}
      <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 bg-[#111827]">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-500/20 text-indigo-400 px-2 py-1 rounded text-xs font-bold uppercase tracking-wider border border-indigo-500/30">
            BETA PREVIEW
          </div>
          <h1 className="text-white font-semibold tracking-wide">Professional Production Features</h1>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <button 
            onClick={() => setActiveTab('radar')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors ${activeTab === 'radar' ? 'bg-white/10 text-white' : 'hover:bg-white/5'}`}
          >
            <Activity className="w-4 h-4" /> Live Train Radar
          </button>
          <button 
            onClick={() => setActiveTab('export')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors ${activeTab === 'export' ? 'bg-white/10 text-white' : 'hover:bg-white/5'}`}
          >
            <FileSpreadsheet className="w-4 h-4" /> Reports & Exporters
          </button>
          <button 
            onClick={() => setActiveTab('settings')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors ${activeTab === 'settings' ? 'bg-white/10 text-white' : 'hover:bg-white/5'}`}
          >
            <Settings2 className="w-4 h-4" /> Optimization Sliders
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-4 relative overflow-hidden">
        
        {activeTab === 'radar' && (
          <div className="w-full h-full flex flex-col">
            <div className="mb-4 text-sm text-slate-400">
              <strong className="text-white">Real-Time Radar:</strong> Simulating live train tracking using RTIS/NTES style data with AI block conflict warnings.
            </div>
            <div className="flex-1 rounded-2xl overflow-hidden border border-white/10">
              <LiveRadarMap />
            </div>
          </div>
        )}

        {activeTab === 'export' && (
          <div className="w-full max-w-4xl mx-auto py-12">
            <h2 className="text-2xl font-bold text-white mb-6">Professional Exporters (BETA)</h2>
            <div className="grid grid-cols-2 gap-6">
              
              <div className="bg-[#111] border border-white/5 rounded-2xl p-6 hover:border-emerald-500/50 transition-colors">
                <div className="w-12 h-12 bg-emerald-500/10 rounded-xl flex items-center justify-center mb-4">
                  <FileSpreadsheet className="w-6 h-6 text-emerald-400" />
                </div>
                <h3 className="text-lg font-bold text-white mb-2">Multi-Tab Excel (.xlsx)</h3>
                <p className="text-slate-400 text-sm mb-4">
                  Export the complete schedule with formatted tabs for Engineering, S&T, and Electrical departments.
                </p>
                <button className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-semibold flex items-center gap-2">
                  <DownloadCloud className="w-4 h-4" /> Download Schedule (.xlsx)
                </button>
              </div>

              <div className="bg-[#111] border border-white/5 rounded-2xl p-6 hover:border-indigo-500/50 transition-colors">
                <div className="w-12 h-12 bg-indigo-500/10 rounded-xl flex items-center justify-center mb-4">
                  <Cpu className="w-6 h-6 text-indigo-400" />
                </div>
                <h3 className="text-lg font-bold text-white mb-2">Custom CSV Upload</h3>
                <p className="text-slate-400 text-sm mb-4">
                  Drag and drop your own railway division's TMS/COA spreadsheets to run the optimization pipeline.
                </p>
                <button className="bg-[#222] border border-[#333] hover:border-indigo-500 text-white px-4 py-2 rounded-lg text-sm font-semibold">
                  Upload Datasets
                </button>
              </div>

            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="w-full max-w-4xl mx-auto py-12">
            <h2 className="text-2xl font-bold text-white mb-6">Multi-Objective Pareto Trade-Offs</h2>
            <div className="bg-[#111] border border-white/5 rounded-2xl p-8">
              <div className="mb-8">
                <div className="flex justify-between text-sm font-bold text-white mb-4">
                  <span>Punctuality Focus (Minimize Train Delay)</span>
                  <span className="text-indigo-400">Balanced (50/50)</span>
                  <span>Safety Focus (Clear Maintenance Backlog)</span>
                </div>
                <input type="range" min="0" max="100" defaultValue="50" className="w-full h-2 bg-[#333] rounded-lg appearance-none cursor-pointer accent-indigo-500" />
              </div>
              <p className="text-slate-400 text-sm">
                * Adjusting this slider will instruct the OR-Tools CP-SAT solver to re-weight its objective function in real time. (BETA preview UI only).
              </p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
