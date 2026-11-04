"""
Shared State and WebSocket Connection Manager for the AI Block Planning System.
"""

import json
from typing import Dict, Any, List
from fastapi import WebSocket
import pandas as pd


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts real-time events."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)

    async def broadcast_json(self, data: dict):
        """Convenience method: serialize dict to JSON and broadcast."""
        await self.broadcast(json.dumps(data, default=str))


manager = ConnectionManager()

# Global in-memory system state
state: Dict[str, Any] = {
    "schedule_df": None,
    "tasks_df": None,
    "blocks_df": None,
    "stats": None,
    "coa_df": None,
    "data": None,
    "is_ready": False,
    "emergency_history": [],
    "last_scenario": None,
    "baseline_comparison": None,
    "continuous_loop_enabled": False,
}
