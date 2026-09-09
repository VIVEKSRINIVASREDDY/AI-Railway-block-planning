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

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import pandas as pd

# ── Ensure project root is on path ──
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.data_generator import generate_all
from src.ingestion.loader import load_data
from src.models.prioritizer import compute_criticality_scores
from src.models.clustering import cluster_tasks
from src.optimizer.solver import solve_block_scheduling

# ── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Block Planning System",
    description="API for AI-Powered Automatic Block Planning (Indian Railways PS-26027)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-Memory State ──
_state = {
    "schedule_df": None,
    "tasks_df": None,
    "blocks_df": None,
    "stats": None,
    "coa_df": None,
    "is_ready": False,
}

# ── WebSocket Manager ──
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()


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
        # Start the continuous background optimization loop
        asyncio.create_task(continuous_optimization_loop())
    except Exception as e:
        print(f"[WARN] Startup pipeline warmup error: {e}")

async def continuous_optimization_loop():
    """Background task that runs the pipeline periodically to simulate real-time defects."""
    while True:
        await asyncio.sleep(15)  # Run every 15 seconds
        if _state["is_ready"]:
            try:
                print("[BACKGROUND] Running continuous optimization...")
                await run_pipeline()
            except Exception as e:
                print(f"[WARN] Continuous loop error: {e}")


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
        schedule_df, stats = solve_block_scheduling(blocks_df, data["coa"])

        # Store in state
        _state["schedule_df"] = schedule_df
        _state["tasks_df"] = tasks_clustered
        _state["blocks_df"] = blocks_df
        _state["stats"] = stats
        _state["coa_df"] = data["coa"]
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
    if not _state["is_ready"] or _state["stats"] is None:
        return {"response": "The pipeline hasn't run yet. I don't have any data to analyze."}

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"response": "⚠️ **GEMINI_API_KEY** is missing. Please set it in your environment to chat with me!"}

    try:
        import requests
        stats = _state["stats"]
        
        # Build context
        context = f"""
        You are 'RailBot', an AI assistant for the Indian Railways Block Planning System.
        Your tone is professional, technical, and helpful. Keep answers concise.
        
        CURRENT SYSTEM METRICS:
        - Asset Availability: {stats['asset_availability_pct']:.1f}%
        - Block Utilization: {stats['block_utilization_pct']:.1f}%
        - Schedule Rate: {stats['schedule_rate_pct']:.1f}% ({stats['blocks_scheduled']} / {stats['total_blocks']} blocks)
        - Integration Rate: {stats['integration_rate_pct']:.1f}% ({stats['multi_dept_blocks_scheduled']} joint blocks)
        
        USER QUESTION:
        {req.message}
        """
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": context}]}]
        }
        headers = {"Content-Type": "application/json"}
        
        resp = requests.post(url, json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response.")
            return {"response": reply}
        else:
            return {"response": f"❌ **AI API Error:** {resp.status_code} - {resp.text}"}
            
    except Exception as e:
        return {"response": f"❌ **Error:** {str(e)}"}


@app.websocket("/api/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for client messages if any
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── Serve Static Frontend (If Built) ──

dist_path = os.path.join(project_root, "ui-web", "dist")
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
