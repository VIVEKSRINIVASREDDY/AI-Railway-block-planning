# -*- coding: utf-8 -*-
"""
Unified System Launcher for AI-Powered Automatic Block Planning System.
Launches the entire stack simultaneously:
  1. FastAPI Backend (port 8000)
  2. Streamlit Dashboard (port 8501)
  3. Vite React Frontend (port 5173) & Unified SPA (port 8000)
  4. Digital Twin IoT Telemetry Sensor Feed
"""

import os
import sys
import time
import signal
import subprocess
import webbrowser
import threading

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Determine the correct Python 3 executable
PYTHON_EXE = sys.executable

def print_banner():
    banner = r"""
======================================================================
  INDIAN RAILWAYS AI-POWERED AUTOMATIC BLOCK PLANNING SYSTEM
  Smart India Hackathon 2026 | Problem Statement: SIH26027
======================================================================
  [1] FastAPI Backend API     : http://localhost:8000
  [2] Interactive API Docs    : http://localhost:8000/docs
  [3] React Web Dashboard     : http://localhost:5173  (or http://localhost:8000)
  [4] Streamlit Dashboard     : http://localhost:8501
  [5] IoT Digital Twin Feed   : Streaming telemetry into port 8000
======================================================================
  Press Ctrl + C anytime to shut down all running services.
======================================================================
"""
    print(banner)

def ensure_initial_data():
    """Verify that schedule and dataset files exist; generate if missing."""
    generated_dir = os.path.join(PROJECT_ROOT, "database", "generated")
    schedule_file = os.path.join(generated_dir, "schedule.csv")
    
    if not os.path.exists(schedule_file):
        print("[*] Initial datasets not found. Running optimizer pipeline first...")
        subprocess.run([PYTHON_EXE, "main.py", "--optimize"], cwd=PROJECT_ROOT, check=True)
        print("[✓] Optimization completed.\n")
    else:
        print("[✓] Pre-computed datasets and schedule found.\n")

def run_iot_telemetry():
    """Run IoT simulation stream in background thread once API is up."""
    time.sleep(6)  # Give FastAPI time to start
    try:
        from scripts.iot_simulator import run_simulation
        print("[*] Digital Twin IoT Sensor stream started.")
        run_simulation(duration_seconds=3600)  # Stream for 1 hour or until shutdown
    except Exception as e:
        print(f"[!] IoT Simulator notice: {e}")

def main():
    print_banner()
    ensure_initial_data()

    processes = []
    
    try:
        # 1. Start FastAPI backend
        print("[*] Starting FastAPI Backend on port 8000...")
        fastapi_proc = subprocess.Popen(
            [
                PYTHON_EXE, "-m", "uvicorn", "api.routes:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ],
            cwd=PROJECT_ROOT,
        )
        processes.append(("FastAPI Backend", fastapi_proc))

        # 2. Start Streamlit Dashboard
        print("[*] Starting Streamlit Analytics Dashboard on port 8501...")
        dashboard_path = os.path.join(PROJECT_ROOT, "dashboard", "app.py")
        streamlit_proc = subprocess.Popen(
            [
                PYTHON_EXE, "-m", "streamlit", "run", dashboard_path,
                "--server.port", "8501",
                "--server.headless", "true",
                "--theme.base", "dark"
            ],
            cwd=PROJECT_ROOT,
        )
        processes.append(("Streamlit Dashboard", streamlit_proc))

        # 3. Start React Frontend (Vite dev server)
        frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        if os.path.exists(os.path.join(frontend_dir, "package.json")):
            print("[*] Starting Vite React Frontend on port 5173...")
            frontend_proc = subprocess.Popen(
                [npm_cmd, "run", "dev"],
                cwd=frontend_dir,
                shell=(sys.platform == "win32"),
            )
            processes.append(("React Frontend", frontend_proc))

        # 4. Start IoT Simulator in a daemon background thread
        iot_thread = threading.Thread(target=run_iot_telemetry, daemon=True)
        iot_thread.start()

        # 5. Open browser automatically after a short delay
        def open_browser():
            time.sleep(4)
            print("[*] Opening React Dashboard in default web browser...")
            webbrowser.open("http://localhost:5173")

        threading.Thread(target=open_browser, daemon=True).start()

        print("\n[✓] All services are running! Monitoring processes...\n")

        # Keep parent alive and monitor child processes
        while True:
            time.sleep(1)
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"\n[!] Notice: {name} exited with code {ret}")

    except KeyboardInterrupt:
        print("\n\n[*] Shutdown requested (Ctrl+C). Terminating all services...")
    finally:
        for name, proc in processes:
            try:
                print(f"[*] Stopping {name} (PID: {proc.pid})...")
                if sys.platform == "win32":
                    subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    proc.terminate()
            except Exception:
                pass
        print("\n[✓] All services successfully stopped. Goodbye!\n")

if __name__ == "__main__":
    main()
