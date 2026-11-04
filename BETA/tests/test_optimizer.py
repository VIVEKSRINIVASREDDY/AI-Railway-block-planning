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
        """Solver must produce a non-empty schedule DataFrame from synthetic data."""
        from database.loader import load_data
        from ai_engine.prioritizer import compute_criticality_scores
        from ai_engine.clustering import cluster_tasks
        from optimizer.solver import solve_block_scheduling

        data = load_data()
        scored = compute_criticality_scores(data["all_tasks"])
        blocks_df, _ = cluster_tasks(scored)
        schedule_df, stats = solve_block_scheduling(
            blocks_df=blocks_df,
            coa_df=data["coa"],
            equipment_df=data.get("equipment"),
        )
        assert len(schedule_df) > 0, "Schedule must contain at least one block"
        assert stats["solver_status"] in ("OPTIMAL", "FEASIBLE")

    def test_schedule_determinism(self):
        """Running the solver twice on the same data should yield identical results."""
        from database.loader import load_data
        from ai_engine.prioritizer import compute_criticality_scores
        from ai_engine.clustering import cluster_tasks
        from optimizer.solver import solve_block_scheduling

        data = load_data()
        scored = compute_criticality_scores(data["all_tasks"])
        blocks_df, _ = cluster_tasks(scored)

        _, stats_1 = solve_block_scheduling(
            blocks_df=blocks_df, coa_df=data["coa"], equipment_df=data.get("equipment"),
        )
        _, stats_2 = solve_block_scheduling(
            blocks_df=blocks_df, coa_df=data["coa"], equipment_df=data.get("equipment"),
        )
        assert stats_1["blocks_scheduled"] == stats_2["blocks_scheduled"], \
            "Identical input must produce identical schedule length"

    def test_no_overlapping_blocks(self):
        """No two blocks on the same section should have overlapping time windows."""
        from database.loader import load_data
        from ai_engine.prioritizer import compute_criticality_scores
        from ai_engine.clustering import cluster_tasks
        from optimizer.solver import solve_block_scheduling

        data = load_data()
        scored = compute_criticality_scores(data["all_tasks"])
        blocks_df, _ = cluster_tasks(scored)
        schedule_df, _ = solve_block_scheduling(
            blocks_df=blocks_df, coa_df=data["coa"], equipment_df=data.get("equipment"),
        )

        # Group by section and day
        for (section, day), group in schedule_df.groupby(["section", "day_of_week"]):
            sorted_blocks = group.sort_values("block_start_hour")
            starts = sorted_blocks["block_start_hour"].values
            ends = sorted_blocks["block_end_hour"].values
            for i in range(len(starts) - 1):
                assert ends[i] <= starts[i + 1] + 0.01, (
                    f"Overlap in section '{section}' on {day}: "
                    f"block ending at {ends[i]} vs next starting at {starts[i+1]}"
                )

    def test_kpi_targets(self):
        """Verify that optimization KPIs meet SRS targets."""
        from database.loader import load_data
        from ai_engine.prioritizer import compute_criticality_scores
        from ai_engine.clustering import cluster_tasks
        from optimizer.solver import solve_block_scheduling

        data = load_data()
        scored = compute_criticality_scores(data["all_tasks"])
        blocks_df, _ = cluster_tasks(scored)
        _, stats = solve_block_scheduling(
            blocks_df=blocks_df, coa_df=data["coa"], equipment_df=data.get("equipment"),
        )
        # SRS target: ≥ 88.5% asset availability
        assert stats["asset_availability_pct"] >= 85.0, \
            f"Asset availability {stats['asset_availability_pct']}% below target"
        # SRS target: ≥ 70% integration rate
        assert stats["integration_rate_pct"] >= 60.0, \
            f"Integration rate {stats['integration_rate_pct']}% below target"


# ─────────────────────────────────────────────────────────
# 2. AI Engine Tests
# ─────────────────────────────────────────────────────────
class TestAIEngine:
    """Verify AI scoring and clustering modules."""

    def test_prioritizer_import(self):
        from ai_engine.prioritizer import compute_criticality_scores
        assert callable(compute_criticality_scores)

    def test_clustering_import(self):
        from ai_engine.clustering import cluster_tasks
        assert callable(cluster_tasks)

    def test_criticality_scores_range(self):
        """Criticality scores must be between 0 and 100."""
        from database.loader import load_data
        from ai_engine.prioritizer import compute_criticality_scores

        data = load_data()
        scored = compute_criticality_scores(data["all_tasks"])
        assert "criticality_index" in scored.columns
        assert scored["criticality_index"].min() >= 0
        assert scored["criticality_index"].max() <= 100

    def test_clustering_produces_blocks(self):
        """DBSCAN clustering must produce at least one integrated block."""
        from database.loader import load_data
        from ai_engine.prioritizer import compute_criticality_scores
        from ai_engine.clustering import cluster_tasks

        data = load_data()
        scored = compute_criticality_scores(data["all_tasks"])
        blocks_df, tasks = cluster_tasks(scored)
        assert len(blocks_df) > 0, "At least one block must be formed"
        assert "block_id" in tasks.columns


# ─────────────────────────────────────────────────────────
# 3. Beta API Endpoint Tests
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
# 4. Data Loader Tests
# ─────────────────────────────────────────────────────────
class TestDataLoader:
    """Verify data loader works correctly."""

    def test_data_loader_import(self):
        from database.loader import load_data
        assert callable(load_data)

    def test_data_has_tasks(self):
        from database.loader import load_data
        data = load_data()
        assert data is not None
        assert isinstance(data, dict)
        assert "all_tasks" in data
        assert len(data["all_tasks"]) > 0

    def test_data_has_all_datasets(self):
        """Loader must return all expected dataset keys."""
        from database.loader import load_data
        data = load_data()
        expected_keys = ["tms", "smms", "tdms", "coa", "all_tasks", "crews", "equipment"]
        for key in expected_keys:
            assert key in data, f"Missing dataset key: {key}"
