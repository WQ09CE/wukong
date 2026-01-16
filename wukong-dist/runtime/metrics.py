"""
Wukong Metrics - Cost and duration tracking for task graph execution.

Collects metrics from events.jsonl and state.json to provide:
- Per-node timing and cost estimation
- Aggregated cost breakdowns by role and tier
- Execution duration tracking
- Export to JSON report format
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


# Cost tier definitions (estimated cost per call in USD)
COST_TIERS = {
    "cheap": 0.001,    # haiku - eye, ear, nose
    "medium": 0.01,    # sonnet - tongue
    "expensive": 0.10,  # opus - body, mind
}

# Role to cost tier mapping
ROLE_TO_TIER = {
    "eye": "cheap",
    "ear": "cheap",
    "nose": "cheap",
    "tongue": "medium",
    "body": "expensive",
    "mind": "expensive",
}


@dataclass
class NodeMetrics:
    """Metrics for a single node execution."""

    node_id: str
    role: str
    cost_tier: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_sec: Optional[float] = None
    estimated_cost: float = 0.0
    status: str = "pending"
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "role": self.role,
            "cost_tier": self.cost_tier,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_sec": self.duration_sec,
            "estimated_cost": self.estimated_cost,
            "status": self.status,
            "retry_count": self.retry_count,
        }


@dataclass
class GraphMetrics:
    """Aggregated metrics for a task graph execution."""

    graph_id: str
    track: str
    title: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_duration_sec: Optional[float] = None
    total_estimated_cost: float = 0.0
    nodes: Dict[str, NodeMetrics] = field(default_factory=dict)
    cost_by_role: Dict[str, float] = field(default_factory=dict)
    cost_by_tier: Dict[str, float] = field(default_factory=dict)
    status: str = "created"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "graph_id": self.graph_id,
            "track": self.track,
            "title": self.title,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_sec": self.total_duration_sec,
            "total_estimated_cost": round(self.total_estimated_cost, 4),
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "cost_by_role": {k: round(v, 4) for k, v in self.cost_by_role.items()},
            "cost_by_tier": {k: round(v, 4) for k, v in self.cost_by_tier.items()},
            "status": self.status,
        }


class MetricsCollector:
    """
    Collects and aggregates metrics from event logs and state files.

    Usage:
        collector = MetricsCollector(events_file, state_file)
        metrics = collector.collect_graph_metrics(graph_id)
        print(f"Total cost: ${metrics.total_estimated_cost:.4f}")
    """

    def __init__(
        self,
        events_file: Path,
        state_file: Path,
        taskgraph_file: Optional[Path] = None,
    ):
        """
        Initialize the MetricsCollector.

        Args:
            events_file: Path to events.jsonl
            state_file: Path to state.json
            taskgraph_file: Optional path to taskgraph.json
        """
        self.events_file = Path(events_file).expanduser()
        self.state_file = Path(state_file).expanduser()
        self.taskgraph_file = (
            Path(taskgraph_file).expanduser() if taskgraph_file else None
        )

    def _parse_timestamp(self, ts: str) -> datetime:
        """Parse ISO 8601 timestamp to datetime."""
        # Handle both formats: with and without microseconds
        try:
            # Try with microseconds and timezone
            if "+" in ts or ts.endswith("Z"):
                ts = ts.replace("Z", "+00:00")
                return datetime.fromisoformat(ts)
            else:
                return datetime.fromisoformat(ts)
        except ValueError:
            # Fallback: just return current time
            return datetime.now()

    def _calculate_duration(
        self,
        start_ts: Optional[str],
        end_ts: Optional[str],
    ) -> Optional[float]:
        """Calculate duration in seconds between two timestamps."""
        if not start_ts or not end_ts:
            return None

        try:
            start = self._parse_timestamp(start_ts)
            end = self._parse_timestamp(end_ts)
            delta = end - start
            return delta.total_seconds()
        except Exception:
            return None

    def _read_events(
        self,
        filter_graph_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Read events from the events file."""
        if not self.events_file.exists():
            return []

        events = []
        with open(self.events_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                    if filter_graph_id and event.get("graph_id") != filter_graph_id:
                        continue
                    events.append(event)
                except json.JSONDecodeError:
                    continue

        return events

    def _read_taskgraph(self) -> Optional[Dict[str, Any]]:
        """Read the current task graph."""
        if not self.taskgraph_file or not self.taskgraph_file.exists():
            return None

        try:
            with open(self.taskgraph_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _get_node_cost_tier(
        self,
        node: Dict[str, Any],
    ) -> str:
        """Get the cost tier for a node."""
        # First check constraints
        constraints = node.get("constraints", {})
        if "cost_tier" in constraints:
            return constraints["cost_tier"]

        # Fall back to role-based tier
        role = node.get("role", "body")
        return ROLE_TO_TIER.get(role, "medium")

    def _estimate_node_cost(
        self,
        node: Dict[str, Any],
        retry_count: int = 0,
    ) -> float:
        """Estimate the cost for a node execution."""
        tier = self._get_node_cost_tier(node)
        base_cost = COST_TIERS.get(tier, COST_TIERS["medium"])
        # Cost increases with retries
        return base_cost * (1 + retry_count)

    def collect_graph_metrics(
        self,
        graph_id: Optional[str] = None,
    ) -> Optional[GraphMetrics]:
        """
        Collect all metrics for a task graph.

        Args:
            graph_id: ID of the graph to collect metrics for.
                     If None, uses the current graph from taskgraph.json.

        Returns:
            GraphMetrics object with all collected data, or None if not found.
        """
        # Get graph info
        graph = self._read_taskgraph()
        if not graph:
            return None

        # Use provided graph_id or get from current graph
        target_graph_id = graph_id or graph.get("id")
        if not target_graph_id:
            return None

        # Verify we have the right graph
        if graph.get("id") != target_graph_id:
            return None

        # Initialize metrics
        metrics = GraphMetrics(
            graph_id=target_graph_id,
            track=graph.get("track", "unknown"),
            title=graph.get("title", ""),
            status=graph.get("status", "created"),
        )

        # Read events for this graph
        events = self._read_events(filter_graph_id=target_graph_id)

        # Build node metrics from graph nodes and events
        for node in graph.get("nodes", []):
            node_id = node["id"]
            role = node.get("role", "unknown")
            tier = self._get_node_cost_tier(node)

            node_metrics = NodeMetrics(
                node_id=node_id,
                role=role,
                cost_tier=tier,
                status=node.get("status", "pending"),
                retry_count=node.get("retry_count", 0),
            )

            # Find timing from events
            for event in events:
                if event.get("node_id") != node_id:
                    continue

                event_type = event.get("type")
                timestamp = event.get("timestamp")

                if event_type == "NodeScheduled":
                    node_metrics.started_at = timestamp
                elif event_type in ("NodeCompleted", "NodeFailed"):
                    node_metrics.completed_at = timestamp

            # Calculate duration
            node_metrics.duration_sec = self._calculate_duration(
                node_metrics.started_at,
                node_metrics.completed_at,
            )

            # Estimate cost if node was executed
            if node_metrics.status in ("done", "failed", "running"):
                node_metrics.estimated_cost = self._estimate_node_cost(
                    node,
                    node_metrics.retry_count,
                )

            metrics.nodes[node_id] = node_metrics

        # Calculate aggregated metrics
        self._aggregate_metrics(metrics, events)

        return metrics

    def _aggregate_metrics(
        self,
        metrics: GraphMetrics,
        events: List[Dict[str, Any]],
    ) -> None:
        """Calculate aggregated metrics for the graph."""
        # Find graph timing from events
        for event in events:
            event_type = event.get("type")
            timestamp = event.get("timestamp")

            if event_type == "TaskGraphCreated":
                metrics.started_at = timestamp
            elif event_type == "Stop":
                metrics.completed_at = timestamp

        # Calculate total duration
        metrics.total_duration_sec = self._calculate_duration(
            metrics.started_at,
            metrics.completed_at,
        )

        # Aggregate costs
        cost_by_role: Dict[str, float] = {}
        cost_by_tier: Dict[str, float] = {}
        total_cost = 0.0

        for node_metrics in metrics.nodes.values():
            cost = node_metrics.estimated_cost
            role = node_metrics.role
            tier = node_metrics.cost_tier

            total_cost += cost

            if role not in cost_by_role:
                cost_by_role[role] = 0.0
            cost_by_role[role] += cost

            if tier not in cost_by_tier:
                cost_by_tier[tier] = 0.0
            cost_by_tier[tier] += cost

        metrics.total_estimated_cost = total_cost
        metrics.cost_by_role = cost_by_role
        metrics.cost_by_tier = cost_by_tier

    def get_node_metrics(
        self,
        graph_id: str,
        node_id: str,
    ) -> Optional[NodeMetrics]:
        """
        Get metrics for a specific node.

        Args:
            graph_id: ID of the task graph
            node_id: ID of the node

        Returns:
            NodeMetrics for the node, or None if not found
        """
        graph_metrics = self.collect_graph_metrics(graph_id)
        if not graph_metrics:
            return None

        return graph_metrics.nodes.get(node_id)

    def get_total_cost(
        self,
        graph_id: Optional[str] = None,
    ) -> float:
        """
        Get the total estimated cost for a task graph.

        Args:
            graph_id: ID of the task graph (or None for current)

        Returns:
            Total estimated cost in USD
        """
        metrics = self.collect_graph_metrics(graph_id)
        if not metrics:
            return 0.0

        return metrics.total_estimated_cost

    def get_total_duration(
        self,
        graph_id: Optional[str] = None,
    ) -> float:
        """
        Get the total duration for a task graph execution.

        Args:
            graph_id: ID of the task graph (or None for current)

        Returns:
            Total duration in seconds
        """
        metrics = self.collect_graph_metrics(graph_id)
        if not metrics:
            return 0.0

        return metrics.total_duration_sec or 0.0

    def get_cost_breakdown(
        self,
        graph_id: Optional[str] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        Get cost breakdown by role and tier.

        Args:
            graph_id: ID of the task graph (or None for current)

        Returns:
            Dictionary with 'by_role' and 'by_tier' breakdowns
        """
        metrics = self.collect_graph_metrics(graph_id)
        if not metrics:
            return {"by_role": {}, "by_tier": {}}

        return {
            "by_role": metrics.cost_by_role,
            "by_tier": metrics.cost_by_tier,
        }

    def export_report(
        self,
        graph_id: Optional[str] = None,
    ) -> str:
        """
        Export a full metrics report as JSON string.

        Args:
            graph_id: ID of the task graph (or None for current)

        Returns:
            JSON string containing the full metrics report
        """
        metrics = self.collect_graph_metrics(graph_id)
        if not metrics:
            return json.dumps({"error": "Graph not found"}, indent=2)

        return json.dumps(metrics.to_dict(), indent=2, ensure_ascii=False)


def get_default_collector() -> MetricsCollector:
    """Get a MetricsCollector with default paths."""
    wukong_dir = Path.home() / ".wukong"
    return MetricsCollector(
        events_file=wukong_dir / "events.jsonl",
        state_file=wukong_dir / "state.json",
        taskgraph_file=wukong_dir / "taskgraph.json",
    )
