"""
Streamlit Dashboard for AI Block Planning System.

Visualizes optimized maintenance schedules with:
- KPI metric cards (Asset Availability, Block Utilization, Integration Rate)
- Interactive Plotly Gantt charts (weekly/monthly view by corridor)
- Department and corridor filters
- Detailed data tables for blocks and tasks
"""

import os
import sys
import json

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ── Ensure project root is on path ──
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.generator import generate_all
from database.loader import load_data
from ai_engine.prioritizer import compute_criticality_scores
from ai_engine.clustering import cluster_tasks
from optimizer.solver import solve_block_scheduling


# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Block Planning|Indian Railways",
    page_icon="🚂",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    * { font-family: 'Outfit', sans-serif; }

    /* Overall Background and Text */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }

    /* Sidebar Customization */
    [data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Headers */
    h1, h2, h3 {
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }

    /* KPI Cards with Glassmorphism */
    .kpi-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: -100%; width: 50%; height: 100%;
        background: linear-gradient(to right, transparent, rgba(255,255,255,0.03), transparent);
        transform: skewX(-20deg);
        transition: 0.5s;
    }
    .kpi-card:hover::before {
        left: 150%;
    }
    .kpi-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
        border-color: rgba(99, 102, 241, 0.3);
    }
    .kpi-value {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
        line-height: 1.1;
    }
    .kpi-value.green {
        background: linear-gradient(135deg, #34d399, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-value.amber {
        background: linear-gradient(135deg, #fbbf24, #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-value.purple {
        background: linear-gradient(135deg, #a78bfa, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .kpi-label {
        font-size: 0.95rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600;
    }
    .kpi-sub {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.5rem;
    }

    /* Premium Header */
    .header-container {
        background: radial-gradient(circle at 10% 20%, rgba(30, 41, 59, 1) 0%, rgba(15, 23, 42, 1) 90%);
        border-radius: 24px;
        padding: 3.5rem 3rem;
        margin-bottom: 2.5rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255,255,255,0.1);
        position: relative;
        overflow: hidden;
    }
    .header-container::after {
        content: '';
        position: absolute;
        top: -50%; right: -20%; width: 60%; height: 200%;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
        pointer-events: none;
    }
    .header-title {
        font-size: 2.8rem;
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }
    .header-subtitle {
        font-size: 1.15rem;
        color: #94a3b8;
        margin-top: 1.2rem;
        max-width: 800px;
        line-height: 1.6;
        font-weight: 300;
    }

    /* Section titles */
    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #f1f5f9;
        margin: 2.5rem 0 1.5rem 0;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Fix table readability */
    .stDataFrame { 
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem; 
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    
    /* Metric container */
    [data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# ─── Pipeline Execution ──────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def run_full_pipeline():
    """Run the full pipeline and cache results."""
    generate_all()
    data = load_data()
    scored = compute_criticality_scores(data["all_tasks"])
    blocks_df, tasks_clustered = cluster_tasks(scored)
    schedule_df, stats = solve_block_scheduling(blocks_df, data["coa"])
    return schedule_df, tasks_clustered, blocks_df, stats, data["coa"]


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🚂 AI Block Planning")
    st.markdown("**Indian Railways PS-26027**")
    st.markdown("---")

    if st.button("🔄 Run / Refresh Pipeline", use_container_width=True, type="primary"):
        st.cache_data.clear()

    st.markdown("---")
    st.markdown("### Filters")

    dept_filter = st.multiselect(
        "Department",
        ["Engineering", "S&T", "Electrical"],
        default=["Engineering", "S&T", "Electrical"],
    )

    corridor_filter = st.selectbox(
        "Corridor",
        ["All Corridors", "Delhi-Kanpur", "Mumbai-Pune", "Chennai-Vijayawada", "Howrah-Dhanbad"],
    )

    severity_filter = st.slider("Min Severity", 1, 5, 1)

    view_mode = st.radio("Schedule View", ["Weekly", "Monthly"], horizontal=True)

    st.markdown("---")
    st.markdown(
        "<small style='color: #607d8b;'>Built with OR-Tools, XGBoost,<br>"
        "DBSCAN, FastAPI & Streamlit</small>",
        unsafe_allow_html=True,
    )


# ─── Main Content ────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="header-container">
    <p class="header-title">🚂 AI-Powered Automatic Block Planning System</p>
    <p class="header-subtitle">
        Integrated maintenance scheduling for Engineering, Signalling & Traction departments
        — maximizing track availability through AI-driven optimization
    </p>
</div>
""", unsafe_allow_html=True)

# Run pipeline
with st.spinner("⚙️ Running optimization pipeline..."):
    try:
        schedule_df, tasks_df, blocks_df, stats, coa_df = run_full_pipeline()
        pipeline_ok = True
    except Exception as e:
        st.error(f"Pipeline error: {e}")
        pipeline_ok = False

if not pipeline_ok:
    st.stop()


# ─── KPI Cards ────────────────────────────────────────────────────────────────

st.markdown('<p class="section-title">📊 Key Performance Indicators</p>', unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Asset Availability</div>
        <div class="kpi-value green">{stats['asset_availability_pct']:.1f}%</div>
        <div class="kpi-sub">Track-hours available for operations</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Block Utilization</div>
        <div class="kpi-value">{stats['block_utilization_pct']:.1f}%</div>
        <div class="kpi-sub">Window time used for maintenance</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Schedule Rate</div>
        <div class="kpi-value amber">{stats['schedule_rate_pct']:.0f}%</div>
        <div class="kpi-sub">{stats['blocks_scheduled']}/{stats['total_blocks']} blocks scheduled</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Integration Rate</div>
        <div class="kpi-value purple">{stats['integration_rate_pct']:.1f}%</div>
        <div class="kpi-sub">{stats['multi_dept_blocks_scheduled']} multi-dept blocks</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Secondary KPIs
s1, s2, s3, s4 = st.columns(4)
s1.metric("🔧 Tasks Scheduled", f"{stats['tasks_scheduled']}/{stats['total_tasks']}")
s2.metric("⏱️ Total Hours Used", f"{stats['total_scheduled_hours']:.0f} hrs")
s3.metric("🧮 Solve Time", f"{stats['solve_time_seconds']:.2f}s")
s4.metric("🟢 Solver Status", stats["solver_status"])


# ─── Gantt Chart ──────────────────────────────────────────────────────────────

st.markdown('<p class="section-title">📅 Maintenance Schedule — Gantt Chart</p>', unsafe_allow_html=True)

if len(schedule_df) > 0:
    # Apply filters
    gantt_data = schedule_df.copy()

    if corridor_filter != "All Corridors":
        gantt_data = gantt_data[gantt_data["corridor"] == corridor_filter]

    if dept_filter:
        mask = gantt_data["departments"].apply(
            lambda d: any(dept in d for dept in dept_filter)
        )
        gantt_data = gantt_data[mask]

    if len(gantt_data) > 0:
        # Map day of week to ordinal for proper ordering
        day_order = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        gantt_data["day_order"] = gantt_data["day_of_week"].map(day_order)
        gantt_data = gantt_data.sort_values(["day_order", "section", "block_start_hour"])

        # Create a synthetic date for Gantt visualization
        from datetime import datetime, timedelta
        base_date = datetime(2026, 9, 7)  # Current week Monday
        gantt_data["start_dt"] = gantt_data.apply(
            lambda r: base_date + timedelta(days=day_order.get(r["day_of_week"], 0),
                                             hours=r["block_start_hour"]),
            axis=1,
        )
        gantt_data["end_dt"] = gantt_data.apply(
            lambda r: base_date + timedelta(days=day_order.get(r["day_of_week"], 0),
                                             hours=r["block_end_hour"]),
            axis=1,
        )

        # Determine color column
        gantt_data["primary_dept"] = gantt_data["departments"].apply(
            lambda d: d.split(",")[0].strip()
        )

        dept_colors = {
            "Engineering": "#3b82f6",
            "S&T": "#10b981",
            "Electrical": "#8b5cf6",
        }

        fig = px.timeline(
            gantt_data,
            x_start="start_dt",
            x_end="end_dt",
            y="section",
            color="primary_dept",
            color_discrete_map=dept_colors,
            hover_data={
                "block_id": True,
                "departments": True,
                "total_hours": True,
                "max_criticality": True,
                "task_count": True,
                "day_of_week": True,
                "start_dt": False,
                "end_dt": False,
                "primary_dept": False,
            },
            labels={
                "section": "Track Section",
                "primary_dept": "Department",
                "start_dt": "Start",
                "end_dt": "End",
            },
            title="",
        )

        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit", color="#94a3b8"),
            height=500,
            xaxis=dict(
                title="",
                gridcolor="rgba(100,180,255,0.1)",
                dtick=86400000,  # 1 day in ms
                tickformat="%a %H:%M",
            ),
            yaxis=dict(
                title="",
                gridcolor="rgba(100,180,255,0.05)",
                autorange="reversed",
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=12),
            ),
            margin=dict(l=0, r=0, t=40, b=0),
        )

        fig.update_traces(
            marker_line_color="rgba(255,255,255,0.3)",
            marker_line_width=0.5,
            opacity=0.85,
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No blocks match the current filters.")
else:
    st.warning("No blocks were scheduled. Try adjusting constraints.")


# ─── Criticality Distribution ─────────────────────────────────────────────────

st.markdown('<p class="section-title">📈 Task Criticality Analysis</p>', unsafe_allow_html=True)

c1, c2 = st.columns(2)

with c1:
    # Criticality distribution by department
    if "criticality_index" in tasks_df.columns:
        filtered_tasks = tasks_df.copy()
        if dept_filter:
            filtered_tasks = filtered_tasks[filtered_tasks["department"].isin(dept_filter)]

        fig_hist = px.histogram(
            filtered_tasks,
            x="criticality_index",
            color="department",
            nbins=25,
            color_discrete_map={
                "Engineering": "#3b82f6",
                "S&T": "#10b981",
                "Electrical": "#8b5cf6",
            },
            labels={"criticality_index": "Criticality Index", "department": "Department"},
            title="Criticality Index Distribution",
            barmode="overlay",
        )
        fig_hist.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit", color="#94a3b8"),
            height=350,
            margin=dict(l=0, r=0, t=40, b=0),
        )
        fig_hist.update_traces(opacity=0.75)
        st.plotly_chart(fig_hist, use_container_width=True)

with c2:
    # Priority tier pie chart
    if "priority_tier" in tasks_df.columns:
        tier_counts = tasks_df["priority_tier"].value_counts().reset_index()
        tier_counts.columns = ["Tier", "Count"]

        fig_pie = px.pie(
            tier_counts,
            values="Count",
            names="Tier",
            color="Tier",
            color_discrete_map={
                "Critical": "#ef4444",
                "High": "#f59e0b",
                "Medium": "#3b82f6",
                "Low": "#10b981",
            },
            title="Priority Tier Breakdown",
            hole=0.45,
        )
        fig_pie.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Outfit", color="#94a3b8"),
            height=350,
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_pie, use_container_width=True)


# ─── Corridor Heatmap ─────────────────────────────────────────────────────────

st.markdown('<p class="section-title">🗺️ Corridor Block Density</p>', unsafe_allow_html=True)

if len(schedule_df) > 0:
    day_order_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    heatmap_data = schedule_df.groupby(["section", "day_of_week"]).agg(
        block_count=("block_id", "count"),
        total_hours=("total_hours", "sum"),
    ).reset_index()

    heatmap_pivot = heatmap_data.pivot_table(
        index="section",
        columns="day_of_week",
        values="total_hours",
        fill_value=0,
    )
    # Reorder columns
    cols = [d for d in day_order_list if d in heatmap_pivot.columns]
    heatmap_pivot = heatmap_pivot[cols]

    fig_heat = px.imshow(
        heatmap_pivot.values,
        labels=dict(x="Day of Week", y="Section", color="Hours"),
        x=cols,
        y=heatmap_pivot.index.tolist(),
        color_continuous_scale="Blues",
        aspect="auto",
        title="",
    )
    fig_heat.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Outfit", color="#94a3b8"),
        height=400,
        margin=dict(l=0, r=0, t=20, b=0),
    )
    st.plotly_chart(fig_heat, use_container_width=True)


# ─── Data Tables ──────────────────────────────────────────────────────────────

st.markdown('<p class="section-title">📋 Detailed Data</p>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🗓️ Scheduled Blocks", "🔧 All Tasks", "🧩 Integrated Blocks"])

with tab1:
    if len(schedule_df) > 0:
        display_cols = [
            "block_id", "corridor", "section", "day_of_week",
            "block_start_hour", "block_end_hour", "total_hours",
            "departments", "max_criticality", "task_count",
        ]
        show_df = schedule_df[display_cols].copy()
        show_df = show_df.sort_values(["corridor", "day_of_week", "block_start_hour"])
        st.dataframe(show_df, use_container_width=True, height=400)
    else:
        st.info("No scheduled blocks to display.")

with tab2:
    display_task_cols = [
        "task_id", "department", "corridor", "section", "chainage_km",
        "defect_type", "severity", "days_overdue", "required_hours",
    ]
    if "criticality_index" in tasks_df.columns:
        display_task_cols.append("criticality_index")
    if "priority_tier" in tasks_df.columns:
        display_task_cols.append("priority_tier")
    if "block_id" in tasks_df.columns:
        display_task_cols.append("block_id")

    filtered = tasks_df.copy()
    if dept_filter:
        filtered = filtered[filtered["department"].isin(dept_filter)]
    filtered = filtered[filtered["severity"] >= severity_filter]

    available_cols = [c for c in display_task_cols if c in filtered.columns]
    show_tasks = filtered[available_cols].sort_values(
        "criticality_index" if "criticality_index" in filtered.columns else "severity",
        ascending=False,
    )
    st.dataframe(show_tasks, use_container_width=True, height=400)

with tab3:
    if len(blocks_df) > 0:
        block_display = blocks_df[[
            "block_id", "corridor", "section", "center_km",
            "km_range_start", "km_range_end", "departments",
            "total_hours", "max_criticality", "task_count", "is_multi_department",
        ]].sort_values("max_criticality", ascending=False)
        st.dataframe(block_display, use_container_width=True, height=400)
    else:
        st.info("No blocks to display.")


# ─── Footer ──────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#607d8b; font-size:0.8rem;'>"
    "AI-Powered Automatic Block Planning System · Indian Railways PS-26027 · "
    "Capstone Project 2026"
    "</div>",
    unsafe_allow_html=True,
)
