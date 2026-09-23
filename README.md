# AI-Powered Automatic Block Planning System
## Indian Railways Problem Statement 26027

### Overview
An integrated, AI-driven Automatic Block Planning system that ingests maintenance defects and corridor schedule data, scores and clusters tasks using ML/heuristics, and solves a constraint-based optimization to produce conflict-free weekly/monthly block maintenance plans for Indian Railways.

### Architecture
```
TMS/SMMS/TDMS (Defects) ──► Data Ingestion ──► AI Prioritization ──► Spatial Clustering ──► OR-Tools Optimizer ──► FastAPI ──► Streamlit Dashboard
COA (Corridor Schedule) ──┘                    (Criticality Index)   (DBSCAN Grouping)     (CP-SAT Solver)         (API)      (Gantt + KPIs)
```

### Quick Start (Run Whole Project at Once)

To launch the **entire project simultaneously** (FastAPI backend + React Web App + Streamlit Dashboard + IoT Sensor Telemetry Feed):

```bash
# Option A: Run the unified launcher script
py run_all.py

# Option B: Run via main CLI flag
py main.py --all

# Option C (Windows One-Click):
.\run_all.bat
```

Once launched:
- 🌐 **Modern React Web App**: [http://localhost:5173](http://localhost:5173) (or [http://localhost:8000](http://localhost:8000))
- 📊 **Streamlit Analytics Dashboard**: [http://localhost:8501](http://localhost:8501)
- ⚡ **FastAPI Server**: [http://localhost:8000](http://localhost:8000)
- 📑 **Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 📡 **Digital Twin IoT Feed**: Streaming live sensor telemetry into port 8000

---

### Individual Service Commands
If you prefer running services independently:
```bash
# 1. Generate synthetic data
py main.py --generate

# 2. Run AI optimization pipeline
py main.py --optimize

# 3. Launch FastAPI server only
py main.py --api

# 4. Launch Streamlit dashboard only
py main.py --dashboard

# 5. Launch React Web UI + Unified Backend
py main.py --web
```


### Project Structure
```
capstone-project/
├── config/                  # Configuration and environments
├── database/                # Data generation & ingestion
│   ├── generator.py         # Synthetic data generator
│   ├── loader.py            # CSV loading & validation
│   └── generated/           # Output CSVs
├── ai_engine/               # AI/ML models
│   ├── prioritizer.py       # Criticality Index scoring
│   └── clustering.py        # DBSCAN spatial clustering
├── optimizer/               # Optimization engine
│   └── solver.py            # OR-Tools CP-SAT solver
├── api/                     # REST API backend
│   └── routes.py            # FastAPI endpoints
├── frontend/                # React Web application
├── dashboard/               # Streamlit dashboard
│   └── app.py               
├── scripts/                 # Utility scripts
├── main.py                  # Pipeline entry point
├── requirements.txt
└── README.md
```

### Modules

| Module | Purpose |
|--------|---------|
| **Data Generator** | Creates realistic synthetic maintenance defect data (TMS, SMMS, TDMS) and corridor schedules (COA) |
| **Ingestion** | Loads CSVs, validates schemas via Pydantic, merges into unified task dataframe |
| **Prioritizer** | Computes Criticality Index (0-100) using weighted heuristic + XGBoost blend |
| **Clustering** | Groups spatially overlapping tasks across departments using DBSCAN (eps=2.0 km) |
| **Optimizer** | CP-SAT constraint solver maximizing criticality-weighted coverage within corridor windows |
| **API** | FastAPI backend serving schedule, task, and KPI data |
| **Dashboard** | Streamlit UI with Plotly Gantt charts, KPI cards, and department filters |

### Key Metrics
- **Asset Availability %**: Percentage of track-hours available for train operations
- **Block Utilization Rate**: How efficiently maintenance windows are used
- **Conflict Reduction**: Reduction in scheduling conflicts vs. manual planning
- **Integration Rate**: Percentage of multi-department tasks scheduled as integrated blocks

### Team
University Capstone Project — 2026

### License
Academic Use Only
