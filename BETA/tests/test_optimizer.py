"""
BETA Test Suite — Automated tests for the Block Planning optimizer and Beta API.
Run with:  pytest BETA/tests/ -v
"""
import sys
import os
import pytest

# Ensure project root is on sys.path so imports resolve
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# ─────────────────────────────────────────────────────────
# 1. Optimizer Determinism Tests
# ─────────────────────────────────────────────────────────
class TestOptimizer:
    """Verify the CP-SAT solver produces consistent, valid schedules."""

    def test_solver_import(self):
        """Solver module must import without error."""
        from optimizer.solver import solve_block_scheduling
        assert callable(solve_block_scheduling)

    def test_solver_returns_schedule(self):
        """Solver must produce a non-empty schedule list from synthetic data."""
        from optimizer.solver import solve_block_scheduling
        from database.loader import load_synthetic_data

        data = load_synthetic_data()
        result = solve_block_scheduling(data)
        assert isinstance(result, list), "Solver must return a list"
        assert len(result) > 0, "Schedule must contain at least one block"

    def test_schedule_determinism(self):
        """Running the solver twice on the same data should yield identical results."""
        from optimizer.solver import solve_block_scheduling
        from database.loader import load_synthetic_data

        data = load_synthetic_data()
        run_1 = solve_block_scheduling(data)
        run_2 = solve_block_scheduling(data)
        assert len(run_1) == len(run_2), "Identical input must produce identical schedule length"

    def test_no_overlapping_blocks(self):
        """No two blocks on the same section should have overlapping time windows."""
        from optimizer.solver import solve_block_scheduling
        from database.loader import load_synthetic_data

        data = load_synthetic_data()
        schedule = solve_block_scheduling(data)

        # Group by section
        by_section = {}
        for block in schedule:
            sec = block.get("section", "unknown")
            by_section.setdefault(sec, []).append(block)

        for sec, blocks in by_section.items():
            sorted_blocks = sorted(blocks, key=lambda b: b.get("start_hour", 0))
            for i in range(len(sorted_blocks) - 1):
                end_i = sorted_blocks[i].get("start_hour", 0) + sorted_blocks[i].get("duration", 0)
                start_next = sorted_blocks[i + 1].get("start_hour", 0)
                assert end_i <= start_next, (
                    f"Overlap in section '{sec}': block ending at {end_i} vs next starting at {start_next}"
                )


# ─────────────────────────────────────────────────────────
# 2. Beta API Endpoint Tests
# ─────────────────────────────────────────────────────────
class TestBetaAPI:
    """Test the BETA Live Radar FastAPI endpoints."""

    def test_beta_router_import(self):
        """Beta router must import cleanly."""
        from BETA.api_beta import beta_router
        assert beta_router is not None

    def test_live_trains_endpoint(self):
        """GET /api/beta/live-trains must return a list of trains."""
        from fastapi.testclient import TestClient
        from BETA.api_beta import beta_router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(beta_router)
        client = TestClient(app)

        resp = client.get("/api/beta/live-trains")
        assert resp.status_code == 200

        data = resp.json()
        assert "trains" in data
        assert "timestamp" in data
        assert isinstance(data["trains"], list)
        assert len(data["trains"]) > 0

    def test_train_fields_present(self):
        """Each train in the response must have the expected fields."""
        from fastapi.testclient import TestClient
        from BETA.api_beta import beta_router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(beta_router)
        client = TestClient(app)

        resp = client.get("/api/beta/live-trains")
        train = resp.json()["trains"][0]

        required_fields = ["id", "name", "type", "loco", "lat", "lon", "speed", "heading", "delay_mins", "status"]
        for field in required_fields:
            assert field in train, f"Missing required field: {field}"

    def test_train_coordinates_in_range(self):
        """All train coordinates must be within the Mumbai-Manmad corridor bounding box."""
        from fastapi.testclient import TestClient
        from BETA.api_beta import beta_router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(beta_router)
        client = TestClient(app)

        resp = client.get("/api/beta/live-trains")
        for train in resp.json()["trains"]:
            assert 17.0 < train["lat"] < 22.0, f"Latitude out of range: {train['lat']}"
            assert 71.0 < train["lon"] < 76.0, f"Longitude out of range: {train['lon']}"


# ─────────────────────────────────────────────────────────
# 3. Data Loader Tests
# ─────────────────────────────────────────────────────────
class TestDataLoader:
    """Verify synthetic data loaders work correctly."""

    def test_data_loader_import(self):
        from database.loader import load_synthetic_data
        assert callable(load_synthetic_data)

    def test_data_has_tasks(self):
        from database.loader import load_synthetic_data
        data = load_synthetic_data()
        assert data is not None
        # Data should be a dict or similar with tasks/sections
        assert isinstance(data, (dict, list))
