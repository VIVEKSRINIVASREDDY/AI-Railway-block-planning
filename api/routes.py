"""
FastAPI Backend for the AI Block Planning System.

Provides REST API endpoints to trigger the pipeline, retrieve schedules,
tasks, and KPI metrics for the dashboard.
"""

import os
import sys
import json
import asyncio
from typing import Optional
from dotenv import load_dotenv

# Load .env from config directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", ".env"))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel



# ── Ensure project root is on path ──
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.generator import generate_all
from database.loader import load_data
from ai_engine.prioritizer import compute_criticality_scores
from ai_engine.clustering import cluster_tasks
from optimizer.solver import solve_block_scheduling
from realtime.collectors.weather_data import fetch_live_weather

from api.state import state, manager
from api.emergency import router as emergency_router
from api.scenario import router as scenario_router
from api.explainability import router as explainability_router
from api.baseline import router as baseline_router
from api.weather import router as weather_router
from api.telemetry import router as telemetry_router
from api.realtime_routes import router as realtime_data_router

# BETA Features
from BETA.api_beta import beta_router

# ── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Block Planning System",
    description="API for AI-Powered Automatic Block Planning (Indian Railways PS-26027)",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Alias for backward compatibility within this module
_state = state

# Mount feature routers
app.include_router(emergency_router)
app.include_router(scenario_router)
app.include_router(explainability_router)
app.include_router(baseline_router)
app.include_router(weather_router)
app.include_router(telemetry_router)
app.include_router(realtime_data_router)
app.include_router(beta_router)



# ── Schemas ──

class PipelineResponse(BaseModel):
    status: str
    message: str
    stats: Optional[dict] = None

class HealthResponse(BaseModel):
    status: str
    pipeline_ready: bool

class ChatRequest(BaseModel):
    message: str


# ── Routes ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Warm up pipeline on server start so dashboard loads immediately with live data."""
    try:
        await run_pipeline()
        asyncio.create_task(continuous_optimization_loop())
        asyncio.create_task(fetch_live_weather())
    except Exception as e:
        print(f"[WARN] Startup pipeline warmup error: {e}")

async def continuous_optimization_loop():
    """Background task that runs periodic updates only when explicitly enabled."""
    while True:
        await asyncio.sleep(20)
        if _state["is_ready"] and _state.get("continuous_loop_enabled", False):
            try:
                print("[BACKGROUND] Running continuous optimization cycle...")
                await run_pipeline()
            except Exception as e:
                print(f"[WARN] Continuous loop error: {e}")


@app.post("/api/simulation/toggle")
async def toggle_continuous_simulation():
    """Toggle continuous background optimization loop on or off."""
    _state["continuous_loop_enabled"] = not _state.get("continuous_loop_enabled", False)
    return {
        "continuous_loop_enabled": _state["continuous_loop_enabled"],
        "message": f"Continuous simulation {'enabled' if _state['continuous_loop_enabled'] else 'paused'}."
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        pipeline_ready=_state["is_ready"],
    )


@app.post("/api/generate", response_model=PipelineResponse)
async def run_pipeline():
    """
    Run the full pipeline:
    1. Generate synthetic data
    2. Ingest & validate
    3. Score criticality
    4. Cluster tasks
    5. Optimize schedule
    """
    try:
        # Step 1: Generate data
        generate_all()

        # Step 2: Load & validate
        data = load_data()

        # Step 3: Score
        scored = compute_criticality_scores(data["all_tasks"])

        # Step 4: Cluster
        blocks_df, tasks_clustered = cluster_tasks(scored)

        # Step 5: Optimize
        schedule_df, stats = solve_block_scheduling(
            blocks_df=blocks_df,
            coa_df=data["coa"],
            crews_df=data.get("crews"),
            equipment_df=data.get("equipment"),
            trains_df=data.get("trains"),
        )

        # Store in state
        _state["schedule_df"] = schedule_df
        _state["tasks_df"] = tasks_clustered
        _state["blocks_df"] = blocks_df
        _state["stats"] = stats
        _state["coa_df"] = data["coa"]
        _state["data"] = data
        _state["baseline_comparison"] = None
        _state["is_ready"] = True

        # Broadcast update to connected clients
        await manager.broadcast(json.dumps({
            "event": "pipeline_updated",
            "stats": stats
        }))

        return PipelineResponse(
            status="success",
            message=f"Pipeline complete. {stats['blocks_scheduled']}/{stats['total_blocks']} blocks scheduled.",
            stats=stats,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schedule")
async def get_schedule():
    """Return the optimized schedule as JSON."""
    if not _state["is_ready"] or _state["schedule_df"] is None:
        raise HTTPException(status_code=404, detail="Pipeline not yet run. POST /api/generate first.")

    df = _state["schedule_df"]
    return {
        "count": len(df),
        "schedule": json.loads(df.to_json(orient="records")),
    }


@app.get("/api/tasks")
async def get_tasks(department: Optional[str] = None):
    """Return all tasks with criticality scores."""
    if not _state["is_ready"] or _state["tasks_df"] is None:
        raise HTTPException(status_code=404, detail="Pipeline not yet run. POST /api/generate first.")

    df = _state["tasks_df"]
    if department:
        df = df[df["department"] == department]

    result = df.copy()
    if "priority_tier" in result.columns:
        result["priority_tier"] = result["priority_tier"].astype(str)

    return {
        "count": len(result),
        "tasks": json.loads(result.to_json(orient="records")),
    }


@app.get("/api/blocks")
async def get_blocks():
    """Return all integrated blocks."""
    if not _state["is_ready"] or _state["blocks_df"] is None:
        raise HTTPException(status_code=404, detail="Pipeline not yet run. POST /api/generate first.")

    df = _state["blocks_df"]
    return {
        "count": len(df),
        "blocks": json.loads(df.to_json(orient="records")),
    }


@app.get("/api/kpis")
async def get_kpis():
    """Return KPI metrics from the optimization."""
    if not _state["is_ready"] or _state["stats"] is None:
        raise HTTPException(status_code=404, detail="Pipeline not yet run. POST /api/generate first.")

    return _state["stats"]


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Real-time GenAI Assistant Endpoint (Using REST to avoid protobuf conflicts)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", ".env"))
        load_dotenv()
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return {"response": "⚠️ **GEMINI_API_KEY** is missing. Please set it in config/.env or your environment to chat with me!"}

    try:
        import requests
        stats = _state.get("stats") or {
            "asset_availability_pct": 81.5,
            "block_utilization_pct": 35.3,
            "schedule_rate_pct": 63.0,
            "blocks_scheduled": 104,
            "total_blocks": 165,
            "integration_rate_pct": 25.0,
            "multi_dept_blocks_scheduled": 48
        }
        
        # Build context
        context = f"""
        You are 'RailBot', an expert AI assistant for the Indian Railways Block Planning and Corridor Optimization System (Problem Statement PS-26027).
        Your tone is professional, technical, authoritative, and helpful. Keep answers concise, clear, and formatted nicely in markdown.
        
        CURRENT SYSTEM METRICS:
        - Asset Availability: {stats['asset_availability_pct']:.1f}%
        - Block Utilization: {stats['block_utilization_pct']:.1f}%
        - Schedule Rate: {stats['schedule_rate_pct']:.1f}% ({stats['blocks_scheduled']} / {stats['total_blocks']} blocks)
        - Integration Rate: {stats['integration_rate_pct']:.1f}% ({stats['multi_dept_blocks_scheduled']} joint blocks)
        
        USER QUESTION:
        {req.message}
        """
        
        # Try gemini-flash-latest, fallback to gemini-3.6-flash
        for model in ["gemini-flash-latest", "gemini-3.6-flash"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": context}]}]
            }
            headers = {"Content-Type": "application/json"}
            
            resp = requests.post(url, json=payload, headers=headers, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                reply = "".join([p.get("text", "") for p in parts if "text" in p]).strip()
                if reply:
                    return {"response": reply}
        
        return {"response": f"❌ **AI API Error:** {resp.status_code} - {resp.text}"}
            
    except Exception as e:
        return {"response": f"❌ **Error:** {str(e)}"}


@app.websocket("/api/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for client messages
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        manager.disconnect(websocket)


# ── Map Data Endpoint ─────────────────────────────────────────────────────────

# Static railway corridor layout: Mumbai-Pune-Nashik approximate route
RAILWAY_STATIONS = [
    {"id": "CSMT", "name": "Mumbai CSMT", "lat": 18.9398, "lon": 72.8355, "km": 0},
    {"id": "KYN",  "name": "Kalyan Jn",   "lat": 19.2389, "lon": 73.1293, "km": 55},
    {"id": "IGP",  "name": "Igatpuri",    "lat": 19.6989, "lon": 73.5601, "km": 120},
    {"id": "NSK",  "name": "Nashik Road", "lat": 19.9615, "lon": 73.8197, "km": 180},
    {"id": "DWD",  "name": "Devlali",     "lat": 19.9729, "lon": 73.8365, "km": 185},
    {"id": "MMR",  "name": "Manmad Jn",   "lat": 20.2509, "lon": 74.4398, "km": 256},
]

TRACK_SEGMENTS = [
    {"id": "SEG-1", "from": "CSMT", "to": "KYN",  "km_start": 0,   "km_end": 55,  "coords": [[18.9398,72.8355],[19.0500,72.9200],[19.1500,73.0200],[19.2389,73.1293]]},
    {"id": "SEG-2", "from": "KYN",  "to": "IGP",  "km_start": 55,  "km_end": 120, "coords": [[19.2389,73.1293],[19.3800,73.2500],[19.5200,73.3900],[19.6989,73.5601]]},
    {"id": "SEG-3", "from": "IGP",  "to": "NSK",  "km_start": 120, "km_end": 180, "coords": [[19.6989,73.5601],[19.7800,73.6400],[19.8700,73.7200],[19.9615,73.8197]]},
    {"id": "SEG-4", "from": "NSK",  "to": "DWD",  "km_start": 180, "km_end": 185, "coords": [[19.9615,73.8197],[19.9729,73.8365]]},
    {"id": "SEG-5", "from": "DWD",  "to": "MMR",  "km_start": 185, "km_end": 256, "coords": [[19.9729,73.8365],[20.0800,73.9800],[20.1600,74.2000],[20.2509,74.4398]]},
]

@app.get("/api/map-data")
async def get_map_data():
    """Return railway track geometry, station health, and defect heatmap data."""
    import random
    random.seed(42)

    # Enrich stations with health status from tasks if available
    stations = []
    for st in RAILWAY_STATIONS:
        health = "good"
        if _state["is_ready"] and _state["tasks_df"] is not None:
            df = _state["tasks_df"]
            # Find tasks near this station km
            nearby = df[(df["km_marker"] - st["km"]).abs() < 40] if "km_marker" in df.columns else df.iloc[0:0]
            if len(nearby) > 0:
                avg_score = nearby["criticality_score"].mean() if "criticality_score" in nearby.columns else 0
                if avg_score > 0.7:
                    health = "critical"
                elif avg_score > 0.45:
                    health = "watch"
        stations.append({**st, "health": health})

    # Enrich segments with criticality from schedule
    segments = []
    for seg in TRACK_SEGMENTS:
        criticality = "good"
        block_info = None
        speed_restriction = 110
        if _state["is_ready"] and _state["schedule_df"] is not None:
            df = _state["schedule_df"]
            # Match segment by km range
            matched = df[
                (df["section"].str.contains(seg["from"], na=False) |
                 df["section"].str.contains(seg["to"], na=False))
            ] if "section" in df.columns else df.iloc[0:0]
            if len(matched) > 0:
                block = matched.iloc[0]
                task_count = block.get("task_count", 1)
                criticality = "critical" if task_count >= 5 else ("watch" if task_count >= 3 else "good")
                speed_restriction = 30 if criticality == "critical" else (60 if criticality == "watch" else 110)
                block_info = {
                    "block_id": block.get("block_id", "N/A"),
                    "departments": block.get("departments", ""),
                    "day": block.get("day_of_week", ""),
                    "start_hour": block.get("block_start_hour", 0),
                    "end_hour": block.get("block_end_hour", 0),
                    "task_count": task_count,
                    "speed_restriction": speed_restriction,
                }
        segments.append({**seg, "criticality": criticality, "block_info": block_info, "speed_restriction": speed_restriction})

    # Generate defect heatmap points from tasks
    heatmap = []
    if _state["is_ready"] and _state["tasks_df"] is not None:
        df = _state["tasks_df"]
        for _, row in df.iterrows():
            km = row.get("km_marker", random.uniform(0, 256))
            # Interpolate lat/lon along the route based on km
            pct = min(km / 256.0, 1.0)
            lat = 18.9398 + pct * (20.2509 - 18.9398) + random.gauss(0, 0.015)
            lon = 72.8355 + pct * (74.4398 - 72.8355) + random.gauss(0, 0.015)
            intensity = float(row.get("criticality_score", 0.5))
            heatmap.append([lat, lon, intensity])

    return {"stations": stations, "segments": segments, "heatmap": heatmap}


# ── Incident Simulator Endpoint ───────────────────────────────────────────────




# ── Fleet Manager Endpoint ────────────────────────────────────────────────────

MACHINERY = [
    {"id": "TM-01", "name": "Track Tamper",              "type": "tamper",   "dept": "Engineering", "icon": "🚜"},
    {"id": "TW-01", "name": "Tower Wagon",                "type": "tower",    "dept": "Electrical",  "icon": "🚡"},
    {"id": "BR-01", "name": "Ballast Regulator",          "type": "ballast",  "dept": "Engineering", "icon": "🚧"},
    {"id": "UT-01", "name": "Ultrasonic Testing Van",     "type": "sonic",    "dept": "Engineering", "icon": "📡"},
    {"id": "OHE-01","name": "OHE Maintenance Vehicle",    "type": "ohe",      "dept": "Electrical",  "icon": "⚡"},
    {"id": "ST-01", "name": "Signal Testing Unit",        "type": "signal",   "dept": "S&T",         "icon": "🔦"},
    {"id": "TW-02", "name": "Tower Wagon #2",             "type": "tower",    "dept": "Electrical",  "icon": "🚡"},
    {"id": "TM-02", "name": "Track Tamper #2",            "type": "tamper",   "dept": "Engineering", "icon": "🚜"},
]

@app.get("/api/fleet")
async def get_fleet():
    """Return machinery allocation derived from schedule. Detects conflicts."""
    import random
    random.seed(99)

    if not _state["is_ready"] or _state["schedule_df"] is None:
        # Return idle fleet if pipeline not ready
        return {"machines": [
            {**m, "status": "idle", "assigned_block": None, "location_km": random.randint(0,256),
             "next_use": None, "available_from": "Now"} for m in MACHINERY
        ], "conflicts": []}

    df = _state["schedule_df"]
    dept_blocks = {}
    for _, row in df.iterrows():
        depts = [d.strip() for d in row.get("departments","").split(",")]
        for d in depts:
            if d not in dept_blocks:
                dept_blocks[d] = []
            dept_blocks[d].append(row)

    machines_out = []
    # Track machine → assigned block for conflict detection
    type_assignments = {}  # machine_type → list of (block_id, km, start_hour, end_hour)

    for m in MACHINERY:
        dept = m["dept"]
        blocks = dept_blocks.get(dept, [])
        # Assign to first available block that matches department
        assigned = None
        if blocks:
            # Pick a block pseudo-deterministically
            idx = (hash(m["id"]) % len(blocks))
            block = blocks[idx]
            assigned = {
                "block_id":   block.get("block_id",""),
                "section":    block.get("section",""),
                "day":        block.get("day_of_week",""),
                "start_hour": block.get("block_start_hour", 0),
                "end_hour":   block.get("block_end_hour", 0),
                "km":         random.randint(0, 256),
            }
            # Track for conflict detection
            if m["type"] not in type_assignments:
                type_assignments[m["type"]] = []
            type_assignments[m["type"]].append({
                "machine_id": m["id"],
                "machine_name": m["name"],
                "block_id": assigned["block_id"],
                "km": assigned["km"],
                "start_hour": assigned["start_hour"],
                "end_hour": assigned["end_hour"],
            })

        machines_out.append({
            **m,
            "status":         "deployed" if assigned else "idle",
            "assigned_block": assigned,
            "location_km":    assigned["km"] if assigned else random.randint(0, 256),
            "next_use":       assigned["day"] if assigned else None,
            "available_from": f"{int(assigned['end_hour']):02d}:00" if assigned else "Now",
        })

    # Detect conflicts: same machine type deployed in overlapping time windows at different km
    conflicts = []
    for mtype, assignments in type_assignments.items():
        for i in range(len(assignments)):
            for j in range(i+1, len(assignments)):
                a, b = assignments[i], assignments[j]
                # Time overlap check
                overlap = not (a["end_hour"] <= b["start_hour"] or b["end_hour"] <= a["start_hour"])
                # Location conflict (>30 km apart)
                dist = abs(a["km"] - b["km"])
                if overlap and dist > 30:
                    conflicts.append({
                        "type": mtype,
                        "machine_a": a["machine_name"],
                        "machine_b": b["machine_name"],
                        "block_a":   a["block_id"],
                        "block_b":   b["block_id"],
                        "km_diff":   dist,
                        "message":   f"{a['machine_name']} and {b['machine_name']} both needed simultaneously but are {dist}km apart.",
                    })

    return {"machines": machines_out, "conflicts": conflicts}


# ── Serve Static Frontend (If Built) ──

dist_path = os.path.join(project_root, "frontend", "dist")
if os.path.exists(dist_path):
    assets_path = os.path.join(dist_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        
        file_path = os.path.join(dist_path, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_path, "index.html"))


def create_app():
    return app
