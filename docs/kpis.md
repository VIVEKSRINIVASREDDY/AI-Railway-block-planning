# Indian Railways Block Planning Key Performance Indicators (KPIs)
**Version:** 1.0 (SPEC Compliance)  
**Authority:** Operations Research Engine & Decision Support Framework

This document serves as the **Single Source of Truth** for all KPI formulas used across the backend solver, REST endpoints (`/api/v1/kpis`), reports, and user interfaces.

---

## 1. Primary Operational Metrics

### 1.1 Asset Availability (%)
- **Definition:** The percentage of total scheduled corridor asset-hours that remain in service and are not incapacitated by unaddressed maintenance defects or speed restrictions.
- **Formula:**
  $$\text{Asset Availability \%} = \left( 1 - \frac{\sum_{t \in \text{Unscheduled Tasks}} \text{Duration}_t \times \text{Track Factor}}{\text{Total Horizon Track Hours}} \right) \times 100$$
- **Target Threshold:** $\ge 88.0\%$ (Strict Indian Railways Golden Rule)
- **Dashboard Display:** "Asset Availability" (Target > 88% Pass)

### 1.2 Block Utilization (%)
- **Definition:** The ratio of productive maintenance block hours actually scheduled compared to total available non-peak corridor traffic window hours.
- **Formula:**
  $$\text{Block Utilization \%} = \left( \frac{\sum_{b \in \text{Scheduled Blocks}} \text{Duration}_b}{\sum_{w \in \text{Available Windows}} \text{Duration}_w} \right) \times 100$$
- **Target Threshold:** $35.0\% - 50.0\%$ (Peak-traffic excluded windows)

### 1.3 Joint Block Integration Rate (%)
- **Definition:** The proportion of maintenance blocks that integrate multiple departments (Engineering, S&T, Electrical/TRD) into a single shadow possession, avoiding separate corridor shutdowns.
- **Formula:**
  $$\text{Joint Block Rate \%} = \left( \frac{\text{Count of Multi-Department Blocks Scheduled}}{\text{Total Blocks Scheduled}} \right) \times 100$$
- **Target Threshold:** $\ge 70.0\%$

### 1.4 Task Integration Rate (%)
- **Definition:** The percentage of individual maintenance tasks executed within a joint multi-department block rather than isolated departmental possessions.
- **Formula:**
  $$\text{Task Integration Rate \%} = \left( \frac{\sum \text{Tasks in Multi-Dept Blocks}}{\text{Total Tasks Scheduled}} \right) \times 100$$

### 1.5 Schedule Completion Rate (%)
- **Definition:** Total candidate blocks successfully allocated a conflict-free window within the planning horizon.
- **Formula:**
  $$\text{Schedule Rate \%} = \left( \frac{\text{Blocks Scheduled}}{\text{Total Candidate Blocks Formed}} \right) \times 100$$

---

## 2. Dynamic Resilience & Stability Metrics

### 2.1 Schedule Resilience Score (0–100)
- **Initial Baseline:** `N/A` (Evaluated dynamically upon disruption injection)
- **Formula:**
  $$\text{Resilience} = 100 - \left( 0.4 \times \Delta_{\text{delay}} + 0.3 \times \text{Displaced Blocks} + 0.3 \times \text{Replan Latency Penalty} \right)$$
- When no disruption has occurred, displays `N/A (Pending Incident)`.

### 2.2 Schedule Stability (%)
- **Formula:**
  $$\text{Stability \%} = \left( \frac{\text{Blocks Unmoved}}{\text{Total Active Blocks}} \right) \times 100$$
