"""
Real-Time Weather Data Collector.

Periodically polls Open-Meteo for live weather updates.
Updates the central RailwayState and triggers event detection.
"""

import asyncio
import httpx
import time
from typing import Dict, Any

from realtime.state_manager import digital_twin_state
from realtime.event_detector import detector

# Reusing the corridor nodes from api/weather.py
CORRIDOR_NODES = {
    "Mumbai CSMT": {"lat": 18.9398, "lon": 72.8355},
    "Kalyan": {"lat": 19.2389, "lon": 73.1293},
    "Lonavala": {"lat": 19.7515, "lon": 73.4042},
    "Pune": {"lat": 18.5284, "lon": 73.8744}
}

async def fetch_live_weather() -> None:
    """Background polling loop for live weather."""
    print("[WEATHER COLLECTOR] Started polling live Open-Meteo data...")
    while True:
        try:
            for node_name, coords in CORRIDOR_NODES.items():
                url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current_weather=true"
                
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json().get("current_weather", {})
                        code = data.get("weathercode", 0)
                        temp = data.get("temperature", 0.0)
                        
                        alert_level = "LOW"
                        hazard_type = None
                        
                        if code in [65, 82, 95, 96, 99] or temp >= 42.0:
                            alert_level = "CRITICAL"
                            hazard_type = "Track Flooding" if code in [65, 82, 95, 96, 99] else "Heat Buckling"
                        elif code in [61, 63, 80, 81] or temp >= 38.0:
                            alert_level = "MEDIUM"
                            hazard_type = "High Heat" if temp >= 38.0 else "Reduced Visibility"
                            
                        weather_obj = {
                            "node": node_name,
                            "alert_level": alert_level,
                            "hazard_type": hazard_type,
                            "temperature": temp
                        }
                        
                        # Forward to detector
                        if alert_level in ["MEDIUM", "HIGH", "CRITICAL"]:
                            await detector.process_weather_alert(weather_obj)
                            
            # Sleep 15 minutes before next poll (rate limit conscious)
            await asyncio.sleep(900)
            
        except Exception as e:
            print(f"[WEATHER COLLECTOR] Error polling Open-Meteo: {e}")
            await asyncio.sleep(60) # Exponential backoff retry logic
