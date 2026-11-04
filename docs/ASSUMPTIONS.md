# Engineering Assumptions & Domain Mappings
**AI-Powered Automatic Block Planning System (Indian Railways PS-26027)**

---

## 1. Operating Rules & Core Tenets

1. **Decision-Support Boundary:**
   The software is an advisory decision-support system for Railway Section Controllers, Branch Officers (DEN, DSTE, DEE/TRD), and the DRM. It does not replace fail-safe track circuit interlocking, Kavach (ATP), or block working rules. The only safety claim permitted: **zero violations of modeled hard constraints**, verified by an independent rule engine.

2. **Data Provenance Hierarchy:**
   Every record processed or transmitted by the system must carry an unambiguous provenance flag:
   - `REAL`: Ingested from verified official Indian Railways production feeds or static exports.
   - `SYNTHETIC`: Generated via seeded parameter distributions (e.g., synthetic TMS defect logs).
   - `SIMULATED`: Dynamically calculated via physics/kinematic models (e.g., train radar positions interpolated from timetables).
   - `LIVE`: Polled in real-time from active external sensor/weather APIs (e.g., Open-Meteo).

3. **No Unmeasured Numbers:**
   All metrics published in documentation, API payloads, or dashboards must originate from automated benchmark runs (`benchmarks/results/*.json`). No hardcoded or speculative figures are permitted.

---

## 2. Corridor Model & Topology Assumptions

1. **Primary Operational Corridor:**
   - **Route:** Mumbai CSMT – Kalyan – Kasara – Igatpuri (Central Railway, Mumbai Division).
   - **Track Layout:**
     - **CSMT to Kalyan (KM 0.0 to KM 53.9):** Quadruple track territory comprising Up/Down Slow lines (suburban locals) and Up/Down Fast lines (long-distance express and freight).
     - **Kalyan Junction (KM 53.9):** Major operational divergence point. The North-East route proceeds towards Kasara and Igatpuri; the South-East route proceeds towards Karjat, Lonavala, and Pune.
     - **Kalyan to Kasara (KM 53.9 to KM 120.8):** Double-line electrified section.
     - **Kasara to Igatpuri (KM 120.8 to KM 137.0 - Thal Ghat):** High-gradient ghat section (1 in 37 gradient). Governed by strict operational rules:
       - Mandatory banking locomotive attachment at Kasara for Up trains.
       - Severe permanent speed restrictions (PSR 30–40 km/h).
       - Catch sidings and specialized brake testing stops.
       - Maintenance blocks severely constrict division throughput.
   - **Optional Branch:** Karjat – Lonavala – Pune (Bhor Ghat, KM 100 to 192).

2. **Linear Distance & Chainage:**
   Chainage markers (KM) are non-overlapping per section identifier. A graph structure with nodes (`Station`, `Junction`, `BlockHut`) and directed multi-edges (`TrackSegment` with `line_id`: `UP_SLOW`, `DN_SLOW`, `UP_FAST`, `DN_FAST`) maps physical track infrastructure accurately.

---

## 3. Planning Horizons & Governance (Indian Railways Rolling Block Plan)

1. **26-Week Strategic Roadmap:**
   - Long-range corridor rehabilitation, major bridge rebuilding, track renewals (CTR/TSR), and overhead equipment (OHE) renewal.
   - Reviewed bi-monthly at Principal Chief Operations Manager (PCOM) / Principal Chief Engineer (PCE) level.

2. **4-Week Rolling Plan:**
   - Machine deployment schedule (Track tampers, ballast cleaners, dynamic track stabilizers, tower wagons).
   - Re-evaluated and rolled forward every week.

3. **Weekly Operational Plan:**
   - Finalized by Divisional Branch Officers (Sr.DEN / Sr.DSTE / Sr.DEE TRD) and sanctioned by Divisional Railway Manager (DRM) by Saturday.
   - Defines agreed daily block windows for the upcoming week.

4. **Next-Day Freeze (T-1):**
   - The agreed plan for day $T$ is frozen by 18:00 hours on day $T-1$.
   - Blocks inside the T-1 window cannot be relocated or canceled without Sr.DOM sanction and an explicit reason code.

5. **Emergent / Incident Blocks:**
   - Emergency rail fractures, OHE line snaps, or signal track circuit failures occurring on day $T$.
   - Handled via dynamic replanning with minimal displacement of pre-scheduled work.

---

## 4. Maintenance & Engineering Rules

1. **Long Welded Rail (LWR / CWR) Maintenance Temperature Windows:**
   - Per Indian Railways Permanent Way Manual (IRPWM), regular track maintenance (lifting, packing, slewing, tamping) in LWR/CWR territory is permitted only when rail temperature $T_{\text{rail}}$ is within the designated range:
     $$t_d - 30^\circ\text{C} \le T_{\text{rail}} \le t_d + 10^\circ\text{C}$$
     *(where $t_d$ is the rail destressing temperature, typically $40^\circ\text{C}$ to $45^\circ\text{C}$ for Central Railway).*
   - When $T_{\text{rail}} > t_d + 20^\circ\text{C}$ to $t_d + 25^\circ\text{C}$, hot-weather patrolling is instituted and maintenance is prohibited to prevent track buckling.
   - In cold weather ($T_{\text{rail}} < t_d - 30^\circ\text{C}$), cold-weather patrolling is deployed to detect rail and weld fractures.

2. **Rail Temperature Modeling:**
   - Open-Meteo returns ambient air temperature ($T_{\text{air}}$), solar radiation ($G_{\text{solar}}$), and wind speed ($v_{\text{wind}}$).
   - Modeled Rail Surface Temperature:
     $$T_{\text{rail}} = T_{\text{air}} + \Delta T_{\text{solar}}$$
     *(where $\Delta T_{\text{solar}} \approx 15^\circ\text{C}$ to $20^\circ\text{C}$ during peak daytime clear sky, diminishing with cloud cover and wind speed).*
   - Marked explicitly as `SIMULATED` with an uncertainty margin ($\pm 3^\circ\text{C}$).

3. **Block Types & Durations:**
   - **Traffic Block:** Halting train movements on a track segment.
   - **Power Block:** De-energizing the 25 kV AC OHE for overhead traction work. Requires isolation of adjacent tracks where clearances are below prescribed schedules.
   - **Signalling Disconnection:** Disconnection of points, track circuits, or axle counters. Requires formal disconnection memo (T/351) before work and reconnection memo on completion.
   - **Mega Block:** Continuous traffic block exceeding 4 hours. Requires Zonal/Railway Board notification and Advance Reservation Period (ARP) train regulation planning.
   - **Standard Daily Maintenance Block:** 1.5 to 3.5 hours.

4. **Multi-Department Shadow Blocks:**
   - When Engineering, S&T, and TRD tasks overlap spatially within a cluster ($\le 6.0\text{ km}$) on the same line segment, they are combined into an Integrated Block.
   - Work conducted simultaneously by independent gangs on distinct kilometers costs $\max(\text{durations})$.
   - Work sharing machinery or sequential track access costs $\sum(\text{durations})$.

