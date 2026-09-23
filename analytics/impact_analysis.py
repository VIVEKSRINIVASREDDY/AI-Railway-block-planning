"""
Cascading Impact Analysis Engine.

Determines the blast radius of a disruption (e.g., Train Delay, Weather).
Maps the failure from the root cause down to the specific maintenance crews
and tasks affected.
"""

import random
from typing import Dict, Any
from realtime.state_manager import RailwayEvent, digital_twin_state

def calculate_impact(event: RailwayEvent) -> Dict[str, Any]:
    """
    Given an event, calculate the cascading impact graph.
    Returns a graph dictionary for the UI to render.
    """
    
    # 1. Identify Root Cause
    root_node = {
        "id": event.event_id,
        "label": f"{event.event_type} ({event.severity})",
        "type": "event"
    }
    
    nodes = [root_node]
    edges = []
    
    affected_blocks = []
    affected_tasks = []
    affected_crews = []
    
    # 2. Map to Train / Track Section
    if event.event_type == "TRAIN_DELAYED":
        for t_id in event.affected_trains:
            t_node = {"id": t_id, "label": f"Train {t_id}", "type": "train"}
            nodes.append(t_node)
            edges.append({"source": root_node["id"], "target": t_id})
            
            # Identify blocks scheduled in this train's path (Simulation)
            # For this prototype, we probabilistically select 1-2 blocks to be affected
            if digital_twin_state.current_plan:
                all_blocks = digital_twin_state.current_plan.schedule_snapshot
                if all_blocks:
                    # Pick a random block to be in conflict
                    conflict_block = random.choice(all_blocks)
                    b_id = conflict_block.get("id", f"BLK-{random.randint(100,999)}")
                    b_node = {"id": b_id, "label": f"Block {b_id}", "type": "block"}
                    
                    nodes.append(b_node)
                    edges.append({"source": t_id, "target": b_id})
                    affected_blocks.append(b_id)
                    
                    # Tasks in this block
                    t_tasks = conflict_block.get("tasks", [])
                    if t_tasks:
                        task_id = str(t_tasks[0])
                        task_node = {"id": f"TASK-{task_id}", "label": f"Task {task_id}", "type": "task"}
                        nodes.append(task_node)
                        edges.append({"source": b_id, "target": f"TASK-{task_id}"})
                        affected_tasks.append(task_id)
                        
                        # Crew
                        crew_id = conflict_block.get("crew_id", f"CREW-E-{random.randint(10,99)}")
                        crew_node = {"id": crew_id, "label": f"Crew {crew_id}", "type": "crew"}
                        nodes.append(crew_node)
                        edges.append({"source": f"TASK-{task_id}", "target": crew_id})
                        affected_crews.append(crew_id)
                        
    elif event.event_type == "WEATHER_ALERT":
        # Weather affects an entire track section, meaning multiple blocks
        section_node = {"id": "SEC-MUM-PUN", "label": "Mumbai-Pune Section", "type": "section"}
        nodes.append(section_node)
        edges.append({"source": root_node["id"], "target": section_node["id"]})
        
        # Add a couple of dummy blocks affected by weather
        affected_blocks.extend(["BLK-110", "BLK-214"])
        for b in affected_blocks:
            nodes.append({"id": b, "label": f"Block {b}", "type": "block"})
            edges.append({"source": section_node["id"], "target": b})

    # Compile result
    graph = {
        "nodes": nodes,
        "edges": edges,
        "affected_blocks": affected_blocks,
        "affected_tasks": affected_tasks,
        "affected_crews": affected_crews,
        "summary": f"Event cascaded to affect {len(affected_blocks)} block(s) and {len(affected_crews)} crew(s)."
    }
    
    return graph
