# AI-Powered Automatic Block Planning System
## Indian Railways Problem Statement 26027

### Overview
An integrated, AI-driven Automatic Block Planning system that ingests maintenance defects and corridor schedule data, scores and clusters tasks using ML/heuristics, and solves a constraint-based optimization to produce conflict-free weekly/monthly block maintenance plans for Indian Railways.

### Architecture
```
TMS/SMMS/TDMS (Defects) ──► Data Ingestion ──► AI Prioritization ──► Spatial Clustering ──► OR-Tools Optimizer ──► FastAPI ──► Streamlit Dashboard
COA (Corridor Schedule) ──┘                    (Criticality Index)   (DBSCAN Grouping)     (CP-SAT Solver)         (API)      (Gantt + KPIs)
```

### Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate synthetic data
python main.py --generate

# 3. Run full optimization pipeline
python main.py --optimize

# 4. Launch API server
python main.py --api

# 5. Launch dashboard (in separate terminal)
python main.py --dashboard

# Or run everything at once
python main.py --all
```

### Project Structure
```
capstone-project/
├── data/                    # Synthetic data generation
│   ├── data_generator.py    # Generator for TMS, SMMS, TDMS, COA
│   └── generated/           # Output CSVs
├── src/
│   ├── ingestion/           # Data loading & schema validation
│   │   └── loader.py
│   ├── models/              # AI/ML models
│   │   ├── prioritizer.py   # Criticality Index scoring
│   │   └── clustering.py    # DBSCAN spatial clustering
│   ├── optimizer/           # Optimization engine
│   │   └── solver.py        # OR-Tools CP-SAT solver
│   └── api/                 # REST API
│       └── routes.py        # FastAPI endpoints
├── ui/
│   └── app.py               # Streamlit dashboard
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
