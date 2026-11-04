# Comprehensive System Audit: AI-Powered Automatic Block Planning System
**Indian Railways Problem Statement 26027**  
**Audit Date:** November 2026  
**Auditor Role:** Principal Systems Architect, Operations Research Engineer & Full-Stack Developer  
**Status:** Phase 0 Complete — Audit Before Change (Zero Code Modified)

---

## 1. Executive Summary

An exhaustive technical audit of the codebase was conducted against the Master Specification (`SPEC.md`). The repository contains a working prototype that integrates data generation, rule/XGBoost-based scoring, DBSCAN spatial clustering, OR-Tools CP-SAT scheduling, FastAPI endpoints, a React 19 GIS cockpit, and a secondary Streamlit analytics dashboard.

**Key Findings:**
1. **Existing Baseline Works:** Core optimization (`optimizer/solver.py`), AI prioritization (`ai_engine/prioritizer.py`), DBSCAN clustering (`ai_engine/clustering.py`), and data loading (`database/loader.py`) execute successfully. 12 automated unit tests pass in 26 seconds.
2. **Critical Safety & Architecture Gaps:**
   - **No Independent Validator:** Constraint safety is asserted solely by the solver; no independent rule checker (`optimizer/validator.py`) exists.
   - **Binary CP-SAT Model:** The solver uses discrete binary variables `x[b,w]` on precomputed windows instead of continuous CP-SAT interval variables (`NewIntervalVar`, `AddNoOverlap`), limiting temporal flexibility.
   - **Single Linear Axis Corridor:** Corridors are modeled as 1D linear KM lines rather than a multi-line graph (UP/DOWN, Fast/Slow, junction bifurcations at Kalyan to Thal Ghat / Bhor Ghat).
   - **Absence of Indian Railways Governance Lifecycle:** Lacks the 5-tier planning horizons (26-week roadmap, 4-week rolling, weekly DRM approval, T-1 freeze, emergent), deviation reason codes, and role-based access control.
   - **No Provenance Tracking:** Records and API outputs lack provenance tags (`REAL`, `SYNTHETIC`, `SIMULATED`, `LIVE`).
   - **Unmeasured Figures in Documentation:** README claims "89.4% availability" and "73.5% integration", but no `benchmarks/` suite or `results/*.json` exists to substantiate them.
   - **Client-Side Sanction Orders:** PDF sanction orders are generated in the browser via `jsPDF` with unhashed QR strings, lacking server-side Ed25519/HMAC cryptographic signatures.
   - **Test Suite Network Hangs:** Tests calling `api_beta.py` hang in sandboxed or offline environments due to unmocked external requests to Open-Meteo.

---

## 2. Test Suite & Runtime Execution Audit

### 2.1 Automated Test Execution (`pytest BETA/tests/ -v`)
- **Python Environment:** Python 3.13.1 (64-bit), `pytest-9.2.0`, `anyio-4.11.0`.
- **Tests Executed:** 16 tests in `BETA/tests/test_optimizer.py`.
- **Results:**
  - `TestOptimizer` (5 tests): **100% PASSED**
    - `test_solver_import`: PASSED
    - `test_solver_returns_schedule`: PASSED (produces valid non-empty schedule DataFrame)
    - `test_schedule_determinism`: PASSED (identical input produces identical block count)
    - `test_no_overlapping_blocks`: PASSED (validates block_end <= block_start on section/day)
    - `test_kpi_targets`: PASSED (asset availability >= 85%, integration rate >= 60%)
  - `TestAIEngine` (4 tests): **100% PASSED**
    - `test_prioritizer_import`: PASSED
    - `test_clustering_import`: PASSED
    - `test_criticality_scores_range`: PASSED (scores bounded in [0, 100])
    - `test_clustering_produces_blocks`: PASSED
  - `TestDataLoader` (3 tests): **100% PASSED**
    - `test_data_loader_import`: PASSED
    - `test_data_has_tasks`: PASSED
    - `test_data_has_all_datasets`: PASSED
  - `TestBetaAPI` (4 tests): **BLOCKED / HANGS IN OFFLINE RUNTIME**
    - `test_live_trains_endpoint`, `test_train_fields_present`, `test_train_coordinates_in_range` trigger `fetch_corridor_weather()`, which attempts an unmocked network request to `api.open-meteo.com` with a 4.0s timeout per attempt, hanging in sandboxed environments without offline fallbacks.

### 2.2 Launcher & CLI Execution
- `python main.py --help`: **PASSED** (all flags `--generate`, `--optimize`, `--api`, `--dashboard`, `--web`, `--realtime`, `--simulate`, `--replan`, `--all` recognized).
- `run_all.py`: Orchestrates FastAPI, Streamlit, Vite, and IoT simulator concurrently via subprocesses.

---

## 3. Detailed Gap Analysis Against Specification

### Section 1: Role & Operating Rules
| Requirement | Current Repository State | Compliance | Risk |
| :--- | :--- | :---: | :---: |
| Audit before change (preserve what works) | Repository inspected in detail; zero code touched during audit | **Compliant** | None |
| No unmeasured numbers (metrics from `benchmarks/results/*.json`) | No `benchmarks/` dir exists. Numbers in README/v1 PRD are hardcoded | **Non-Compliant** | High |
| Provenance on every record (`REAL`, `SYNTHETIC`, `SIMULATED`, `LIVE`) | No provenance field in any Pydantic schema or CSV output | **Non-Compliant** | High |
| Decision support only; zero claim of 100% safety | v1 PRD claimed "100% Deterministic Safety"; needs strictly scoped wording | **Non-Compliant** | Medium |
| Exact methods decide schedules (CP-SAT rules over ML/LLM) | CP-SAT decides schedule; ML provides input scores only | **Compliant** | None |
| Defensible by team (simple, commented models with why comments) | Code has docstrings, but needs formal "why" justification lines | **Partial** | Low |
| Small steps; assumptions in `docs/ASSUMPTIONS.md` | `docs/ASSUMPTIONS.md` did not exist | **Remediated** | Low |

---

### Section 2: Mission, Scope & Process Alignment
| Requirement | Current Repository State | Compliance | Risk |
| :--- | :--- | :---: | :---: |
| Rolling Block Plan horizons (26-week, 4-week, weekly, T-1, emergent) | Flat single-horizon 7-day schedule only; no planning modes or freeze rules | **Non-Compliant** | High |
| Lead times modeled per block class (>4h mega block needs Board approval) | Duration capped at 4.0h; no mega-block lead-time or ARP governance | **Non-Compliant** | Medium |
| Block types (Traffic, Power/OHE, Signalling disconnection) | Tracks department (ENG/S&T/TRD) but lacks formal block-type classification | **Partial** | Medium |
| Deviation codes on denial or reduction (Sr.DOM/DOM approval) | Replanner modifies schedules without recording IR reason codes | **Non-Compliant** | Medium |
| Graph corridor model (CSMT-Kalyan 4+ lines, Thal Ghat, Bhor Ghat, ghat rules) | Flat 1D KM axis; 4 independent lines (CSMT-Pune, Delhi-Kanpur, etc.) without junctions | **Non-Compliant** | High |

---

### Section 4: Data Layer (`database/`)
| Requirement | Current Repository State | Compliance | Risk |
| :--- | :--- | :---: | :---: |
| Pydantic v2 schemas with `provenance`, `line_id`, `km_from`, `km_to`, `block_type`, `duration_p50/p90`, `deadline` | Schemas in `loader.py` lack these fields; tasks have single `chainage_km` | **Non-Compliant** | High |
| Block demand schema (reason, min duration, preferred window, readiness, output, consequence) | No block demand request schema; raw defects are directly clustered | **Non-Compliant** | High |
| Data-quality report on load (missing fields, invalid km, overlaps, orphan IDs) | Only basic row validation error count printed to stdout; no structured report | **Non-Compliant** | Medium |
| Configured seeded generator in `config/scenario.yaml` | `config/scenario.yaml` does not exist; parameters hardcoded in `generator.py` | **Non-Compliant** | High |
| DataSource adapter interface (for real COA/TMS/SMMS/TDMS exports) | Hardcoded `pd.read_csv()` in `loader.py`; no adapter interface | **Non-Compliant** | Medium |

---

### Section 5: Criticality Engine (`ai_engine/prioritizer.py`)
| Requirement | Current Repository State | Compliance | Risk |
| :--- | :--- | :---: | :---: |
| Tiers: P1 >= 80, P2 60-79, P3 40-59, P4 < 40 | Cutoffs match, but tier assignment uses string labels | **Compliant** | Low |
| Configurable weights in `config/weights.yaml` | Weights hardcoded in `prioritizer.py` (`WEIGHTS` dict); no YAML file | **Non-Compliant** | High |
| Safety floors (sev 5, rail fracture, buckling alert -> P1) | Only checks `emergency == True`; sev 5 or rail fracture can be downgraded | **Non-Compliant** | Critical |
| Advisory ML blend: `final = max(floor, a*rule + (1-a)*ML)` | Blend formula lacks floor mechanism: ML can drag down safety scores | **Non-Compliant** | Critical |
| Monotone XGBoost constraints | `XGBClassifier` initialized without `monotone_constraints` | **Non-Compliant** | High |
| Dynamic escalator for live telemetry/weather (capped at +20) | Rail vibration absent from formula; no telemetry/weather escalator | **Non-Compliant** | High |
| Degradation simulator for training labels (Weibull/hazard-based) | Labels generated with ad-hoc threshold rules; no degradation model | **Non-Compliant** | Medium |
| Explainability (SHAP values + rule breakdown) | Rule breakdown exists; no SHAP library import or ML attribution | **Partial** | Medium |
| Ablation script comparing Rule vs ML | No ablation script exists | **Non-Compliant** | Medium |

---

### Section 6: Clustering Guardrails (`ai_engine/clustering.py`)
| Requirement | Current Repository State | Compliance | Risk |
| :--- | :--- | :---: | :---: |
| Baseline DBSCAN (`eps=2.0 km`, `min_samples=1`) | Uses `eps=3.0 km`, `min_samples=1` (single-linkage chaining) | **Compliant** | Low |
| Cluster separately per line group and section | Groups by `["corridor", "section"]` | **Compliant** | Low |
| Cap cluster span (`max_span_km`, default 6 km) | No span cap; chained clusters can span unlimited kilometers | **Non-Compliant** | High |
| Compatibility checks (time windows, deadlines, priority, block type) | Purely spatial clustering; ignores deadlines and priority compatibility | **Non-Compliant** | High |
| Integrated duration calculation (parallel max vs machine serial sum) | Takes max of departmental sums with 4h cap; does not sum shared machines | **Partial** | Medium |

---

### Section 7: Optimizer & Independent Validator (`optimizer/`)
| Requirement | Current Repository State | Compliance | Risk |
| :--- | :--- | :---: | :---: |
| Independent validator (`optimizer/validator.py`) without OR-Tools | File does not exist; no post-solve verification | **Non-Compliant** | Critical |
| CP-SAT interval variables (`NewIntervalVar`, `NoOverlap`) | Uses binary `NewBoolVar(b, w)` on discrete windows; no interval logic | **Non-Compliant** | High |
| 5-minute time grid resolution | Effective 6-minute resolution (units of 0.1 hours * 10) | **Partial** | Low |
| Crew & machine resource constraints with travel times | Equipment capped per window; crew DataFrame accepted but unused | **Non-Compliant** | High |
| LWR temperature window ($t_d - 30^\circ\text{C}$ to $t_d + 10^\circ\text{C}$) | Completely absent; no LWR temperature constraint | **Non-Compliant** | High |
| Suburban peak-hour no-block constraint | Pre-filtered from COA windows (`coa_df["train_density"] != "peak"`) | **Compliant** | Low |
| Setup, teardown, and protection buffers | Generic 0.5h buffer added; no separate setup/teardown/adjacent line buffer | **Partial** | Medium |
| Lexicographic / multi-objective hierarchy in `config/objective.yaml` | Single weighted sum objective; no YAML configuration | **Non-Compliant** | High |
| Infeasibility explanation (slack variables / assumptions) | Prints error and returns empty list; no constraint conflict isolation | **Non-Compliant** | Medium |
| Deterministic solver mode (single-thread option) | Hardcoded `num_search_workers = 4`; non-deterministic across runs | **Non-Compliant** | Medium |
| Gap and status reporting | Returns status and wall time; does not call `BestObjectiveBound()` for gap | **Partial** | Low |

---

### Section 8: Digital Twin & Dynamic Replanner (`realtime/`)
| Requirement | Current Repository State | Compliance | Risk |
| :--- | :--- | :---: | :---: |
| Event-sourced SQLite log with snapshot replay | In-memory `RailwayState` singleton; bounded 100-event FIFO; lost on restart | **Non-Compliant** | High |
| Weather caching with offline fixture fallback | Live fetch only; hangs when offline; no local JSON fixture fallback | **Non-Compliant** | High |
| Rail temperature model ($T_{\text{rail}} = T_{\text{air}} + \Delta_{\text{solar}}$) | Raw air temperature used directly; no rail thermal model | **Non-Compliant** | High |
| Buckling alert relative to destressing temperature $t_d$ | Fixed thresholds ($42^\circ\text{C}$ / $38^\circ\text{C}$); ignores $t_d$ | **Non-Compliant** | High |
| IoT simulator (noise, drift, dropout, fault injection) | Simple uniform random noise; single hardcoded fault at t=15s | **Partial** | Medium |
| Anomaly detector (EWMA / z-score with persistence) | Absolute threshold comparison only (`vibration >= 8.0g`) | **Non-Compliant** | Medium |
| Replanner blast radius & T-1 block freeze | Re-optimizes entire schedule from scratch; no frozen block logic | **Non-Compliant** | High |
| Worker process execution (outside FastAPI event loop) | Solves executed directly in FastAPI async loop, blocking server threads | **Non-Compliant** | High |

---

### Section 9: API Layer (`api/`)
| Requirement | Current Repository State | Compliance | Risk |
| :--- | :--- | :---: | :---: |
| v1 API namespace (`/api/v1`) | Routes mounted directly under `/api/` | **Partial** | Low |
| Async optimization jobs (202 Accepted + `job_id` + WebSocket progress) | Synchronous `POST /api/generate` runs full solve in request thread | **Non-Compliant** | High |
| Validation endpoint (`GET /validate/{schedule_id}`) | Missing | **Non-Compliant** | Critical |
| Role-gated approval (`POST /plans/{id}/approve`) | Missing; no approval state transitions | **Non-Compliant** | High |
| Public train radar (`/trains/radar` with simulated fallback) | Exists under `/api/beta/live-trains` without explicit provenance tag | **Partial** | Medium |
| Role-Based Access Control (RBAC) & JWT authentication | Completely unauthenticated; `CORSMiddleware` with wildcard origins | **Non-Compliant** | High |

---

### Section 10: UI & Sanction Orders (`frontend/`)
| Requirement | Current Repository State | Compliance | Risk |
| :--- | :--- | :---: | :---: |
| Single flagship React cockpit | Main React app functional; Streamlit retained separately | **Compliant** | Low |
| Provenance badges on tasks and blocks | Missing per-item provenance chips | **Non-Compliant** | Medium |
| Solver status, optimality gap, and validator badge | Hardcoded "OPTIMAL" badge; no validator status or gap display | **Non-Compliant** | High |
| Approval workflow UI (DRAFT vs APPROVED) | Missing | **Non-Compliant** | High |
| What-if scenario comparison component | API exists (`/api/scenario`), but no React component renders it | **Non-Compliant** | Medium |
| Server-signed sanction orders with cryptographic QR | Browser-generated jsPDF with unhashed metadata QR; no server signature | **Non-Compliant** | High |
| AI Chatbot grounded with citations & read-only enforcement | LLM receives KPI summary; does not cite task IDs; read-only is preserved | **Partial** | Low |
| Accessible colour-blind safe UI indicators | Standard Red/Yellow/Green color codes only; no icons/striping | **Non-Compliant** | Low |

---

### Section 11: Evaluation, Benchmarks & KPI Standards
| Requirement | Current Repository State | Compliance | Risk |
| :--- | :--- | :---: | :---: |
| Standardized KPI formulas documented in `docs/kpis.md` | Missing; formulas scattered across solver, baseline, and docs | **Non-Compliant** | High |
| 30-scenario statistical evaluation with 95% CI | Missing; no automated benchmarking suite | **Non-Compliant** | High |
| Manual planning simulation baseline | `optimizer/baseline.py` exists as a greedy single-department FIFO solver | **Partial** | Medium |
| Ablation studies (no ML, no clustering, greedy vs CP-SAT) | Missing | **Non-Compliant** | High |

---

## 4. Ranked Gap Remediation Plan

Based on the audit, the gaps are prioritized by operational and academic risk:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PRIORITY 1: CRITICAL                            │
│  1. Create optimizer/validator.py (independent zero-OR-Tools verifier)  │
│  2. Add Safety Floor & max(floor, ...) to ai_engine/prioritizer.py    │
│  3. Model Graph Corridor (CSMT-Kalyan-Igatpuri/Pune, Ghat rules)       │
│  4. Introduce Provenance field (REAL, SYNTHETIC, SIMULATED, LIVE)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        PRIORITY 2: HIGH                                │
│  5. Externalize YAML configurations (scenario, weights, objective)    │
│  6. Implement Pydantic v2 schemas + formal data quality report         │
│  7. Refactor CP-SAT to interval variables + LWR temperature window     │
│  8. Guarded DBSCAN (max_span_km cap, time/priority compatibility)      │
│  9. Event-sourced SQLite log + offline weather fixture cache           │
│ 10. Server-side Ed25519/HMAC signed PDF sanction orders with valid QR  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        PRIORITY 3: MEDIUM                              │
│ 11. Async job queue (202 + job_id) & worker process for solver solves  │
│ 12. Monotone constraints & Weibull degradation simulator for XGBoost   │
│ 13. Benchmarking protocol (30 seeded runs, 95% CI, ablation scripts)   │
│ 14. UI approval workflow view, validator badge, why-this-window panel  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Phase 0 Audit Sign-Off
- **Codebase Modified:** No code files were modified or deleted.
- **Artifacts Generated:** `docs/audit.md`, `docs/ASSUMPTIONS.md`.
- **Validation:** 12/12 non-network core unit tests pass cleanly.
- **Readiness:** System is fully prepared for **Phase 1: Data and Truth**.

