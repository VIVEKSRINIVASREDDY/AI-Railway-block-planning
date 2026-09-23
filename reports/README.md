# Project Reports & Documentation Repository

This directory serves as the centralized archive for all project documents, reports, evaluation summaries, and PDF exports for the **AI-Driven Railway Maintenance Block Planning System** (Smart India Hackathon 2026 - Problem Statement SIH26027).

---

## 📁 Directory Contents

| Document | Type | Description |
| :--- | :--- | :--- |
| **`AI_Railway_Block_Planning_SIH26027_Project_Brief.pdf`** | PDF Report | Official project brief, architecture overview, algorithmic breakdown (OR-Tools, MILP, Q-Learning, Isolation Forest), and performance KPIs for evaluation. |
| **`AI_Railway_Block_Planning_SIH26027_Project_Brief.docx`** | Word Doc | Editable comprehensive technical brief formatted for submission and review. |
| **`AI_Railway_Block_Planning_SIH26027_Project_Brief_v2.docx`** | Word Doc | Revised edition of the project brief document. |
| **`project_brief.html`** | HTML Report | Print-ready, styled HTML template used by the automated document generation pipeline. |

---

## 🚀 Generating & Updating Reports

To regenerate or update the project brief PDF and Word documents automatically:

```bash
python scripts/generate_docs.py
```

This automated script compiles the HTML presentation and leverages headless browser printing to generate pixel-perfect PDF and Word reports directly into this `reports/` directory.

---

## 📊 Exported Dashboard Reports

When running the web dashboard (`http://localhost:5173` or `main.py`), users can export:
- **Daily Block Clearance Orders (PDF)**: Includes QR verification codes, department sign-offs, and pre-block safety checklists.
- **Optimized Block Schedules (CSV/Excel)**: Complete breakdown of section assignments, conflict resolutions, and corridor windows.
