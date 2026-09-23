"""
Event Detection Engine.

Processes raw live and simulated data to detect state changes.
Generates standardized events (e.g., TRAIN_DELAYED, WEATHER_ALERT).
Determines if an event severity breaches the threshold for autonomous replanning.
"""

import time
import uuid
import random
from typing import Dict, Any, Optional

from realtime.state_manager import digital_twin_state, RailwayEvent
from api.state import manager # For WebSocket broadcasting

# Assume replanner is implemented in realtime.replanner
import realtime.replanner as replanner

class EventDetector:
    def __init__(self):
        # Configurable threshold: Only MEDIUM, HIGH, CRITICAL trigger replans.
        self.replan_thresholds = ["MEDIUM", "HIGH", "CRITICAL"]

    async def process_train_update(self, train_id: str, delay_minutes: int, location: str) -> Optional[RailwayEvent]:
        """Detects if a train update constitutes a reportable event."""
        # Get previous state
        prev_train = digital_twin_state.active_trains.get(train_id, {})
        prev_delay = prev_train.get("delay", 0)
        
        # Only flag if delay increased significantly (e.g., > 10 mins change)
        if abs(delay_minutes - prev_delay) > 10:
            severity = "LOW"
            if delay_minutes > 15: severity = "MEDIUM"
            if delay_minutes > 30: severity = "HIGH"
            if delay_minutes > 60: severity = "CRITICAL"
            
            event = RailwayEvent(
                event_id=str(uuid.uuid4())[:8],
                event_type="TRAIN_DELAYED" if delay_minutes > prev_delay else "TRAIN_RECOVERED",
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                severity=severity,
                source="SIMULATED",
                affected_trains=[train_id],
                description=f"Train {train_id} at {location} reported a delay of {delay_minutes} minutes."
            )
            
            await self._emit_event(event)
            return event
        
        # Update state silently if minor change
        digital_twin_state.update_train_delay(train_id, delay_minutes, location)
        return None

    async def process_weather_alert(self, weather_data: Dict[str, Any]) -> RailwayEvent:
        """Processes an incoming weather anomaly from Open-Meteo."""
        severity = weather_data.get("alert_level", "LOW")
        hazard = weather_data.get("hazard_type", "Unknown Anomaly")
        node = weather_data.get("node", "Unknown Section")
        
        event = RailwayEvent(
            event_id=str(uuid.uuid4())[:8],
            event_type="WEATHER_ALERT",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            severity=severity,
            source="LIVE",
            description=f"Live Weather API reports {hazard} near {node}."
        )
        
        await self._emit_event(event)
        return event

    async def _emit_event(self, event: RailwayEvent):
        """Register event in state, broadcast to UI, and trigger replan if necessary."""
        digital_twin_state.add_event(event)
        
        # Broadcast via WebSocket to Live UI
        await manager.broadcast_json({
            "event": "NEW_RAILWAY_EVENT",
            "data": event.model_dump()
        })
        
        # Determine if we should replan
        if event.severity in self.replan_thresholds:
            print(f"[EVENT DETECTOR] {event.severity} event detected: {event.event_type}. Triggering Impact Analysis & Replanner...")
            await replanner.trigger_dynamic_replan(event)

detector = EventDetector()
