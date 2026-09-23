"""
Real-Time API Routes.

Exposes the digital twin state, live events, plan versioning, and analytics
to the frontend.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from realtime.state_manager import digital_twin_state
from realtime.event_detector import detector
import analytics.impact_analysis as impact_engine
import analytics.resilience as resilience_engine

router = APIRouter(tags=["Real-Time Digital Twin"])

class SimulationEventReq(BaseModel):
    event_type: str
    target_id: str
    value: int
    location: str

@router.get("/api/realtime/state")
async def get_realtime_state():
    return {
        "active_trains": digital_twin_state.active_trains,
        "critical_assets": digital_twin_state.critical_assets,
        "current_plan_version": digital_twin_state.current_plan.plan_id if digital_twin_state.current_plan else "BASELINE"
    }

@router.get("/api/realtime/events")
async def get_realtime_events():
    return {"events": [e.model_dump() for e in digital_twin_state.event_feed]}

@router.get("/api/realtime/plan/{plan_id}")
async def get_plan_version(plan_id: str):
    for p in digital_twin_state.plan_history:
        if p.plan_id == plan_id:
            return p.model_dump()
    raise HTTPException(status_code=404, detail="Plan version not found")

@router.get("/api/analytics/impact/{event_id}")
async def get_impact_analysis(event_id: str):
    for e in digital_twin_state.event_feed:
        if e.event_id == event_id:
            return impact_engine.calculate_impact(e)
    raise HTTPException(status_code=404, detail="Event not found")

@router.get("/api/analytics/resilience")
async def get_resilience_score():
    return resilience_engine.compute_resilience_score()

@router.post("/api/simulation/inject")
async def inject_simulation_event(req: SimulationEventReq):
    """Manual injection of events for the Digital Twin UI Simulator."""
    if req.event_type == "TRAIN_DELAYED":
        # Simulating a train delay which triggers the detector
        event = await detector.process_train_update(req.target_id, req.value, req.location)
        if event:
            return {"status": "success", "event_id": event.event_id, "message": "Event triggered replan"}
        return {"status": "success", "message": "Delay updated silently (below threshold)"}
        
    return {"status": "error", "message": "Unknown event type"}
