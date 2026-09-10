import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { Map, AlertTriangle, Activity, ZoomIn, ZoomOut, Layers } from 'lucide-react';

const API = import.meta.env.MODE === 'development' ? 'http://localhost:8000/api' : '/api';

const CRITICALITY_COLORS = {
  good:     { track: '#10b981', station: '#10b981', glow: 'rgba(16,185,129,0.6)',  label: 'Normal',   badge: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' },
  watch:    { track: '#f59e0b', station: '#f59e0b', glow: 'rgba(245,158,11,0.6)',  label: 'Watch',    badge: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
  critical: { track: '#ef4444', station: '#ef4444', glow: 'rgba(239,68,68,0.6)',   label: 'Critical', badge: 'bg-red-500/20 text-red-400 border-red-500/30' },
};

export default function RailwayMap() {
  const mapRef = useRef(null);
  const leafletMap = useRef(null);
  const heatLayerRef = useRef(null);
  const [mapData, setMapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedSegment, setSelectedSegment] = useState(null);
  const [heatmapOn, setHeatmapOn] = useState(true);
  const [legendOpen, setLegendOpen] = useState(true);

  useEffect(() => {
    axios.get(`${API}/map-data`)
      .then(r => setMapData(r.data))
      .catch(() => setMapData(null))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!mapData || leafletMap.current) return;

    // Dynamically import Leaflet (avoids SSR issues)
    import('leaflet').then(L => {
      // Fix default icon path issue in bundlers
      delete L.Icon.Default.prototype._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
      });

      const map = L.map(mapRef.current, {
        center: [19.5, 73.6],
        zoom: 9,
        zoomControl: false,
        attributionControl: false,
      });

      leafletMap.current = map;

      // Dark Esri tile layer
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
        maxZoom: 16,
      }).addTo(map);

      // Draw track segments
      (mapData.segments || []).forEach(seg => {
        const color = CRITICALITY_COLORS[seg.criticality]?.track || '#10b981';
        const weight = seg.criticality === 'critical' ? 5 : (seg.criticality === 'watch' ? 4 : 3);

        // Glow effect (wider, transparent underline)
        L.polyline(seg.coords, {
          color: CRITICALITY_COLORS[seg.criticality]?.glow || 'rgba(16,185,129,0.3)',
          weight: weight + 6,
          opacity: 0.25,
        }).addTo(map);

        // Main line
        const line = L.polyline(seg.coords, {
          color,
          weight,
          opacity: 0.95,
          dashArray: seg.criticality === 'critical' ? '8,4' : null,
        }).addTo(map);

        line.on('click', () => setSelectedSegment(seg));
        line.on('mouseover', (e) => {
          line.setStyle({ weight: weight + 3, opacity: 1 });
          const info = seg.block_info;
          const fmtH = h => `${String(Math.floor(h)).padStart(2,'0')}:${String(Math.round((h - Math.floor(h)) * 60)).padStart(2,'0')}`;
          L.popup({ className: 'railway-popup' })
            .setLatLng(e.latlng)
            .setContent(`
              <div style="background:#0f0f0f;border:1px solid #333;border-radius:10px;padding:12px;min-width:200px;font-family:Inter,sans-serif;">
                <div style="color:#94a3b8;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">${seg.from} → ${seg.to}</div>
                <div style="color:${CRITICALITY_COLORS[seg.criticality]?.track};font-weight:700;font-size:13px;margin-bottom:8px">${CRITICALITY_COLORS[seg.criticality]?.label || 'Normal'}</div>
                ${info ? `
                  <div style="color:#e2e8f0;font-size:12px;margin-bottom:3px">Block: <span style="color:#10b981;font-family:monospace">${info.block_id}</span></div>
                  <div style="color:#94a3b8;font-size:11px;margin-bottom:3px">Dept: ${info.departments}</div>
                  <div style="color:#94a3b8;font-size:11px;margin-bottom:3px">Time: ${fmtH(info.start_hour)}–${fmtH(info.end_hour)} ${info.day}</div>
                  <div style="color:#f59e0b;font-size:11px">⚡ Speed limit: ${info.speed_restriction} km/h</div>
                ` : '<div style="color:#64748b;font-size:11px">No active maintenance</div>'}
              </div>
            `)
            .openOn(map);
        });
        line.on('mouseout', () => {
          line.setStyle({ weight, opacity: 0.95 });
        });
      });

      // Draw station markers
      (mapData.stations || []).forEach(st => {
        const color = CRITICALITY_COLORS[st.health]?.station || '#10b981';
        const r = st.health === 'critical' ? 10 : (st.health === 'watch' ? 9 : 8);

        const circle = L.circleMarker([st.lat, st.lon], {
          radius: r,
          fillColor: color,
          color: '#000',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.9,
        }).addTo(map);

        circle.bindTooltip(`
          <div style="background:#0f0f0f;border:1px solid #333;border-radius:8px;padding:8px 12px;font-family:Inter,sans-serif">
            <div style="color:#e2e8f0;font-weight:700;font-size:12px">${st.name}</div>
            <div style="color:${color};font-size:11px;margin-top:2px">Km ${st.km} · ${CRITICALITY_COLORS[st.health]?.label}</div>
          </div>
        `, { permanent: false, direction: 'top', className: 'railway-tooltip', opacity: 1 });

        // Pulsing ring for critical stations
        if (st.health === 'critical') {
          L.circleMarker([st.lat, st.lon], {
            radius: r + 6,
            fillColor: 'transparent',
            color: color,
            weight: 2,
            opacity: 0.4,
          }).addTo(map);
        }
      });

      // Heatmap: draw directly on a canvas overlay layer
      if (mapData.heatmap?.length) {
        const HeatLayer = L.Layer.extend({
          initialize(points) { this._points = points; },
          onAdd(map) {
            this._map = map;
            this._canvas = L.DomUtil.create('canvas', 'leaflet-heatmap-canvas');
            const size = map.getSize();
            this._canvas.width = size.x;
            this._canvas.height = size.y;
            this._canvas.style.position = 'absolute';
            this._canvas.style.pointerEvents = 'none';
            this._canvas.style.opacity = '0.55';
            map.getPanes().overlayPane.appendChild(this._canvas);
            map.on('moveend zoomend resize', this._redraw, this);
            this._redraw();
          },
          onRemove(map) {
            map.getPanes().overlayPane.removeChild(this._canvas);
            map.off('moveend zoomend resize', this._redraw, this);
          },
          _redraw() {
            const map = this._map;
            const size = map.getSize();
            const canvas = this._canvas;
            canvas.width = size.x; canvas.height = size.y;
            const origin = map.getPixelOrigin();
            const topLeft = map.containerPointToLayerPoint([0,0]);
            L.DomUtil.setPosition(canvas, topLeft);
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            this._points.forEach(([lat, lon, intensity]) => {
              const pt = map.latLngToContainerPoint([lat, lon]);
              const r = 22;
              const grad = ctx.createRadialGradient(pt.x, pt.y, 0, pt.x, pt.y, r);
              const alpha = Math.min(intensity * 0.7, 0.65);
              const clr = intensity > 0.7 ? `239,68,68` : intensity > 0.45 ? `245,158,11` : `14,165,233`;
              grad.addColorStop(0,   `rgba(${clr},${alpha})`);
              grad.addColorStop(0.5, `rgba(${clr},${alpha * 0.4})`);
              grad.addColorStop(1,   `rgba(${clr},0)`);
              ctx.fillStyle = grad;
              ctx.beginPath();
              ctx.arc(pt.x, pt.y, r, 0, Math.PI * 2);
              ctx.fill();
            });
          },
          setVisible(v) { this._canvas && (this._canvas.style.display = v ? '' : 'none'); },
        });
        heatLayerRef.current = new HeatLayer(mapData.heatmap).addTo(map);
      }


      // Attribution
      L.control.attribution({ prefix: '© CARTO | © OpenStreetMap' }).addTo(map);

    });

    return () => {
      if (leafletMap.current) {
        leafletMap.current.remove();
        leafletMap.current = null;
        heatLayerRef.current = null;
      }
    };
  }, [mapData]);

  // Toggle heatmap
  useEffect(() => {
    if (!heatLayerRef.current) return;
    heatLayerRef.current.setVisible?.(heatmapOn);
    if (leafletMap.current) {
      if (heatmapOn && !leafletMap.current.hasLayer(heatLayerRef.current)) {
        heatLayerRef.current.addTo(leafletMap.current);
      } else if (!heatmapOn && leafletMap.current.hasLayer(heatLayerRef.current)) {
        leafletMap.current.removeLayer(heatLayerRef.current);
      }
    }
  }, [heatmapOn]);

  const zoomIn = () => leafletMap.current?.zoomIn();
  const zoomOut = () => leafletMap.current?.zoomOut();

  const segStats = mapData ? {
    good: mapData.segments?.filter(s => s.criticality === 'good').length || 0,
    watch: mapData.segments?.filter(s => s.criticality === 'watch').length || 0,
    critical: mapData.segments?.filter(s => s.criticality === 'critical').length || 0,
  } : null;

  return (
    <div className="relative w-full" style={{ height: '580px' }}>
      {/* Leaflet CSS */}
      <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />

      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center z-20 bg-black/80 rounded-2xl">
          <div className="w-8 h-8 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-slate-400 text-sm">Loading railway map...</p>
        </div>
      )}

      {/* Map container */}
      <div ref={mapRef} className="w-full h-full rounded-2xl overflow-hidden" style={{ background: '#0a0a0a' }} />

      {/* Map controls */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 z-[1000]">
        <button onClick={zoomIn}  className="w-9 h-9 bg-[#111] border border-[#333] rounded-xl text-slate-300 hover:text-white hover:border-emerald-500/50 flex items-center justify-center transition-all"><ZoomIn className="w-4 h-4"/></button>
        <button onClick={zoomOut} className="w-9 h-9 bg-[#111] border border-[#333] rounded-xl text-slate-300 hover:text-white hover:border-emerald-500/50 flex items-center justify-center transition-all"><ZoomOut className="w-4 h-4"/></button>
        <button onClick={() => setHeatmapOn(h => !h)} className={`w-9 h-9 border rounded-xl flex items-center justify-center transition-all ${heatmapOn ? 'bg-orange-500/20 border-orange-500/50 text-orange-400' : 'bg-[#111] border-[#333] text-slate-500'}`} title="Toggle Heatmap"><Layers className="w-4 h-4"/></button>
      </div>

      {/* Legend */}
      {legendOpen && (
        <div className="absolute bottom-4 left-4 z-[1000] bg-[#0f0f0f]/95 border border-[#222] rounded-2xl p-4 min-w-[200px] backdrop-blur">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5"><Map className="w-3.5 h-3.5"/>Track Health</span>
            <button onClick={() => setLegendOpen(false)} className="text-slate-600 hover:text-slate-400 text-xs">✕</button>
          </div>
          {Object.entries(CRITICALITY_COLORS).map(([k, v]) => (
            <div key={k} className="flex items-center gap-2 mb-2">
              <div className="w-8 h-1.5 rounded-full" style={{ backgroundColor: v.track }}/>
              <span className="text-xs text-slate-400">{v.label}</span>
              {segStats && <span className="ml-auto text-xs font-mono text-slate-600">{segStats[k] ?? 0} seg</span>}
            </div>
          ))}
          <div className="border-t border-[#222] mt-2 pt-2">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-3 h-3 rounded-full bg-orange-400 opacity-60"/>
              <span className="text-xs text-slate-400">Defect Heatmap</span>
              <span className={`ml-auto text-[10px] font-semibold ${heatmapOn ? 'text-orange-400' : 'text-slate-600'}`}>{heatmapOn ? 'ON' : 'OFF'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Selected segment panel */}
      {selectedSegment && selectedSegment.block_info && (
        <div className="absolute top-4 left-4 z-[1000] bg-[#0f0f0f]/95 border border-[#333] rounded-2xl p-4 max-w-[260px] backdrop-blur animate-fade-in-up">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-white">{selectedSegment.from} → {selectedSegment.to}</span>
            <button onClick={() => setSelectedSegment(null)} className="text-slate-500 hover:text-white text-xs">✕</button>
          </div>
          <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold border mb-2 ${CRITICALITY_COLORS[selectedSegment.criticality]?.badge}`}>
            <AlertTriangle className="w-2.5 h-2.5"/>{CRITICALITY_COLORS[selectedSegment.criticality]?.label}
          </div>
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between"><span className="text-slate-500">Block ID</span><span className="text-emerald-400 font-mono">{selectedSegment.block_info.block_id}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Department</span><span className="text-slate-300">{selectedSegment.block_info.departments}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Scheduled</span><span className="text-slate-300">{selectedSegment.block_info.day}</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Speed Limit</span><span className="text-amber-400 font-bold">{selectedSegment.block_info.speed_restriction} km/h</span></div>
            <div className="flex justify-between"><span className="text-slate-500">Tasks</span><span className="text-slate-300">{selectedSegment.block_info.task_count}</span></div>
          </div>
        </div>
      )}

      {/* Title bar */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000]">
        <div className="flex items-center gap-2 bg-[#0f0f0f]/90 border border-[#333] rounded-full px-4 py-1.5 backdrop-blur">
          <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse"/>
          <span className="text-xs font-semibold text-slate-300">Mumbai–Nashik Corridor</span>
          <span className="text-[10px] text-emerald-400 font-mono">LIVE</span>
        </div>
      </div>
    </div>
  );
}
