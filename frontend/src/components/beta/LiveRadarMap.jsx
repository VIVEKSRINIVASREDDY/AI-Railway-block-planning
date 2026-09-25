import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { Layers } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || (import.meta.env.MODE === 'development' ? 'http://127.0.0.1:8000/api' : '/api');

export default function LiveRadarMap() {
  const mapRef = useRef(null);
  const leafletMap = useRef(null);
  const [trains, setTrains] = useState([]);
  const trainMarkersRef = useRef({});

  // Setup Map
  useEffect(() => {
    if (leafletMap.current) return;

    import('leaflet').then(L => {
      // Fix default icons
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
        attribution: 'Tiles &copy; Esri &mdash; Esri',
        maxZoom: 16,
      }).addTo(map);

      // Draw corridor line manually since we are independent
      const coords = [
        [18.9398, 72.8355], // CSMT
        [19.2389, 73.1293], // Kalyan
        [19.5315, 73.3042], // Kasara
        [19.7515, 73.4042], // Igatpuri
        [20.2509, 74.4398], // Manmad
      ];
      
      L.polyline(coords, {
        color: '#334155',
        weight: 6,
        opacity: 0.8,
      }).addTo(map);
      
      L.polyline(coords, {
        color: '#94a3b8',
        weight: 2,
        opacity: 0.5,
        dashArray: '5,5'
      }).addTo(map);
    });

    return () => {
      if (leafletMap.current) {
        leafletMap.current.remove();
        leafletMap.current = null;
      }
    };
  }, []);

  // Poll for Live Trains
  useEffect(() => {
    const fetchTrains = () => {
      axios.get(`${API}/beta/live-trains`)
        .then(res => {
          setTrains(res.data.trains || []);
        })
        .catch(err => console.error("Beta Live Trains Error:", err));
    };

    fetchTrains();
    const interval = setInterval(fetchTrains, 2000);
    return () => clearInterval(interval);
  }, []);

  // Update Train Markers
  useEffect(() => {
    if (!leafletMap.current) return;
    import('leaflet').then(L => {
      const map = leafletMap.current;
      
      // Update or Create
      trains.forEach(t => {
        const latlng = [t.lat, t.lon];
        
        if (trainMarkersRef.current[t.id]) {
          // Update position
          trainMarkersRef.current[t.id].setLatLng(latlng);
          
          // Update popup content if changed (e.g. speed)
          const popupContent = `
            <div style="background:#0b0f19;border:1px solid ${t.color};border-radius:8px;padding:12px;min-width:180px;font-family:Inter,sans-serif;">
              <div style="color:${t.color};font-weight:700;font-size:14px;margin-bottom:4px">${t.id} ${t.name}</div>
              <div style="color:#94a3b8;font-size:12px;margin-bottom:2px">Loco: ${t.loco} | Dir: ${t.heading}</div>
              <div style="color:#e2e8f0;font-size:12px;margin-bottom:2px">Speed: <strong style="color:#10b981">${t.speed} km/h</strong></div>
              <div style="color:${t.delay_mins > 0 ? '#ef4444' : '#10b981'};font-size:12px;margin-bottom:8px">Status: ${t.status} ${t.delay_mins > 0 ? `(+${t.delay_mins}m)` : ''}</div>
              ${t.conflict_warning ? `<div style="background:rgba(239,68,68,0.2);color:#f87171;padding:6px;border-radius:4px;font-size:11px;font-weight:600;">${t.conflict_warning}</div>` : ''}
            </div>
          `;
          trainMarkersRef.current[t.id].getPopup().setContent(popupContent);
        } else {
          // Create marker
          const svgIcon = L.divIcon({
            className: 'custom-train-marker',
            html: `
              <div style="position:relative; width:24px; height:24px; display:flex; justify-content:center; align-items:center;">
                <!-- Radar Sweep -->
                <div style="position:absolute; width:40px; height:40px; border-radius:50%; background:radial-gradient(circle, ${t.color}88 0%, transparent 70%); animation: pulse 2s infinite;"></div>
                <!-- Train Icon -->
                <div style="width:14px; height:14px; background:${t.color}; border:2px solid #fff; border-radius:50%; box-shadow:0 0 10px ${t.color}; z-index:10;"></div>
              </div>
            `,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
          });
          
          const marker = L.marker(latlng, { icon: svgIcon }).addTo(map);
          
          marker.bindPopup(`
            <div style="background:#0b0f19;border:1px solid ${t.color};border-radius:8px;padding:12px;min-width:180px;font-family:Inter,sans-serif;">
              <div style="color:${t.color};font-weight:700;font-size:14px;margin-bottom:4px">${t.id} ${t.name}</div>
              <div style="color:#94a3b8;font-size:12px;margin-bottom:2px">Loco: ${t.loco} | Dir: ${t.heading}</div>
              <div style="color:#e2e8f0;font-size:12px;margin-bottom:2px">Speed: <strong style="color:#10b981">${t.speed} km/h</strong></div>
              <div style="color:${t.delay_mins > 0 ? '#ef4444' : '#10b981'};font-size:12px;margin-bottom:8px">Status: ${t.status} ${t.delay_mins > 0 ? `(+${t.delay_mins}m)` : ''}</div>
              ${t.conflict_warning ? `<div style="background:rgba(239,68,68,0.2);color:#f87171;padding:6px;border-radius:4px;font-size:11px;font-weight:600;">${t.conflict_warning}</div>` : ''}
            </div>
          `);
          
          trainMarkersRef.current[t.id] = marker;
        }
      });
      
      // Cleanup removed trains
      const currentIds = trains.map(t => t.id);
      Object.keys(trainMarkersRef.current).forEach(id => {
        if (!currentIds.includes(id)) {
          map.removeLayer(trainMarkersRef.current[id]);
          delete trainMarkersRef.current[id];
        }
      });
    });
  }, [trains]);

  return (
    <div className="relative w-full h-full bg-[#111] rounded-2xl overflow-hidden border border-white/5 shadow-2xl">
      <style>{`
        @keyframes pulse {
          0% { transform: scale(0.5); opacity: 1; }
          100% { transform: scale(2.5); opacity: 0; }
        }
        .leaflet-container { background: #0b0f19 !important; font-family: 'Inter', sans-serif; }
      `}</style>

      {/* Map Container */}
      <div ref={mapRef} className="absolute inset-0 z-0" />

      {/* Glassmorphic Overlay for Controls */}
      <div className="absolute top-4 left-4 z-[400] flex flex-col gap-2">
        <div className="bg-[#111]/80 backdrop-blur-md border border-white/10 p-3 rounded-xl shadow-xl">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
            <h3 className="text-white font-bold text-sm tracking-wide">LIVE RAIL RADAR</h3>
          </div>
          <div className="text-slate-400 text-xs">Tracking {trains.length} Active Trains</div>
        </div>
        
        {/* Conflict Alerts Container */}
        {trains.filter(t => t.conflict_warning).map((t, idx) => (
          <div key={idx} className="bg-red-500/10 backdrop-blur-md border border-red-500/30 p-3 rounded-xl shadow-xl max-w-[280px]">
            <div className="text-red-400 text-xs font-bold uppercase mb-1 flex items-center gap-1">
              ⚠️ Maintenance Conflict
            </div>
            <div className="text-red-200/90 text-xs">
              {t.conflict_warning}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
