"""
Spatial Clustering Module.

Groups maintenance tasks from different departments that occur in the same
geographic section (KM range) into Integrated Blocks using DBSCAN clustering.

Integrated Blocks allow multiple departments (Engineering, S&T, Electrical)
to share a single maintenance window, reducing total corridor downtime.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN


@dataclass
class IntegratedBlock:
    """A group of spatially co-located tasks forming an integrated maintenance block."""
    block_id: str
    cluster_label: int
    corridor: str
    section: str
    center_km: float
    km_range_start: float
    km_range_end: float
    task_ids: list = field(default_factory=list)
    departments: list = field(default_factory=list)
    total_hours: float = 0.0
    max_criticality: float = 0.0
    avg_criticality: float = 0.0
    task_count: int = 0
    is_multi_department: bool = False
    required_equipment: list = field(default_factory=list)
    has_mandatory: bool = False
    has_emergency: bool = False

    def to_dict(self) -> dict:
        return {
            "block_id": self.block_id,
            "cluster_label": self.cluster_label,
            "corridor": self.corridor,
            "section": self.section,
            "center_km": self.center_km,
            "km_range_start": self.km_range_start,
            "km_range_end": self.km_range_end,
            "task_ids": ",".join(self.task_ids),
            "departments": ",".join(sorted(set(self.departments))),
            "total_hours": self.total_hours,
            "max_criticality": self.max_criticality,
            "avg_criticality": self.avg_criticality,
            "task_count": self.task_count,
            "is_multi_department": self.is_multi_department,
            "required_equipment": ",".join(self.required_equipment),
            "has_mandatory": self.has_mandatory,
            "has_emergency": self.has_emergency,
        }


def cluster_tasks(
    tasks_df: pd.DataFrame,
    eps_km: float = 3.0,
    min_samples: int = 1,
) -> tuple:
    """
    Cluster maintenance tasks spatially using DBSCAN on chainage_km.

    Clustering is performed per (corridor, section) pair to ensure tasks
    are only grouped within the same track section.

    Args:
        tasks_df: Scored task DataFrame with chainage_km, criticality_index, etc.
        eps_km: Maximum distance (in km) between tasks to be in the same cluster.
        min_samples: Minimum tasks to form a cluster (default 1 = no noise).

    Returns:
        (blocks_df, tasks_with_clusters):
          - blocks_df: DataFrame of IntegratedBlock summaries
          - tasks_with_clusters: Original tasks with added cluster_id and block_id
    """
    print("=" * 60)
    print("  AI Block Planning - Spatial Clustering (DBSCAN)")
    print("=" * 60)
    print(f"\n  Parameters: eps={eps_km} km, min_samples={min_samples}")

    result_tasks = tasks_df.copy()
    result_tasks["cluster_id"] = -1
    result_tasks["block_id"] = ""

    blocks = []
    global_block_id = 0

    # Group by corridor and section for localized clustering
    grouped = tasks_df.groupby(["corridor", "section"])

    for (corridor, section), group in grouped:
        if len(group) < 1:
            continue

        # DBSCAN on 1D chainage
        X = group[["chainage_km"]].values
        clustering = DBSCAN(eps=eps_km, min_samples=min_samples, metric="euclidean")
        labels = clustering.fit_predict(X)

        # Update cluster assignments in result
        for idx, label in zip(group.index, labels):
            result_tasks.at[idx, "cluster_id"] = label

        # Build IntegratedBlock for each cluster
        unique_labels = set(labels)
        for label in unique_labels:
            if label == -1:
                # Noise points become singleton blocks
                noise_mask = labels == label
                noise_indices = group.index[noise_mask]
                for ni in noise_indices:
                    global_block_id += 1
                    row = tasks_df.loc[ni]
                    block = IntegratedBlock(
                        block_id=f"BLK-{global_block_id:04d}",
                        cluster_label=-1,
                        corridor=corridor,
                        section=section,
                        center_km=row["chainage_km"],
                        km_range_start=row["chainage_km"],
                        km_range_end=row["chainage_km"],
                        task_ids=[row["task_id"]],
                        departments=[row["department"]],
                        total_hours=row["estimated_duration"],
                        max_criticality=row.get("criticality_index", 0),
                        avg_criticality=row.get("criticality_index", 0),
                        task_count=1,
                        is_multi_department=False,
                        required_equipment=[row["required_equipment"]] if row["required_equipment"] != "None" else [],
                        has_mandatory=row["mandatory"],
                        has_emergency=row.get("emergency", False),
                    )
                    blocks.append(block)
                    result_tasks.at[ni, "block_id"] = block.block_id
                continue

            # Clustered tasks
            cluster_mask = labels == label
            cluster_indices = group.index[cluster_mask]
            cluster_data = tasks_df.loc[cluster_indices]

            global_block_id += 1
            km_values = cluster_data["chainage_km"].values
            ci_values = cluster_data.get("criticality_index", pd.Series([0] * len(cluster_data))).values
            departments = cluster_data["department"].unique().tolist()

            # Calculate total_hours assuming departments work concurrently,
            # but tasks within the same department are sequential
            dept_hours = cluster_data.groupby("department")["estimated_duration"].sum()
            block_hours = float(dept_hours.max())
            # Cap block duration so integrated blocks fit in typical corridor windows
            block_hours = min(block_hours, 4.0)

            block = IntegratedBlock(
                block_id=f"BLK-{global_block_id:04d}",
                cluster_label=label,
                corridor=corridor,
                section=section,
                center_km=round(float(np.mean(km_values)), 1),
                km_range_start=round(float(np.min(km_values)), 1),
                km_range_end=round(float(np.max(km_values)), 1),
                task_ids=cluster_data["task_id"].tolist(),
                departments=departments,
                total_hours=round(block_hours, 1),
                max_criticality=round(float(np.max(ci_values)), 2),
                avg_criticality=round(float(np.mean(ci_values)), 2),
                task_count=len(cluster_data),
                is_multi_department=len(departments) > 1,
                required_equipment=[e for e in cluster_data["required_equipment"].unique() if e != "None"],
                has_mandatory=cluster_data["mandatory"].any(),
                has_emergency=cluster_data.get("emergency", pd.Series([False])).any(),
            )
            blocks.append(block)

            # Tag tasks
            for idx in cluster_indices:
                result_tasks.at[idx, "block_id"] = block.block_id

    # Convert to DataFrame
    blocks_df = pd.DataFrame([b.to_dict() for b in blocks])

    # Summary statistics
    total_blocks = len(blocks_df)
    multi_dept = blocks_df["is_multi_department"].sum() if len(blocks_df) > 0 else 0
    avg_tasks = blocks_df["task_count"].mean() if len(blocks_df) > 0 else 0

    print(f"\n  Clustering Results:")
    print(f"    Total blocks formed:          {total_blocks}")
    print(f"    Multi-department (integrated): {multi_dept} ({multi_dept/max(total_blocks,1)*100:.0f}%)")
    print(f"    Avg tasks per block:           {avg_tasks:.1f}")
    print(f"    Total tasks clustered:         {len(result_tasks)}")

    if len(blocks_df) > 0:
        dept_dist = {}
        for _, row in blocks_df.iterrows():
            for d in row["departments"].split(","):
                dept_dist[d.strip()] = dept_dist.get(d.strip(), 0) + 1
        print(f"\n  Department coverage in blocks:")
        for dept, count in sorted(dept_dist.items()):
            print(f"    {dept:15s}: {count} blocks")

    print(f"{'-' * 60}\n")

    return blocks_df, result_tasks


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database.loader import load_data
    from ai_engine.prioritizer import compute_criticality_scores

    data = load_data()
    scored = compute_criticality_scores(data["all_tasks"])
    blocks_df, tasks_clustered = cluster_tasks(scored)
    print("\nSample Integrated Blocks:")
    print(blocks_df.head(15).to_string())
