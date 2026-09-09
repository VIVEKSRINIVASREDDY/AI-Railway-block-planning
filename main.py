# -*- coding: utf-8 -*-
"""
AI-Powered Automatic Block Planning System - Pipeline Entry Point.

Usage:
    python main.py --generate      Generate synthetic data
    python main.py --optimize      Run full pipeline (ingest -> score -> cluster -> optimize)
    python main.py --api           Launch FastAPI server
    python main.py --dashboard     Launch Streamlit dashboard
    python main.py --web           Build React UI and launch unified FastAPI server
    python main.py --all           Generate + Optimize + Launch API
"""

import argparse
import os
import sys
import subprocess
import json

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def cmd_generate():
    """Generate synthetic datasets."""
    from data.data_generator import generate_all
    generate_all()


def cmd_optimize():
    """Run full optimization pipeline."""
    from data.data_generator import generate_all
    from src.ingestion.loader import load_data
    from src.models.prioritizer import compute_criticality_scores
    from src.models.clustering import cluster_tasks
    from src.optimizer.solver import solve_block_scheduling

    # Step 1: Generate data (if not exists)
    data_dir = os.path.join(PROJECT_ROOT, "data", "generated")
    if not os.path.exists(os.path.join(data_dir, "tms_defects.csv")):
        print("No data found. Generating synthetic datasets first...\n")
        generate_all()

    # Step 2: Load & validate
    data = load_data()

    # Step 3: Score criticality
    scored_tasks = compute_criticality_scores(data["all_tasks"])

    # Step 4: Cluster
    blocks_df, tasks_clustered = cluster_tasks(scored_tasks)

    # Step 5: Optimize
    schedule_df, stats = solve_block_scheduling(blocks_df, data["coa"])

    # Save results
    output_dir = os.path.join(PROJECT_ROOT, "data", "generated")
    schedule_df.to_csv(os.path.join(output_dir, "schedule.csv"), index=False)
    blocks_df.to_csv(os.path.join(output_dir, "blocks.csv"), index=False)

    # Convert priority_tier to string before saving
    tasks_out = tasks_clustered.copy()
    if "priority_tier" in tasks_out.columns:
        tasks_out["priority_tier"] = tasks_out["priority_tier"].astype(str)
    tasks_out.to_csv(os.path.join(output_dir, "scored_tasks.csv"), index=False)

    with open(os.path.join(output_dir, "stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    print("=" * 60)
    print("  Pipeline Complete - Output Files")
    print("=" * 60)
    print(f"  - {output_dir}/schedule.csv")
    print(f"  - {output_dir}/blocks.csv")
    print(f"  - {output_dir}/scored_tasks.csv")
    print(f"  - {output_dir}/stats.json")
    print("=" * 60)

    return schedule_df, stats


def cmd_api():
    """Launch FastAPI server."""
    import uvicorn
    print("\n[*] Launching FastAPI server on http://localhost:8000")
    print("   Docs: http://localhost:8000/docs\n")
    uvicorn.run(
        "src.api.routes:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


def cmd_dashboard():
    """Launch Streamlit dashboard."""
    dashboard_path = os.path.join(PROJECT_ROOT, "ui", "app.py")
    print("\n[*] Launching Streamlit dashboard...")
    print("   URL: http://localhost:8501\n")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", dashboard_path,
         "--server.port=8501",
         "--server.headless=true",
         "--theme.base=dark"],
    )


def cmd_web():
    """Build Vite React app and launch FastAPI server for unified deployment."""
    ui_path = os.path.join(PROJECT_ROOT, "ui-web")
    print("\n[*] Building Vite React frontend...")
    build_result = subprocess.run(["npm", "run", "build"], cwd=ui_path, shell=True)
    if build_result.returncode != 0:
        print("Failed to build the frontend. Is npm installed?")
        return

    print("\n[*] Launching unified FastAPI server (Frontend + Backend)...")
    import uvicorn
    uvicorn.run(
        "src.api.routes:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


def main():
    parser = argparse.ArgumentParser(
        description="AI-Powered Automatic Block Planning System (Indian Railways PS-26027)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --generate              Generate synthetic data
  python main.py --optimize              Run full pipeline
  python main.py --api                   Start FastAPI server
  python main.py --dashboard             Start Streamlit UI
  python main.py --web                   Build React UI and start unified server
  python main.py --all                   Generate + Optimize + API
  python main.py --generate --optimize   Generate data, then optimize
        """,
    )
    parser.add_argument("--generate", action="store_true", help="Generate synthetic datasets")
    parser.add_argument("--optimize", action="store_true", help="Run full optimization pipeline")
    parser.add_argument("--api", action="store_true", help="Launch FastAPI server")
    parser.add_argument("--dashboard", action="store_true", help="Launch Streamlit dashboard")
    parser.add_argument("--web", action="store_true", help="Build React UI and launch unified server")
    parser.add_argument("--all", action="store_true", help="Generate + Optimize + Launch API")

    args = parser.parse_args()

    # Default: show help
    if not any([args.generate, args.optimize, args.api, args.dashboard, args.web, args.all]):
        parser.print_help()
        print("\n💡 Quick start: python main.py --web")
        return

    if args.all:
        cmd_generate()
        cmd_optimize()
        cmd_api()
        return

    if args.generate:
        cmd_generate()

    if args.optimize:
        cmd_optimize()

    if args.api:
        cmd_api()

    if args.dashboard:
        cmd_dashboard()

    if args.web:
        cmd_web()


if __name__ == "__main__":
    main()
