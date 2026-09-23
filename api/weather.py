"""
Real-Time Weather Integration API Router.

Fetches live weather conditions via Open-Meteo for key corridor nodes.
If extreme weather (heavy rain, extreme heat) is detected, automatically
flags warnings or creates emergency track inspection tasks.
"""

import httpx
import json
import time
from typing import Dict, Any
from fastapi import APIRouter

from api.state import state, manager

router = APIRouter(prefix="/api/weather", tags=["Live Weather"])

# Pre-defined corridor weather stations
CORRIDOR_NODES = {
    "Mumbai CSMT": {"lat": 18.9398, "lon": 72.8355, "section": "CSMT-KYN"},
    "Kalyan": {"lat": 19.2389, "lon": 73.1293, "section": "CSMT-KYN"},
    "Lonavala": {"lat": 19.7515, "lon": 73.4042, "section": "KYN-IGP"},
    "Pune": {"lat": 18.5284, "lon": 73.8744, "section": "Pune Corridor"}
}

# WMO Weather interpretation codes
def get_weather_description(code: int) -> str:
    mapping = {
        0: "Clear sky",
        1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
    }
    return mapping.get(code, "Unknown")


async def fetch_weather_for_node(node_name: str, lat: float, lon: float) -> Dict[str, Any]:
    """Fetch live data from Open-Meteo for a specific coordinate."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json().get("current_weather", {})
                code = data.get("weathercode", 0)
                desc = get_weather_description(code)
                temp = data.get("temperature", 0.0)
                wind = data.get("windspeed", 0.0)

                # Determine if weather is hazardous to railway operations
                alert_level = "NORMAL"
                hazard_type = None
                
                # Heavy rain / thunderstorms
                if code in [65, 82, 95, 96, 99]:
                    alert_level = "CRITICAL"
                    hazard_type = "Track Flooding & Washout Risk"
                # Moderate rain
                elif code in [61, 63, 80, 81]:
                    alert_level = "WARNING"
                    hazard_type = "Reduced Visibility & Slippery Rail"
                # Extreme heat (Risk of Track Buckling)
                elif temp >= 42.0:
                    alert_level = "CRITICAL"
                    hazard_type = "Extreme Heat (Track Buckling Risk)"
                elif temp >= 38.0:
                    alert_level = "WARNING"
                    hazard_type = "High Heat"

                return {
                    "node": node_name,
                    "temperature": temp,
                    "windspeed": wind,
                    "weather_desc": desc,
                    "alert_level": alert_level,
                    "hazard_type": hazard_type,
                    "timestamp": data.get("time", time.strftime("%Y-%m-%dT%H:%M"))
                }
            return {"node": node_name, "error": "API Error"}
        except Exception as e:
            return {"node": node_name, "error": str(e)}


@router.get("/live")
async def get_live_weather():
    """Poll Open-Meteo for all corridor nodes and return aggregated weather state."""
    results = []
    has_critical = False
    critical_nodes = []

    for name, coords in CORRIDOR_NODES.items():
        node_weather = await fetch_weather_for_node(name, coords["lat"], coords["lon"])
        results.append(node_weather)
        
        if node_weather.get("alert_level") == "CRITICAL":
            has_critical = True
            critical_nodes.append(node_weather)

    response_payload = {
        "status": "success",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "corridor_weather": results,
        "global_alert": has_critical,
        "active_hazards": critical_nodes
    }

    # Store in global state
    state["live_weather"] = response_payload

    # If critical weather detected, broadcast alert via WebSocket
    if has_critical:
        await manager.broadcast(json.dumps({
            "event": "WEATHER_ALERT",
            "data": critical_nodes
        }))

    return response_payload
