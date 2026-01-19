#!/usr/bin/env python3
"""
Wukong Runtime CLI - Command line interface for Wukong 2.0 Runtime

Usage:
    python3 ~/.wukong/runtime/cli.py analyze "修复登录bug"
    python3 ~/.wukong/runtime/cli.py create --track fix "修复登录bug"
    python3 ~/.wukong/runtime/cli.py status
    python3 ~/.wukong/runtime/cli.py progress
    python3 ~/.wukong/runtime/cli.py next
    python3 ~/.wukong/runtime/cli.py complete <node_id> --summary "..."
    python3 ~/.wukong/runtime/cli.py fail <node_id> --reason "..."
    python3 ~/.wukong/runtime/cli.py abort
    python3 ~/.wukong/runtime/cli.py resume
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
script_dir = Path(__file__).parent.resolve()
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from event_bus import EventBus
from state_manager import StateManager
from scheduler import Scheduler
from artifact_manager import ArtifactManager
from anchor_manager import AnchorManager
from metrics import MetricsCollector, get_default_collector
from health_monitor import HealthMonitor, HealthStatus
from visualizer import Visualizer, get_default_visualizer


# Default paths
DEFAULT_WUKONG_DIR = Path.home() / ".wukong"
DEFAULT_STATE_FILE = DEFAULT_WUKONG_DIR / "state.json"
DEFAULT_EVENTS_FILE = DEFAULT_WUKONG_DIR / "events.jsonl"
DEFAULT_TASKGRAPH_FILE = DEFAULT_WUKONG_DIR / "taskgraph.json"
DEFAULT_TEMPLATES_DIR = DEFAULT_WUKONG_DIR / "runtime" / "templates"
DEFAULT_ARTIFACTS_DIR = DEFAULT_WUKONG_DIR / "artifacts"
DEFAULT_ANCHORS_DIR = DEFAULT_WUKONG_DIR / "anchors"


# Track keywords for analysis
TRACK_KEYWORDS = {
    "fix": ["修复", "修正", "解决", "bug", "fix", "error", "crash", "issue", "问题"],
    "feature": ["添加", "创建", "新增", "实现", "开发", "add", "create", "new", "implement", "feature", "功能"],
    "refactor": ["重构", "优化", "清理", "整理", "refactor", "clean", "optimize", "modernize"],
    "research": ["研究", "调研", "了解", "学习", "探索", "分析", "research", "explore", "investigate", "调查"],
}

# Track phases
TRACK_PHASES = {
    "fix": [
        {"phase": 0, "nodes": ["eye_explore", "nose_analyze"], "parallel": True},
        {"phase": 1, "nodes": ["body_implement"], "parallel": False},
        {"phase": 2, "nodes": ["tongue_verify"], "parallel": False},
    ],
    "feature": [
        {"phase": 0, "nodes": ["ear_understand", "eye_explore"], "parallel": True},
        {"phase": 1, "nodes": ["mind_design"], "parallel": False},
        {"phase": 2, "nodes": ["body_implement"], "parallel": False},
        {"phase": 3, "nodes": ["tongue_verify", "nose_review"], "parallel": True},
    ],
    "refactor": [
        {"phase": 0, "nodes": ["eye_explore"], "parallel": False},
        {"phase": 1, "nodes": ["mind_design"], "parallel": False},
        {"phase": 2, "nodes": ["body_implement"], "parallel": False},
        {"phase": 3, "nodes": ["nose_review", "tongue_verify"], "parallel": True},
    ],
    "research": [
        {"phase": 0, "nodes": ["eye_explore"], "parallel": False},
    ],
    "direct": [
        {"phase": 0, "nodes": [], "parallel": False},
    ],
}


def output_result(result: Dict[str, Any], human: bool = False) -> None:
    """Output result in JSON or human-readable format."""
    if human:
        print_human_readable(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def print_human_readable(result: Dict[str, Any]) -> None:
    """Print result in human-readable format."""
    if "error" in result:
        print(f"Error: {result['error']}")
        return

    if "track" in result and "confidence" in result:
        # analyze result
        print(f"Track: {result['track'].upper()}")
        print(f"Confidence: {result['confidence']:.0%}")
        print(f"Keywords matched: {', '.join(result.get('keywords_matched', []))}")
        print("\nPhases:")
        for phase in result.get("phases", []):
            parallel_str = "(parallel)" if phase.get("parallel") else ""
            print(f"  Phase {phase['phase']}: {', '.join(phase['nodes'])} {parallel_str}")

    elif "total_cost" in result:
        # metrics result (check before status result as it also has graph_id and status)
        print(f"Graph ID: {result.get('graph_id', 'N/A')}")
        print(f"Track: {result.get('track', 'N/A')}")
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
        print(f"\nCost & Duration:")
        print(f"  Total Cost: ${result.get('total_cost', 0):.4f}")
        duration = result.get('total_duration_sec')
        if duration:
            print(f"  Duration: {duration:.1f}s")
        else:
            print(f"  Duration: N/A")
        print(f"  Nodes: {result.get('node_count', 0)}")

        if "by_role" in result:
            print(f"\nCost by Role:")
            for role, cost in result.get("by_role", {}).items():
                print(f"  {role}: ${cost:.4f}")

        if "by_tier" in result:
            print(f"\nCost by Tier:")
            for tier, cost in result.get("by_tier", {}).items():
                print(f"  {tier}: ${cost:.4f}")

    elif "graph_id" in result and "status" in result and "progress" in result:
        # status result
        print(f"Graph ID: {result['graph_id']}")
        print(f"Status: {result['status']}")
        print(f"Track: {result.get('track', 'N/A')}")
        print(f"Current Phase: {result.get('current_phase', 0)}")
        progress = result.get("progress", {})
        print(f"\nProgress: {progress.get('completed', 0)}/{progress.get('total', 0)}")
        print(f"  Running: {progress.get('running', 0)}")
        print(f"  Pending: {progress.get('pending', 0)}")

    elif "ready_nodes" in result:
        # next result
        ready = result.get("ready_nodes", [])
        if ready:
            print(f"Ready nodes ({len(ready)}):")
            for node in ready:
                bg = f"[{node.get('background', 'N/A')}]" if node.get("background") else ""
                print(f"  - {node['id']}: {node.get('title', 'N/A')} ({node.get('role', 'N/A')}) {bg}")
        else:
            print("No nodes ready for execution")

        blocked = result.get("blocked_nodes", [])
        if blocked:
            print(f"\nBlocked nodes: {', '.join(blocked)}")

        completed = result.get("completed_nodes", [])
        if completed:
            print(f"\nCompleted nodes: {', '.join(completed)}")

    elif "retry_count" in result and "node_id" in result:
        # retry result
        if result.get("success"):
            print(f"Success: {result.get('message', 'Retry scheduled')}")
            print(f"  Node: {result.get('node_id')}")
            print(f"  Retry Count: {result.get('retry_count')}")
        else:
            print(f"Failed: {result.get('error', 'Retry failed')}")

    elif "resumed_nodes" in result:
        # enhanced resume result
        if result.get("success"):
            print(f"Success: {result.get('message', 'Task resumed')}")
            print(f"  Graph ID: {result.get('graph_id')}")
            resumed = result.get("resumed_nodes", [])
            if resumed:
                print(f"  Resumed Nodes: {', '.join(resumed)}")
            next_ready = result.get("next_ready", [])
            if next_ready:
                print(f"  Next Ready: {', '.join(next_ready)}")
        else:
            print(f"Failed: {result.get('error', 'Resume failed')}")

    elif "summary" in result and "nodes" in result and "healthy" in result.get("summary", {}):
        # health result
        summary = result.get("summary", {})
        print(f"Health Report ({result.get('timestamp', 'N/A')})")
        print(f"  Healthy: {summary.get('healthy', 0)}")
        print(f"  Stalled: {summary.get('stalled', 0)}")
        print(f"  Timeout: {summary.get('timeout', 0)}")
        print(f"  Total: {summary.get('total', 0)}")

        nodes = result.get("nodes", {})
        if nodes:
            print("\nNode Details:")
            for node_id, node_data in nodes.items():
                status = node_data.get("status", "unknown")
                status_icon = {
                    "healthy": "[OK]",
                    "stalled": "[WARN]",
                    "timeout": "[CRIT]",
                    "unknown": "[?]",
                }.get(status, "[?]")
                seconds = node_data.get("seconds_since_heartbeat")
                if seconds is not None:
                    time_str = f"{seconds:.0f}s ago"
                else:
                    time_str = "never"
                tier = node_data.get("cost_tier", "unknown")
                print(f"  {status_icon} {node_id}: {status} (last: {time_str}, tier: {tier})")

    elif "success" in result:
        # complete/fail/abort/resume result
        if result["success"]:
            print(f"Success: {result.get('message', 'Operation completed')}")
        else:
            print(f"Failed: {result.get('error', result.get('message', 'Operation failed'))}")

    else:
        # Generic result
        for key, value in result.items():
            print(f"{key}: {value}")


def analyze_task(task: str) -> Dict[str, Any]:
    """
    Analyze task and select appropriate track (L0 rule-based).

    Returns a result dict with:
    - track: selected track
    - confidence: confidence score (0.0-1.0)
    - keywords_matched: matched keywords
    - phases: execution phases
    - needs_llm: True if confidence < 0.7 (suggest calling Haiku scheduler)
    - routed_by: "L0" to indicate rule-based routing
    """
    task_lower = task.lower()

    best_track = "direct"
    best_confidence = 0.0
    matched_keywords: List[str] = []

    for track, keywords in TRACK_KEYWORDS.items():
        matches = [kw for kw in keywords if kw in task_lower]
        if matches:
            confidence = len(matches) / len(keywords)
            if confidence > best_confidence:
                best_confidence = confidence
                best_track = track
                matched_keywords = matches

    # Adjust confidence - if any keyword matched, minimum 0.5
    if matched_keywords and best_confidence < 0.5:
        best_confidence = 0.5

    # If no keywords matched, default to direct with low confidence
    if not matched_keywords:
        best_confidence = 0.3

    # Determine if LLM (Haiku scheduler) is needed
    needs_llm = best_confidence < 0.7

    return {
        "track": best_track,
        "confidence": round(best_confidence, 2),
        "keywords_matched": matched_keywords,
        "phases": TRACK_PHASES.get(best_track, TRACK_PHASES["direct"]),
        "needs_llm": needs_llm,
        "routed_by": "L0",
    }


def create_taskgraph(
    track: str,
    task: str,
    working_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new task graph from track template."""
    # Initialize scheduler
    templates_dir = DEFAULT_TEMPLATES_DIR

    # Try to find templates in different locations
    possible_paths = [
        templates_dir,
        script_dir / "templates",
        Path(__file__).parent / "templates",
    ]

    scheduler = None
    for path in possible_paths:
        if path.exists() and (path / f"{track}_track.json").exists():
            scheduler = Scheduler(path)
            break

    if not scheduler:
        return {
            "error": f"Template directory not found. Searched: {[str(p) for p in possible_paths]}",
            "success": False,
        }

    try:
        # Load template
        template = scheduler.load_template(track)

        # Instantiate graph
        graph = scheduler.instantiate_graph(
            template,
            task,
            working_dir=working_dir or os.getcwd(),
        )

        # Save to taskgraph.json
        DEFAULT_WUKONG_DIR.mkdir(parents=True, exist_ok=True)
        with open(DEFAULT_TASKGRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)

        # Initialize state
        state_manager = StateManager(DEFAULT_STATE_FILE)
        state_manager.start_graph(graph["id"], graph.get("session_id", "sess_default"))

        # Write event
        event_bus = EventBus(DEFAULT_EVENTS_FILE)
        event_bus.write_event(
            "TaskGraphCreated",
            {"graph_id": graph["id"], "track": track, "title": graph["title"]},
            graph_id=graph["id"],
            source="user",
        )

        return {
            "success": True,
            "graph_id": graph["id"],
            "track": track,
            "title": graph["title"],
            "nodes": [n["id"] for n in graph.get("nodes", [])],
            "saved_to": str(DEFAULT_TASKGRAPH_FILE),
        }

    except FileNotFoundError as e:
        return {"error": str(e), "success": False}
    except ValueError as e:
        return {"error": str(e), "success": False}


def get_status() -> Dict[str, Any]:
    """Get current task graph status."""
    # Load state
    state_manager = StateManager(DEFAULT_STATE_FILE)
    state = state_manager.get_state()

    if not state.get("current_graph_id"):
        return {
            "graph_id": None,
            "status": "idle",
            "message": "No active task graph",
        }

    # Load task graph
    if not DEFAULT_TASKGRAPH_FILE.exists():
        return {
            "graph_id": state.get("current_graph_id"),
            "status": "error",
            "message": "Task graph file not found",
        }

    with open(DEFAULT_TASKGRAPH_FILE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    # Get scheduler for status calculation
    scheduler = Scheduler(DEFAULT_TEMPLATES_DIR)
    summary = scheduler.get_execution_summary(graph)

    return {
        "graph_id": graph.get("id"),
        "status": summary["status"],
        "track": graph.get("track", "unknown"),
        "title": graph.get("title", ""),
        "current_phase": state.get("current_phase", 0),
        "progress": {
            "total": summary["total_nodes"],
            "completed": summary["done"]["count"],
            "running": summary["running"]["count"],
            "pending": summary["pending"]["count"],
            "failed": summary["failed"]["count"],
        },
    }


def get_next_nodes() -> Dict[str, Any]:
    """Get nodes ready for execution."""
    # Check for active task graph
    if not DEFAULT_TASKGRAPH_FILE.exists():
        return {
            "ready_nodes": [],
            "blocked_nodes": [],
            "completed_nodes": [],
            "message": "No active task graph",
        }

    with open(DEFAULT_TASKGRAPH_FILE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    scheduler = Scheduler(DEFAULT_TEMPLATES_DIR)
    ready_nodes = scheduler.get_ready_nodes(graph)

    # Format ready nodes
    formatted_ready = []
    for node in ready_nodes:
        constraints = node.get("constraints", {})
        formatted_ready.append({
            "id": node["id"],
            "title": node.get("title", ""),
            "role": node.get("role", "unknown"),
            "background": constraints.get("background", "optional"),
            "cost_tier": constraints.get("cost_tier", "medium"),
        })

    # Get blocked and completed nodes
    nodes = graph.get("nodes", [])
    blocked = [n["id"] for n in nodes if n.get("status") == "blocked"]
    completed = [n["id"] for n in nodes if n.get("status") == "done"]
    running = [n["id"] for n in nodes if n.get("status") == "running"]

    return {
        "ready_nodes": formatted_ready,
        "blocked_nodes": blocked,
        "completed_nodes": completed,
        "running_nodes": running,
    }


def complete_node(node_id: str, summary: Optional[str] = None) -> Dict[str, Any]:
    """Mark a node as completed."""
    if not DEFAULT_TASKGRAPH_FILE.exists():
        return {"success": False, "error": "No active task graph"}

    with open(DEFAULT_TASKGRAPH_FILE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    scheduler = Scheduler(DEFAULT_TEMPLATES_DIR)

    try:
        outputs = {"summary": summary} if summary else {}
        graph = scheduler.mark_node_status(graph, node_id, "done", outputs=outputs)

        # Save updated graph
        with open(DEFAULT_TASKGRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)

        # Update state
        state_manager = StateManager(DEFAULT_STATE_FILE)
        state_manager.complete_node(node_id)

        # Archive output if summary provided
        if summary:
            artifact_manager = ArtifactManager(DEFAULT_ARTIFACTS_DIR)
            artifact_manager.archive_output(
                graph["id"],
                node_id,
                {"summary": summary},
                summary=summary,
            )

        # Write event
        event_bus = EventBus(DEFAULT_EVENTS_FILE)
        event_bus.write_event(
            "NodeCompleted",
            {"summary": summary or ""},
            node_id=node_id,
            graph_id=graph["id"],
            source="subagent",
        )

        # Check if graph is complete
        if scheduler.is_graph_complete(graph):
            state_manager.complete_graph()
            event_bus.write_event(
                "Stop",
                {"reason": "all_nodes_completed"},
                graph_id=graph["id"],
                source="system",
            )

        return {
            "success": True,
            "message": f"Node {node_id} marked as completed",
            "graph_complete": scheduler.is_graph_complete(graph),
        }

    except ValueError as e:
        return {"success": False, "error": str(e)}


def fail_node(node_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """Mark a node as failed."""
    if not DEFAULT_TASKGRAPH_FILE.exists():
        return {"success": False, "error": "No active task graph"}

    with open(DEFAULT_TASKGRAPH_FILE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    scheduler = Scheduler(DEFAULT_TEMPLATES_DIR)

    try:
        error = {"reason": reason} if reason else {}
        graph = scheduler.mark_node_status(graph, node_id, "failed", error=error)

        # Save updated graph
        with open(DEFAULT_TASKGRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)

        # Update state
        state_manager = StateManager(DEFAULT_STATE_FILE)
        state_manager.fail_node(node_id)

        # Write event
        event_bus = EventBus(DEFAULT_EVENTS_FILE)
        event_bus.write_event(
            "NodeFailed",
            {"reason": reason or "unknown"},
            node_id=node_id,
            graph_id=graph["id"],
            source="subagent",
        )

        return {
            "success": True,
            "message": f"Node {node_id} marked as failed",
            "reason": reason,
        }

    except ValueError as e:
        return {"success": False, "error": str(e)}


def abort_task(reason: Optional[str] = None) -> Dict[str, Any]:
    """Abort the current task."""
    state_manager = StateManager(DEFAULT_STATE_FILE)
    state = state_manager.get_state()

    if not state.get("current_graph_id"):
        return {"success": False, "error": "No active task to abort"}

    graph_id = state["current_graph_id"]

    # Update state
    state_manager.abort_graph(reason)

    # Update graph status
    if DEFAULT_TASKGRAPH_FILE.exists():
        with open(DEFAULT_TASKGRAPH_FILE, "r", encoding="utf-8") as f:
            graph = json.load(f)
        graph["status"] = "aborted"
        with open(DEFAULT_TASKGRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)

    # Write event
    event_bus = EventBus(DEFAULT_EVENTS_FILE)
    event_bus.write_event(
        "Stop",
        {"reason": reason or "user_abort"},
        graph_id=graph_id,
        source="user",
    )

    return {
        "success": True,
        "message": f"Task {graph_id} aborted",
        "reason": reason,
    }


def resume_task() -> Dict[str, Any]:
    """
    Resume an interrupted task.

    This enhanced version:
    1. Loads state.json to get current state
    2. Loads taskgraph.json to get the task graph
    3. Checks for running nodes (interrupted) and resets them to pending
    4. Returns information about resumed nodes and next ready nodes
    """
    state_manager = StateManager(DEFAULT_STATE_FILE)

    # Use the enhanced prepare_for_resume method
    resume_result = state_manager.prepare_for_resume()

    if not resume_result.get("success"):
        return resume_result

    graph_id = resume_result.get("graph_id")
    resumed_nodes = resume_result.get("resumed_nodes", [])

    # Update graph: reset running nodes to pending
    if DEFAULT_TASKGRAPH_FILE.exists():
        with open(DEFAULT_TASKGRAPH_FILE, "r", encoding="utf-8") as f:
            graph = json.load(f)

        scheduler = Scheduler(DEFAULT_TEMPLATES_DIR)

        # Reset any running nodes to pending (they were interrupted)
        for node in graph.get("nodes", []):
            if node.get("status") == "running":
                node["status"] = "pending"

        # Update graph status
        graph["status"] = "running"

        # Save updated graph
        with open(DEFAULT_TASKGRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)

        # Get ready nodes for next execution
        ready_nodes = scheduler.get_ready_nodes(graph)
        next_ready = [n["id"] for n in ready_nodes]

        # Write resume event
        event_bus = EventBus(DEFAULT_EVENTS_FILE)
        event_bus.write_event(
            "TaskGraphCreated",  # Using existing event type for resume
            {
                "action": "resume",
                "resumed_nodes": resumed_nodes,
            },
            graph_id=graph_id,
            source="user",
        )
    else:
        next_ready = []

    return {
        "success": True,
        "message": f"Task {graph_id} resumed",
        "graph_id": graph_id,
        "resumed_nodes": resumed_nodes,
        "next_ready": next_ready,
    }


def retry_node(node_id: str) -> Dict[str, Any]:
    """
    Retry a failed node.

    This function:
    1. Checks the node status is 'failed'
    2. Resets the node status to 'pending'
    3. Increments the retry_count
    4. Returns the updated information
    """
    if not DEFAULT_TASKGRAPH_FILE.exists():
        return {"success": False, "error": "No active task graph"}

    with open(DEFAULT_TASKGRAPH_FILE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    # Find the node
    target_node = None
    for node in graph.get("nodes", []):
        if node["id"] == node_id:
            target_node = node
            break

    if not target_node:
        return {"success": False, "error": f"Node not found: {node_id}"}

    if target_node.get("status") != "failed":
        return {
            "success": False,
            "error": f"Node {node_id} is not failed (status: {target_node.get('status')})",
        }

    # Increment retry count
    current_retry = target_node.get("retry_count", 0)
    target_node["retry_count"] = current_retry + 1
    target_node["status"] = "pending"

    # Clear error if present
    if "error" in target_node:
        # Store previous error in history
        if "error_history" not in target_node:
            target_node["error_history"] = []
        target_node["error_history"].append(target_node.pop("error"))

    # Save updated graph
    with open(DEFAULT_TASKGRAPH_FILE, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    # Update state manager
    state_manager = StateManager(DEFAULT_STATE_FILE)
    state_manager.record_retry(node_id)

    # Write event
    event_bus = EventBus(DEFAULT_EVENTS_FILE)
    event_bus.write_event(
        "NodeScheduled",  # Using existing event type
        {
            "action": "retry",
            "retry_count": target_node["retry_count"],
        },
        node_id=node_id,
        graph_id=graph["id"],
        source="user",
    )

    return {
        "success": True,
        "node_id": node_id,
        "retry_count": target_node["retry_count"],
        "message": f"Node {node_id} reset for retry (attempt {target_node['retry_count'] + 1})",
    }


def get_metrics(breakdown: bool = False) -> Dict[str, Any]:
    """
    Get metrics for the current task graph.

    Args:
        breakdown: If True, include cost breakdown by role and tier

    Returns:
        Metrics dictionary with cost and duration information
    """
    collector = get_default_collector()
    metrics = collector.collect_graph_metrics()

    if not metrics:
        return {
            "success": False,
            "error": "No task graph found or no metrics available",
        }

    result = {
        "success": True,
        "graph_id": metrics.graph_id,
        "track": metrics.track,
        "title": metrics.title,
        "status": metrics.status,
        "total_cost": round(metrics.total_estimated_cost, 4),
        "total_duration_sec": metrics.total_duration_sec,
        "node_count": len(metrics.nodes),
    }

    if breakdown:
        result["by_role"] = {
            k: round(v, 4) for k, v in metrics.cost_by_role.items()
        }
        result["by_tier"] = {
            k: round(v, 4) for k, v in metrics.cost_by_tier.items()
        }
        result["nodes"] = {
            nid: {
                "role": nm.role,
                "cost_tier": nm.cost_tier,
                "estimated_cost": round(nm.estimated_cost, 4),
                "duration_sec": nm.duration_sec,
                "status": nm.status,
                "retry_count": nm.retry_count,
            }
            for nid, nm in metrics.nodes.items()
        }

    return result


def start_node(node_id: str) -> Dict[str, Any]:
    """Mark a node as started (running)."""
    if not DEFAULT_TASKGRAPH_FILE.exists():
        return {"success": False, "error": "No active task graph"}

    with open(DEFAULT_TASKGRAPH_FILE, "r", encoding="utf-8") as f:
        graph = json.load(f)

    scheduler = Scheduler(DEFAULT_TEMPLATES_DIR)

    try:
        graph = scheduler.mark_node_status(graph, node_id, "running")

        # Save updated graph
        with open(DEFAULT_TASKGRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=False, indent=2)

        # Update state
        state_manager = StateManager(DEFAULT_STATE_FILE)
        state_manager.activate_node(node_id)

        # Write event
        event_bus = EventBus(DEFAULT_EVENTS_FILE)
        event_bus.write_event(
            "NodeScheduled",
            {"node_id": node_id},
            node_id=node_id,
            graph_id=graph["id"],
            source="scheduler",
        )

        return {
            "success": True,
            "message": f"Node {node_id} started",
        }

    except ValueError as e:
        return {"success": False, "error": str(e)}


# ============================================================
# Anchor Commands
# ============================================================


def anchor_search(keywords: List[str], project: Optional[str] = None, anchor_type: Optional[str] = None) -> Dict[str, Any]:
    """Search anchors by keywords."""
    anchor_manager = AnchorManager(DEFAULT_ANCHORS_DIR)

    try:
        results = anchor_manager.search_anchors(
            keywords,
            project=project,
            anchor_type=anchor_type,
            include_global=True,
        )

        return {
            "success": True,
            "keywords": keywords,
            "results_count": len(results),
            "results": results,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def anchor_add(
    anchor_type: str,
    title: str,
    content: str,
    keywords: Optional[List[str]] = None,
    evidence_level: str = "L1",
    graph_id: Optional[str] = None,
    node_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a candidate anchor."""
    anchor_manager = AnchorManager(DEFAULT_ANCHORS_DIR)

    anchor_data = {
        "type": anchor_type,
        "title": title,
        "content": content,
        "keywords": keywords or [],
        "evidence_level": evidence_level,
    }

    source = None
    if graph_id or node_id:
        source = {}
        if graph_id:
            source["graph_id"] = graph_id
        if node_id:
            source["node_id"] = node_id

    try:
        candidate_id = anchor_manager.add_candidate(anchor_data, source=source)
        return {
            "success": True,
            "candidate_id": candidate_id,
            "message": f"Candidate anchor created: {candidate_id}",
        }
    except ValueError as e:
        return {"success": False, "error": str(e)}


def anchor_promote(candidate_id: str, project: Optional[str] = None) -> Dict[str, Any]:
    """Promote a candidate to a full anchor."""
    anchor_manager = AnchorManager(DEFAULT_ANCHORS_DIR)

    try:
        anchor_id = anchor_manager.promote_anchor(candidate_id, project=project)
        return {
            "success": True,
            "anchor_id": anchor_id,
            "candidate_id": candidate_id,
            "message": f"Candidate {candidate_id} promoted to anchor {anchor_id}",
        }
    except ValueError as e:
        return {"success": False, "error": str(e)}


def anchor_export(project: Optional[str] = None, include_global: bool = True) -> Dict[str, Any]:
    """Export anchors to Markdown."""
    anchor_manager = AnchorManager(DEFAULT_ANCHORS_DIR)

    try:
        markdown = anchor_manager.export_anchors_md(
            project=project,
            include_global=include_global,
        )
        return {
            "success": True,
            "markdown": markdown,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def anchor_list_candidates() -> Dict[str, Any]:
    """List all pending candidates."""
    anchor_manager = AnchorManager(DEFAULT_ANCHORS_DIR)

    try:
        candidates = anchor_manager.list_candidates()
        return {
            "success": True,
            "count": len(candidates),
            "candidates": candidates,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def anchor_delete_candidate(candidate_id: str) -> Dict[str, Any]:
    """Delete a candidate anchor."""
    anchor_manager = AnchorManager(DEFAULT_ANCHORS_DIR)

    try:
        deleted = anchor_manager.delete_candidate(candidate_id)
        if deleted:
            return {
                "success": True,
                "message": f"Candidate {candidate_id} deleted",
            }
        else:
            return {
                "success": False,
                "error": f"Candidate not found: {candidate_id}",
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def visualize_graph(include_status: bool = True) -> str:
    """
    Visualize the current task graph as a Mermaid diagram.

    Args:
        include_status: If True, include status colors in the diagram

    Returns:
        Mermaid diagram string wrapped in code fence
    """
    visualizer = get_default_visualizer()
    mermaid_code = visualizer.render_mermaid(include_status=include_status)
    return f"```mermaid\n{mermaid_code}\n```"


def get_progress(compact: bool = False, output_format: str = "terminal", line: bool = False) -> str:
    """
    Get task execution progress visualization.

    Args:
        compact: If True, use compact single-line format
        output_format: Output format - "terminal", "json", or "mermaid"
        line: If True, use append-style progress display (追加式进度)

    Returns:
        Progress visualization string
    """
    visualizer = get_default_visualizer()

    # Import append-style progress functions
    from visualizer import render_full_progress

    if line:
        # Use append-style progress display
        return render_full_progress()

    snapshot = visualizer.collect_snapshot()

    if snapshot is None:
        if output_format == "json":
            return json.dumps({"error": "No active task graph"}, indent=2)
        return "No active task graph"

    if output_format == "json":
        return json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False)
    elif output_format == "mermaid":
        return f"```mermaid\n{visualizer.render_mermaid()}\n```"
    elif compact:
        return visualizer.render_compact(snapshot)
    else:
        return visualizer.render_terminal(snapshot)


# ============================================================
# Health Monitoring Commands
# ============================================================


def get_health(node_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get health status of subagent nodes.

    Args:
        node_id: Optional specific node to check (if None, check all)

    Returns:
        Health report dictionary
    """
    monitor = HealthMonitor(
        state_file=DEFAULT_STATE_FILE,
        events_file=DEFAULT_EVENTS_FILE,
        taskgraph_file=DEFAULT_TASKGRAPH_FILE,
    )

    if node_id:
        # Get specific node health
        report = monitor.get_node_health(node_id)
        if report:
            return {
                "success": True,
                "node_id": node_id,
                **report.to_dict(),
            }
        else:
            return {
                "success": False,
                "error": f"Node not found: {node_id}",
            }
    else:
        # Get full health report
        report = monitor.check_health()
        return report.to_dict()


def record_heartbeat(
    node_id: str,
    progress: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Record a heartbeat from a subagent.

    Args:
        node_id: ID of the node sending heartbeat
        progress: Optional progress information

    Returns:
        Success status
    """
    monitor = HealthMonitor(
        state_file=DEFAULT_STATE_FILE,
        events_file=DEFAULT_EVENTS_FILE,
        taskgraph_file=DEFAULT_TASKGRAPH_FILE,
    )

    try:
        monitor.record_heartbeat(node_id, progress)
        return {
            "success": True,
            "message": f"Heartbeat recorded for {node_id}",
            "node_id": node_id,
            "progress": progress or {},
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def clear_heartbeat(node_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Clear heartbeat record(s).

    Args:
        node_id: Specific node to clear (if None, clear all)

    Returns:
        Success status
    """
    monitor = HealthMonitor(
        state_file=DEFAULT_STATE_FILE,
        events_file=DEFAULT_EVENTS_FILE,
        taskgraph_file=DEFAULT_TASKGRAPH_FILE,
    )

    try:
        if node_id:
            cleared = monitor.clear_heartbeat(node_id)
            if cleared:
                return {
                    "success": True,
                    "message": f"Heartbeat cleared for {node_id}",
                }
            else:
                return {
                    "success": False,
                    "error": f"No heartbeat found for {node_id}",
                }
        else:
            count = monitor.clear_all_heartbeats()
            return {
                "success": True,
                "message": f"Cleared {count} heartbeat(s)",
                "count": count,
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def anchor_stats() -> Dict[str, Any]:
    """Get anchor statistics."""
    anchor_manager = AnchorManager(DEFAULT_ANCHORS_DIR)

    try:
        stats = anchor_manager.get_statistics()
        return {
            "success": True,
            **stats,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def anchor_get(anchor_id: str) -> Dict[str, Any]:
    """Get a specific anchor by ID."""
    anchor_manager = AnchorManager(DEFAULT_ANCHORS_DIR)

    try:
        anchor = anchor_manager.get_anchor(anchor_id)
        if anchor:
            return {
                "success": True,
                "anchor": anchor,
            }
        else:
            return {
                "success": False,
                "error": f"Anchor not found: {anchor_id}",
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def anchor_relevant(task: str, project: Optional[str] = None, max_results: int = 5) -> Dict[str, Any]:
    """Get anchors relevant to a task description."""
    anchor_manager = AnchorManager(DEFAULT_ANCHORS_DIR)

    try:
        anchors = anchor_manager.get_relevant_anchors(
            task,
            project=project,
            max_results=max_results,
        )
        return {
            "success": True,
            "task": task,
            "results_count": len(anchors),
            "results": anchors,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Wukong Runtime CLI - Manage task graph execution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s analyze "修复登录bug"
    %(prog)s create --track fix "修复登录bug"
    %(prog)s status
    %(prog)s progress
    %(prog)s next
    %(prog)s start eye_explore
    %(prog)s complete eye_explore --summary "Found the bug in auth.py"
    %(prog)s fail body_implement --reason "Build error"
    %(prog)s abort --reason "User requested"
    %(prog)s resume

Progress Visualization Commands:
    %(prog)s progress                          # Show terminal progress display
    %(prog)s progress --compact                # Show compact single-line format
    %(prog)s progress --line                   # Show append-style progress (Phase-by-phase)
    %(prog)s progress --format json            # Output as JSON
    %(prog)s progress --format mermaid         # Output as Mermaid diagram

Health Monitoring Commands:
    %(prog)s health                           # Check health of all nodes
    %(prog)s health eye_explore               # Check specific node health
    %(prog)s heartbeat eye_explore            # Record heartbeat
    %(prog)s heartbeat eye_explore -p '{"files_scanned": 10}'
    %(prog)s clear-heartbeat                  # Clear all heartbeats
    %(prog)s clear-heartbeat eye_explore      # Clear specific heartbeat

Anchor Commands:
    %(prog)s anchor search "认证 安全"
    %(prog)s anchor add --type decision --title "Use JWT" --content "..."
    %(prog)s anchor promote <candidate_id>
    %(prog)s anchor export
    %(prog)s anchor list-candidates
    %(prog)s anchor stats
        """,
    )

    # Global options
    parser.add_argument(
        "--human", "-H",
        action="store_true",
        help="Output in human-readable format (default: JSON)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze task and select appropriate track",
    )
    analyze_parser.add_argument("task", help="Task description to analyze")
    analyze_parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable LLM-based classification (requires ANTHROPIC_API_KEY)",
    )

    # create command
    create_parser = subparsers.add_parser(
        "create",
        help="Create a new task graph from track template",
    )
    create_parser.add_argument("task", help="Task description")
    create_parser.add_argument(
        "--track", "-t",
        choices=["fix", "feature", "refactor", "direct"],
        required=True,
        help="Track type to use",
    )
    create_parser.add_argument(
        "--working-dir", "-w",
        help="Working directory (default: current directory)",
    )

    # status command
    subparsers.add_parser("status", help="Show current task graph status")

    # next command
    subparsers.add_parser("next", help="Get nodes ready for execution")

    # start command
    start_parser = subparsers.add_parser(
        "start",
        help="Mark a node as started (running)",
    )
    start_parser.add_argument("node_id", help="ID of the node to start")

    # complete command
    complete_parser = subparsers.add_parser(
        "complete",
        help="Mark a node as completed",
    )
    complete_parser.add_argument("node_id", help="ID of the completed node")
    complete_parser.add_argument(
        "--summary", "-s",
        help="Summary of the node's output",
    )

    # fail command
    fail_parser = subparsers.add_parser(
        "fail",
        help="Mark a node as failed",
    )
    fail_parser.add_argument("node_id", help="ID of the failed node")
    fail_parser.add_argument(
        "--reason", "-r",
        help="Reason for failure",
    )

    # abort command
    abort_parser = subparsers.add_parser(
        "abort",
        help="Abort the current task",
    )
    abort_parser.add_argument(
        "--reason", "-r",
        help="Reason for abortion",
    )

    # resume command
    subparsers.add_parser("resume", help="Resume an interrupted task")

    # retry command
    retry_parser = subparsers.add_parser(
        "retry",
        help="Retry a failed node",
    )
    retry_parser.add_argument("node_id", help="ID of the failed node to retry")

    # metrics command
    metrics_parser = subparsers.add_parser(
        "metrics",
        help="Show cost and duration metrics for current task",
    )
    metrics_parser.add_argument(
        "--breakdown", "-b",
        action="store_true",
        help="Include detailed breakdown by role and tier",
    )

    # visualize command
    visualize_parser = subparsers.add_parser(
        "visualize",
        help="Visualize task graph as Mermaid diagram",
    )
    visualize_parser.add_argument(
        "--no-status",
        action="store_true",
        help="Exclude status colors from diagram",
    )

    # progress command
    progress_parser = subparsers.add_parser(
        "progress",
        help="Show task execution progress visualization",
    )
    progress_parser.add_argument(
        "--compact", "-c",
        action="store_true",
        help="Use compact single-line format",
    )
    progress_parser.add_argument(
        "--format", "-f",
        choices=["terminal", "json", "mermaid"],
        default="terminal",
        help="Output format (default: terminal)",
    )
    progress_parser.add_argument(
        "--line", "-l",
        action="store_true",
        help="Use append-style progress display (Phase-by-phase)",
    )

    # health command
    health_parser = subparsers.add_parser(
        "health",
        help="Check health status of subagent nodes",
    )
    health_parser.add_argument(
        "node_id",
        nargs="?",
        help="Optional: specific node to check",
    )

    # heartbeat command
    heartbeat_parser = subparsers.add_parser(
        "heartbeat",
        help="Record a heartbeat from a subagent",
    )
    heartbeat_parser.add_argument(
        "node_id",
        help="ID of the node sending heartbeat",
    )
    heartbeat_parser.add_argument(
        "--progress", "-p",
        help="Progress info as JSON string (e.g., '{\"files_scanned\": 10}')",
    )

    # clear-heartbeat command
    clear_heartbeat_parser = subparsers.add_parser(
        "clear-heartbeat",
        help="Clear heartbeat record(s)",
    )
    clear_heartbeat_parser.add_argument(
        "node_id",
        nargs="?",
        help="Optional: specific node to clear (clears all if omitted)",
    )

    # anchor command group
    anchor_parser = subparsers.add_parser(
        "anchor",
        help="Manage anchors (cross-session knowledge)",
    )
    anchor_subparsers = anchor_parser.add_subparsers(dest="anchor_command", help="Anchor commands")

    # anchor search
    anchor_search_parser = anchor_subparsers.add_parser(
        "search",
        help="Search anchors by keywords",
    )
    anchor_search_parser.add_argument(
        "keywords",
        nargs="+",
        help="Keywords to search for",
    )
    anchor_search_parser.add_argument(
        "--project", "-p",
        help="Search in specific project",
    )
    anchor_search_parser.add_argument(
        "--type", "-t",
        choices=["decision", "constraint", "interface", "lesson"],
        help="Filter by anchor type",
    )

    # anchor add
    anchor_add_parser = anchor_subparsers.add_parser(
        "add",
        help="Add a candidate anchor",
    )
    anchor_add_parser.add_argument(
        "--type", "-t",
        required=True,
        choices=["decision", "constraint", "interface", "lesson"],
        help="Anchor type",
    )
    anchor_add_parser.add_argument(
        "--title",
        required=True,
        help="Anchor title",
    )
    anchor_add_parser.add_argument(
        "--content",
        required=True,
        help="Anchor content",
    )
    anchor_add_parser.add_argument(
        "--keywords", "-k",
        nargs="+",
        help="Keywords for search",
    )
    anchor_add_parser.add_argument(
        "--evidence-level", "-e",
        default="L1",
        choices=["L0", "L1", "L2", "L3"],
        help="Evidence level (default: L1)",
    )
    anchor_add_parser.add_argument(
        "--graph-id",
        help="Source task graph ID",
    )
    anchor_add_parser.add_argument(
        "--node-id",
        help="Source node ID",
    )

    # anchor promote
    anchor_promote_parser = anchor_subparsers.add_parser(
        "promote",
        help="Promote a candidate to full anchor",
    )
    anchor_promote_parser.add_argument(
        "candidate_id",
        help="ID of the candidate to promote",
    )
    anchor_promote_parser.add_argument(
        "--project", "-p",
        help="Target project for the anchor",
    )

    # anchor export
    anchor_export_parser = anchor_subparsers.add_parser(
        "export",
        help="Export anchors to Markdown",
    )
    anchor_export_parser.add_argument(
        "--project", "-p",
        help="Export specific project's anchors",
    )
    anchor_export_parser.add_argument(
        "--no-global",
        action="store_true",
        help="Exclude global anchors",
    )

    # anchor list-candidates
    anchor_subparsers.add_parser(
        "list-candidates",
        help="List all pending candidates",
    )

    # anchor delete-candidate
    anchor_delete_candidate_parser = anchor_subparsers.add_parser(
        "delete-candidate",
        help="Delete a candidate anchor",
    )
    anchor_delete_candidate_parser.add_argument(
        "candidate_id",
        help="ID of the candidate to delete",
    )

    # anchor stats
    anchor_subparsers.add_parser(
        "stats",
        help="Get anchor statistics",
    )

    # anchor get
    anchor_get_parser = anchor_subparsers.add_parser(
        "get",
        help="Get a specific anchor by ID",
    )
    anchor_get_parser.add_argument(
        "anchor_id",
        help="Anchor ID",
    )

    # anchor relevant
    anchor_relevant_parser = anchor_subparsers.add_parser(
        "relevant",
        help="Get anchors relevant to a task",
    )
    anchor_relevant_parser.add_argument(
        "task",
        help="Task description",
    )
    anchor_relevant_parser.add_argument(
        "--project", "-p",
        help="Project context",
    )
    anchor_relevant_parser.add_argument(
        "--max", "-m",
        type=int,
        default=5,
        help="Maximum results (default: 5)",
    )

    args = parser.parse_args()

    # Handle commands
    result: Dict[str, Any] = {}

    if args.command == "analyze":
        result = analyze_task(args.task)
    elif args.command == "create":
        result = create_taskgraph(args.track, args.task, args.working_dir)
    elif args.command == "status":
        result = get_status()
    elif args.command == "next":
        result = get_next_nodes()
    elif args.command == "start":
        result = start_node(args.node_id)
    elif args.command == "complete":
        result = complete_node(args.node_id, args.summary)
    elif args.command == "fail":
        result = fail_node(args.node_id, args.reason)
    elif args.command == "abort":
        result = abort_task(args.reason)
    elif args.command == "resume":
        result = resume_task()
    elif args.command == "retry":
        result = retry_node(args.node_id)
    elif args.command == "metrics":
        result = get_metrics(breakdown=args.breakdown)
    elif args.command == "visualize":
        # Visualize outputs directly, not as JSON
        mermaid_output = visualize_graph(include_status=not args.no_status)
        print(mermaid_output)
        sys.exit(0)
    elif args.command == "progress":
        # Progress outputs directly, not as JSON (unless --format json)
        progress_output = get_progress(
            compact=args.compact,
            output_format=args.format,
            line=args.line,
        )
        print(progress_output)
        sys.exit(0)
    elif args.command == "health":
        result = get_health(node_id=args.node_id)
    elif args.command == "heartbeat":
        # Parse progress JSON if provided
        progress = None
        if args.progress:
            try:
                progress = json.loads(args.progress)
            except json.JSONDecodeError:
                result = {"success": False, "error": "Invalid JSON for progress"}
                output_result(result, human=args.human)
                sys.exit(1)
        result = record_heartbeat(args.node_id, progress)
    elif args.command == "clear-heartbeat":
        result = clear_heartbeat(node_id=args.node_id)
    elif args.command == "anchor":
        # Handle anchor subcommands
        if args.anchor_command == "search":
            result = anchor_search(
                args.keywords,
                project=args.project,
                anchor_type=getattr(args, "type", None),
            )
        elif args.anchor_command == "add":
            result = anchor_add(
                anchor_type=args.type,
                title=args.title,
                content=args.content,
                keywords=args.keywords,
                evidence_level=args.evidence_level,
                graph_id=args.graph_id,
                node_id=args.node_id,
            )
        elif args.anchor_command == "promote":
            result = anchor_promote(args.candidate_id, project=args.project)
        elif args.anchor_command == "export":
            result = anchor_export(
                project=args.project,
                include_global=not args.no_global,
            )
            # For export, print markdown directly if human mode
            if args.human and result.get("success"):
                print(result.get("markdown", ""))
                sys.exit(0)
        elif args.anchor_command == "list-candidates":
            result = anchor_list_candidates()
        elif args.anchor_command == "delete-candidate":
            result = anchor_delete_candidate(args.candidate_id)
        elif args.anchor_command == "stats":
            result = anchor_stats()
        elif args.anchor_command == "get":
            result = anchor_get(args.anchor_id)
        elif args.anchor_command == "relevant":
            result = anchor_relevant(
                args.task,
                project=args.project,
                max_results=args.max,
            )
        else:
            anchor_parser.print_help()
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

    output_result(result, human=args.human)


if __name__ == "__main__":
    main()
