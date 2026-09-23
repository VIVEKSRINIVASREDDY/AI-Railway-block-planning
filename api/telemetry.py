"""
Real-Time IoT Telemetry API Router.

Receives streaming sensor data from automated track inspection cars,
OHE voltage monitors, and trackside vibration sensors.
Detects anomalies in real-time and triggers automatic emergency replanning
if critical thresholds are breached.
"""

import time
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional

from api.state import state, manager
# We import trigger_emergency_replan directly to reuse the powerful replanning logic
from api.emergency import trigger_emergency_replan, EmergencyRequest

router = APIRouter(prefix="/api/telemetry", tags=["Live IoT Telemetry"])

class SensorPayload(BaseModel):
    sensor_id: str = Field(..., description="Unique ID of the sensor or inspection car")
    sensor_type: str = Field(..., description="Type of sensor: vibration, voltage, temperature, acoustic")
    km_marker: float = Field(..., description="Location of the reading")
    reading_value: float = Field(..., description="The scalar value recorded by the sensor")
    unit: str = Field(..., description="Unit of measurement (g, V, C, dB)")
    timestamp: Optional[str] = None


# Threshold definitions that convert raw readings into Emergency Incidents
THRESHOLDS = {
    "vibration": {"critical": 8.0, "unit": "g", "incident": "Broken Rail"},
    "voltage_drop": {"critical": -2000.0, "unit": "V", "incident": "OHE Wire Snap"}, # E.g., drops below 23kV standard by a lot
    "acoustic": {"critical": 120.0, "unit": "dB", "incident": "Point Machine Fault"},
}


async def _process_telemetry_background(payload: SensorPayload):
    """Background task to evaluate thresholds and trigger replanning without blocking the ingest endpoint."""
    t_cfg = THRESHOLDS.get(payload.sensor_type)
    
    # Store recent telemetry for dashboard ticker
    if "telemetry_feed" not in state:
        state["telemetry_feed"] = []
    
    feed_entry = {
        "timestamp": payload.timestamp or time.strftime("%H:%M:%S"),
        "sensor": f"{payload.sensor_id} ({payload.sensor_type})",
        "location": f"Km {payload.km_marker:.1f}",
        "value": f"{payload.reading_value:.1f} {payload.unit}",
        "status": "NORMAL"
    }

    if t_cfg:
        # Check if critical threshold is breached (absolute value check to handle negative drops too)
        is_critical = False
        if payload.sensor_type == "voltage_drop" and payload.reading_value <= t_cfg["critical"]:
            is_critical = True
        elif payload.sensor_type != "voltage_drop" and payload.reading_value >= t_cfg["critical"]:
            is_critical = True

        if is_critical:
            feed_entry["status"] = "CRITICAL_ANOMALY"
            
            # Broadcast the anomaly immediately
            await manager.broadcast(json.dumps({
                "event": "TELEMETRY_ANOMALY",
                "data": feed_entry
            }))
            
            # TRIGGER AUTONOMOUS REPLANNING
            print(f"\n[TELEMETRY] CRITICAL ANOMALY DETECTED: {payload.sensor_type} @ Km {payload.km_marker}")
            print("            -> Triggering immediate AI Emergency Replanning...")
            
            emg_req = EmergencyRequest(
                incident_type=t_cfg["incident"],
                km_marker=payload.km_marker,
                severity="CRITICAL",
                required_hours=3.5,
                description=f"Automated AI Trigger: {payload.sensor_type} sensor {payload.sensor_id} recorded {payload.reading_value} {payload.unit}."
            )
            
            try:
                # We await the replanning
                await trigger_emergency_replan(emg_req)
            except Exception as e:
                print(f"[TELEMETRY] Replanning failed: {e}")

    # Keep only last 50 events in memory
    state["telemetry_feed"].insert(0, feed_entry)
    state["telemetry_feed"] = state["telemetry_feed"][:50]
    
    # Broadcast normal tick as well for live dashboard graphs
    if feed_entry["status"] == "NORMAL":
        await manager.broadcast(json.dumps({
            "event": "TELEMETRY_TICK",
            "data": feed_entry
        }))


@router.post("/ingest")
async def ingest_telemetry(payload: SensorPayload, background_tasks: BackgroundTasks):
    """
    Ingest a live sensor reading.
    High throughput endpoint that offloads threshold checking and replanning to a background task.
    """
    if not payload.timestamp:
        payload.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        
    # Queue processing
    background_tasks.add_task(_process_telemetry_background, payload)
    
    return {"status": "received"}


@router.get("/feed")
async def get_telemetry_feed():
    """Return the recent telemetry history for dashboard tickers."""
    return {
        "count": len(state.get("telemetry_feed", [])),
        "feed": state.get("telemetry_feed", [])
    }
