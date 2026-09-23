"""
Centralized Configuration for AI Block Planning System.

All modules import paths from here instead of computing them individually.
"""

import os
from pathlib import Path

# ── Project Root ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── Directory Paths ──
CONFIG_DIR = PROJECT_ROOT / "config"
DATABASE_DIR = PROJECT_ROOT / "database"
GENERATED_DIR = DATABASE_DIR / "generated"
AI_ENGINE_DIR = PROJECT_ROOT / "ai_engine"
OPTIMIZER_DIR = PROJECT_ROOT / "optimizer"
API_DIR = PROJECT_ROOT / "api"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# ── Environment ──
ENV_PATH = CONFIG_DIR / ".env"

# ── Data File Paths ──
TMS_CSV = GENERATED_DIR / "tms_defects.csv"
SMMS_CSV = GENERATED_DIR / "smms_defects.csv"
TDMS_CSV = GENERATED_DIR / "tdms_defects.csv"
COA_CSV = GENERATED_DIR / "coa_windows.csv"
SCHEDULE_CSV = GENERATED_DIR / "schedule.csv"
BLOCKS_CSV = GENERATED_DIR / "blocks.csv"
SCORED_TASKS_CSV = GENERATED_DIR / "scored_tasks.csv"
STATS_JSON = GENERATED_DIR / "stats.json"

# ── Ensure project root is on sys.path ──
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
