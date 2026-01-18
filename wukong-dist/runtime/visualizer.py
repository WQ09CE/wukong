"""
Wukong Visualizer - Task execution progress visualization.

Provides visual representations of task graph execution progress:
- Terminal-friendly progress display
- Mermaid diagram generation
- Progress snapshots for monitoring
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any


class NodeVisualStatus(Enum):
    """Visual status for node display."""
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"


# Status display mapping for terminal output
STATUS_DISPLAY = {
    NodeVisualStatus.PENDING: ("----", " "),
    NodeVisualStatus.RUNNING: (">>>>", "*"),
    NodeVisualStatus.DONE: ("Done", "x"),
    NodeVisualStatus.FAILED: ("FAIL", "!"),
    NodeVisualStatus.BLOCKED: ("BLKD", "-"),
}

# Role to emoji mapping for terminal display
ROLE_EMOJI = {
    "eye": "\U0001F441\uFE0F",      # 👁️
    "ear": "\U0001F442",             # 👂
    "nose": "\U0001F443",            # 👃
    "tongue": "\U0001F445",          # 👅
    "body": "\u2694\uFE0F",          # ⚔️
    "mind": "\U0001F9E0",            # 🧠
}


@dataclass
class NodeProgress:
    """Progress information for a single node."""

    node_id: str
    status: NodeVisualStatus
    role: str
    title: str
    duration_sec: Optional[float] = None
    estimated_sec: Optional[float] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "role": self.role,
            "title": self.title,
            "duration_sec": self.duration_sec,
            "estimated_sec": self.estimated_sec,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }


@dataclass
class ProgressSnapshot:
    """Snapshot of task graph execution progress."""

    graph_id: str
    track: str
    title: str
    nodes: Dict[str, NodeProgress]
    current_phase: int
    total_phases: int
    total_nodes: int
    completed_nodes: int
    running_nodes: int
    failed_nodes: int
    pending_nodes: int = 0
    elapsed_sec: Optional[float] = None
    estimated_remaining_sec: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "graph_id": self.graph_id,
            "track": self.track,
            "title": self.title,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "current_phase": self.current_phase,
            "total_phases": self.total_phases,
            "total_nodes": self.total_nodes,
            "completed_nodes": self.completed_nodes,
            "running_nodes": self.running_nodes,
            "failed_nodes": self.failed_nodes,
            "pending_nodes": self.pending_nodes,
            "elapsed_sec": self.elapsed_sec,
            "estimated_remaining_sec": self.estimated_remaining_sec,
        }

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.total_nodes == 0:
            return 0.0
        return (self.completed_nodes / self.total_nodes) * 100


class Visualizer:
    """
    Visualizer for task graph execution progress.

    Collects data from taskgraph.json and state.json to provide
    visual representations of execution progress.

    Usage:
        visualizer = Visualizer()
        snapshot = visualizer.collect_snapshot()
        print(visualizer.render_terminal(snapshot))
    """

    def __init__(
        self,
        taskgraph_file: Optional[Path] = None,
        state_file: Optional[Path] = None,
        events_file: Optional[Path] = None,
    ):
        """
        Initialize the Visualizer.

        Args:
            taskgraph_file: Path to taskgraph.json
            state_file: Path to state.json
            events_file: Path to events.jsonl
        """
        wukong_dir = Path.home() / ".wukong"
        self.taskgraph_file = Path(taskgraph_file) if taskgraph_file else wukong_dir / "taskgraph.json"
        self.state_file = Path(state_file) if state_file else wukong_dir / "state.json"
        self.events_file = Path(events_file) if events_file else wukong_dir / "events.jsonl"

    def _read_taskgraph(self) -> Optional[Dict[str, Any]]:
        """Read the current task graph."""
        if not self.taskgraph_file.exists():
            return None

        try:
            with open(self.taskgraph_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _read_state(self) -> Dict[str, Any]:
        """Read the current runtime state."""
        if not self.state_file.exists():
            return {}

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _read_events(self, graph_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Read events, optionally filtered by graph_id."""
        if not self.events_file.exists():
            return []

        events = []
        try:
            with open(self.events_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        if graph_id and event.get("graph_id") != graph_id:
                            continue
                        events.append(event)
                    except json.JSONDecodeError:
                        continue
        except IOError:
            pass

        return events

    def _parse_timestamp(self, ts: str) -> datetime:
        """Parse ISO 8601 timestamp to datetime."""
        try:
            if "+" in ts or ts.endswith("Z"):
                ts = ts.replace("Z", "+00:00")
                return datetime.fromisoformat(ts)
            else:
                return datetime.fromisoformat(ts)
        except ValueError:
            return datetime.now(timezone.utc)

    def _get_node_status(self, status_str: str) -> NodeVisualStatus:
        """Convert status string to NodeVisualStatus enum."""
        status_map = {
            "pending": NodeVisualStatus.PENDING,
            "running": NodeVisualStatus.RUNNING,
            "done": NodeVisualStatus.DONE,
            "failed": NodeVisualStatus.FAILED,
            "blocked": NodeVisualStatus.BLOCKED,
        }
        return status_map.get(status_str, NodeVisualStatus.PENDING)

    def _calculate_elapsed(self, events: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate elapsed time from events."""
        start_time = None
        for event in events:
            if event.get("type") == "TaskGraphCreated":
                start_time = event.get("timestamp")
                break

        if not start_time:
            return None

        start_dt = self._parse_timestamp(start_time)
        now = datetime.now(timezone.utc)
        return (now - start_dt).total_seconds()

    def _estimate_remaining(
        self,
        nodes: Dict[str, NodeProgress],
        elapsed_sec: Optional[float],
    ) -> Optional[float]:
        """Estimate remaining time based on progress."""
        completed = sum(1 for n in nodes.values() if n.status == NodeVisualStatus.DONE)
        total = len(nodes)

        if completed == 0 or elapsed_sec is None or total == 0:
            return None

        # Simple linear estimation
        avg_time_per_node = elapsed_sec / completed
        remaining_nodes = total - completed
        return avg_time_per_node * remaining_nodes

    def _get_total_phases(self, graph: Dict[str, Any]) -> int:
        """Get total number of phases from graph metadata."""
        metadata = graph.get("metadata", {})
        phases = metadata.get("phases", [])
        return len(phases) if phases else 1

    def _get_current_phase(self, graph: Dict[str, Any], state: Dict[str, Any]) -> int:
        """Determine current phase based on node statuses."""
        # First check state
        if state.get("current_phase") is not None:
            return state.get("current_phase", 0)

        # Otherwise infer from node statuses
        metadata = graph.get("metadata", {})
        phases = metadata.get("phases", [])

        if not phases:
            return 0

        nodes = {n["id"]: n.get("status", "pending") for n in graph.get("nodes", [])}

        # Find the current phase (first phase with non-completed nodes)
        for phase_info in phases:
            phase_nodes = phase_info.get("nodes", [])
            all_done = all(nodes.get(nid) == "done" for nid in phase_nodes)
            if not all_done:
                return phase_info.get("phase", 0)

        # All phases complete
        return len(phases) - 1

    def collect_snapshot(self) -> Optional[ProgressSnapshot]:
        """
        Collect current progress snapshot from taskgraph.json and state.json.

        Returns:
            ProgressSnapshot object, or None if no active task graph.
        """
        graph = self._read_taskgraph()
        if not graph:
            return None

        state = self._read_state()
        graph_id = graph.get("id", "unknown")
        events = self._read_events(graph_id)

        # Build node progress information
        nodes: Dict[str, NodeProgress] = {}
        completed_count = 0
        running_count = 0
        failed_count = 0
        pending_count = 0

        for node in graph.get("nodes", []):
            node_id = node["id"]
            status_str = node.get("status", "pending")
            status = self._get_node_status(status_str)

            # Count by status
            if status == NodeVisualStatus.DONE:
                completed_count += 1
            elif status == NodeVisualStatus.RUNNING:
                running_count += 1
            elif status == NodeVisualStatus.FAILED:
                failed_count += 1
            else:
                pending_count += 1

            # Get duration from node timing
            duration = None
            if "started_at" in node:
                start_dt = self._parse_timestamp(node["started_at"])
                if "completed_at" in node:
                    end_dt = self._parse_timestamp(node["completed_at"])
                    duration = (end_dt - start_dt).total_seconds()
                elif status == NodeVisualStatus.RUNNING:
                    # Running node - show elapsed time
                    now = datetime.now(timezone.utc)
                    duration = (now - start_dt).total_seconds()

            # Get estimated time from constraints
            estimated = None
            constraints = node.get("constraints", {})
            if "time_budget_sec" in constraints:
                estimated = float(constraints["time_budget_sec"])

            # Get error message if failed
            error_msg = None
            if status == NodeVisualStatus.FAILED:
                error = node.get("error", {})
                error_msg = error.get("reason") if isinstance(error, dict) else str(error)

            nodes[node_id] = NodeProgress(
                node_id=node_id,
                status=status,
                role=node.get("role", "unknown"),
                title=node.get("title", node_id),
                duration_sec=duration,
                estimated_sec=estimated,
                error_message=error_msg,
                retry_count=node.get("retry_count", 0),
            )

        # Calculate elapsed time
        elapsed = self._calculate_elapsed(events)

        # Estimate remaining time
        estimated_remaining = self._estimate_remaining(nodes, elapsed)

        # Get phase information
        total_phases = self._get_total_phases(graph)
        current_phase = self._get_current_phase(graph, state)

        return ProgressSnapshot(
            graph_id=graph_id,
            track=graph.get("track", "unknown"),
            title=graph.get("title", ""),
            nodes=nodes,
            current_phase=current_phase,
            total_phases=total_phases,
            total_nodes=len(nodes),
            completed_nodes=completed_count,
            running_nodes=running_count,
            failed_nodes=failed_count,
            pending_nodes=pending_count,
            elapsed_sec=elapsed,
            estimated_remaining_sec=estimated_remaining,
        )

    def render_terminal(
        self,
        snapshot: Optional[ProgressSnapshot] = None,
        use_color: bool = True,
        compact: bool = False,
    ) -> str:
        """
        Render progress as terminal-friendly text.

        Args:
            snapshot: ProgressSnapshot to render (collects if None)
            use_color: Whether to use ANSI color codes
            compact: If True, use compact single-line format

        Returns:
            Formatted terminal string

        Example output:
            Fix: 修复登录bug
            Phase 2/3 | [========>     ] 60% (3/5 nodes)

            [Done] eye_explore    探索问题           12s
            [Done] nose_analyze   分析代码            8s
            [>>>>] body_implement 实现修复           45s
            [----] tongue_verify  验证测试

            Elapsed: 1m 5s | ETA: ~1m 30s
        """
        if snapshot is None:
            snapshot = self.collect_snapshot()

        if snapshot is None:
            return "No active task graph"

        lines = []

        # Title line
        title = snapshot.title or f"{snapshot.track.title()} Task"
        lines.append(title)

        # Progress bar line
        progress_pct = snapshot.progress_percent
        phase_info = f"Phase {snapshot.current_phase + 1}/{snapshot.total_phases}"
        node_info = f"({snapshot.completed_nodes}/{snapshot.total_nodes} nodes)"

        # Build progress bar (20 chars wide)
        bar_width = 20
        filled = int(bar_width * progress_pct / 100)
        bar = "=" * filled
        if filled < bar_width and snapshot.running_nodes > 0:
            bar += ">"
            filled += 1
        bar = bar.ljust(bar_width)

        progress_line = f"{phase_info} | [{bar}] {progress_pct:.0f}% {node_info}"
        lines.append(progress_line)
        lines.append("")

        if not compact:
            # Node details - sort by phase order from metadata
            graph = self._read_taskgraph()
            node_order = []
            if graph:
                metadata = graph.get("metadata", {})
                phases = metadata.get("phases", [])
                for phase_info_item in phases:
                    node_order.extend(phase_info_item.get("nodes", []))

            # Add any nodes not in phases
            for nid in snapshot.nodes:
                if nid not in node_order:
                    node_order.append(nid)

            # Render each node
            for node_id in node_order:
                if node_id not in snapshot.nodes:
                    continue
                node = snapshot.nodes[node_id]

                status_text, _ = STATUS_DISPLAY.get(
                    node.status,
                    ("????", "?"),
                )

                # Format duration
                if node.duration_sec is not None:
                    if node.duration_sec >= 60:
                        duration_str = f"{int(node.duration_sec // 60)}m {int(node.duration_sec % 60)}s"
                    else:
                        duration_str = f"{int(node.duration_sec)}s"
                else:
                    duration_str = ""

                # Format: [Status] node_id   title   duration
                # Use fixed widths for alignment
                node_line = f"[{status_text}] {node_id:<18} {node.title:<18} {duration_str:>8}"

                # Add retry indicator if applicable
                if node.retry_count > 0:
                    node_line += f" (retry {node.retry_count})"

                # Add error message for failed nodes
                if node.status == NodeVisualStatus.FAILED and node.error_message:
                    node_line += f"\n         Error: {node.error_message}"

                lines.append(node_line)

            lines.append("")

        # Timing summary
        timing_parts = []
        if snapshot.elapsed_sec is not None:
            elapsed_str = self._format_duration(snapshot.elapsed_sec)
            timing_parts.append(f"Elapsed: {elapsed_str}")

        if snapshot.estimated_remaining_sec is not None:
            eta_str = self._format_duration(snapshot.estimated_remaining_sec)
            timing_parts.append(f"ETA: ~{eta_str}")

        if timing_parts:
            lines.append(" | ".join(timing_parts))

        # Status indicators for running/failed
        if snapshot.failed_nodes > 0:
            lines.append(f"[!] {snapshot.failed_nodes} node(s) failed")

        return "\n".join(lines)

    def _format_duration(self, seconds: float) -> str:
        """Format seconds into human-readable duration."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"

    def render_mermaid(
        self,
        graph: Optional[Dict[str, Any]] = None,
        include_status: bool = True,
    ) -> str:
        """
        Render task graph as Mermaid diagram.

        This method is migrated from scheduler.py for centralized visualization.

        Args:
            graph: Task graph dictionary (reads from file if None)
            include_status: If True, include status colors

        Returns:
            Mermaid diagram string
        """
        if graph is None:
            graph = self._read_taskgraph()

        if graph is None:
            return "graph TD\n    no_graph[No active task graph]"

        lines = ["graph TD"]
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        # Track nodes by status for styling
        status_nodes: Dict[str, List[str]] = {
            "done": [],
            "running": [],
            "failed": [],
        }

        # Render nodes
        for node in nodes:
            node_id = node["id"]
            role = node.get("role", "unknown")
            title = node.get("title", node_id)
            emoji = ROLE_EMOJI.get(role, "")

            # Format: node_id[emoji: title]
            label = f"{emoji}: {title}" if emoji else title
            lines.append(f"    {node_id}[{label}]")

            # Track status for styling
            status = node.get("status", "pending")
            if status in status_nodes:
                status_nodes[status].append(node_id)

        # Add blank line before edges
        if edges:
            lines.append("")

        # Render edges
        for edge in edges:
            from_id = edge["from"]
            to_id = edge["to"]
            condition = edge.get("condition", "on_success")

            if condition == "on_success":
                lines.append(f"    {from_id} --> {to_id}")
            elif condition == "on_failure":
                lines.append(f"    {from_id} -->|on_failure| {to_id}")
            elif condition == "always":
                lines.append(f"    {from_id} -->|always| {to_id}")
            else:
                lines.append(f"    {from_id} -->|{condition}| {to_id}")

        # Add status styling if requested
        if include_status:
            lines.append("")
            lines.append("    classDef done fill:#90EE90")
            lines.append("    classDef running fill:#87CEEB")
            lines.append("    classDef failed fill:#FFB6C1")

            # Apply classes to nodes
            for status, node_ids in status_nodes.items():
                if node_ids:
                    lines.append(f"    class {','.join(node_ids)} {status}")

        return "\n".join(lines)

    def render_compact(self, snapshot: Optional[ProgressSnapshot] = None) -> str:
        """
        Render a single-line compact progress indicator.

        Args:
            snapshot: ProgressSnapshot to render (collects if None)

        Returns:
            Single-line progress string like:
            "[Fix] 60% (3/5) Phase 2/3 | 1m 5s"
        """
        if snapshot is None:
            snapshot = self.collect_snapshot()

        if snapshot is None:
            return "[No task]"

        parts = [
            f"[{snapshot.track.title()}]",
            f"{snapshot.progress_percent:.0f}%",
            f"({snapshot.completed_nodes}/{snapshot.total_nodes})",
            f"Phase {snapshot.current_phase + 1}/{snapshot.total_phases}",
        ]

        if snapshot.elapsed_sec is not None:
            parts.append(f"| {self._format_duration(snapshot.elapsed_sec)}")

        if snapshot.failed_nodes > 0:
            parts.append(f"[!{snapshot.failed_nodes} failed]")

        return " ".join(parts)


def get_default_visualizer() -> Visualizer:
    """Get a Visualizer with default paths."""
    return Visualizer()


def render_progress() -> str:
    """Convenience function to render current progress."""
    visualizer = get_default_visualizer()
    return visualizer.render_terminal()


def render_mermaid() -> str:
    """Convenience function to render current graph as Mermaid."""
    visualizer = get_default_visualizer()
    return f"```mermaid\n{visualizer.render_mermaid()}\n```"


# ============================================================
# Append-Style Progress Display (追加式进度显示)
# ============================================================

# Status symbols for progress display
PROGRESS_STATUS_SYMBOLS = {
    "done": "\u2713",      # checkmark
    "running": "\u25b6",   # play triangle
    "pending": "\u25cb",   # empty circle
    "failed": "\u2717",    # x mark
}


def render_progress_header(track: str, phases: List[Dict[str, Any]]) -> str:
    """
    Render the initial progress header showing the full DAG flow.

    Args:
        track: Track name (fix, feature, refactor)
        phases: List of phase definitions from track template

    Returns:
        Progress header string

    Example output:
        Progress: [ear+eye] -> [mind] -> [body] -> [tongue+nose]
        --------------------------------------------------------
    """
    # Build phase display
    phase_parts = []
    for phase in phases:
        nodes = phase.get("nodes", [])
        if not nodes:
            continue
        # Extract role names from node IDs (e.g., "eye_explore" -> "eye")
        roles = []
        for node_id in nodes:
            role = node_id.split("_")[0] if "_" in node_id else node_id
            emoji = ROLE_EMOJI.get(role, "")
            roles.append(f"{emoji}{role}" if emoji else role)
        if phase.get("parallel") and len(roles) > 1:
            phase_parts.append(f"[{'+'.join(roles)}]")
        else:
            phase_parts.append(f"[{'+'.join(roles)}]")

    flow_str = " -> ".join(phase_parts)
    header = f"Progress: {flow_str}"
    separator = "-" * len(header)

    return f"{header}\n{separator}"


def render_progress_line(
    phase_index: int,
    phase_nodes: List[str],
    node_statuses: Dict[str, str],
    phase_status: str = "pending",
) -> str:
    """
    Render a single progress line for a phase.

    Args:
        phase_index: The phase number (0-indexed)
        phase_nodes: List of node IDs in this phase
        node_statuses: Dict of node_id -> status
        phase_status: Overall phase status (pending/running/done/failed)

    Returns:
        Single line progress string

    Example output:
        Phase 0: eye completed | nose completed
        Phase 1: mind running...
        Phase 2: body pending
    """
    symbol = PROGRESS_STATUS_SYMBOLS.get(phase_status, "?")

    # Build node status descriptions
    node_parts = []
    for node_id in phase_nodes:
        role = node_id.split("_")[0] if "_" in node_id else node_id
        emoji = ROLE_EMOJI.get(role, "")
        status = node_statuses.get(node_id, "pending")

        if status == "done":
            status_text = "completed"
        elif status == "running":
            status_text = "running..."
        elif status == "failed":
            status_text = "FAILED"
        else:
            status_text = "pending"

        node_parts.append(f"{emoji}{role} {status_text}")

    nodes_str = " | ".join(node_parts)
    return f"{symbol} Phase {phase_index}: {nodes_str}"


def render_full_progress(
    graph: Optional[Dict[str, Any]] = None,
    current_phase: Optional[int] = None,
) -> str:
    """
    Render the full append-style progress display.

    Args:
        graph: Task graph dictionary (reads from file if None)
        current_phase: Override current phase (auto-detect if None)

    Returns:
        Full progress display string

    Example output:
        Progress: [ear+eye] -> [mind] -> [body] -> [tongue+nose]
        --------------------------------------------------------
        Phase 0: ear completed | eye completed
        Phase 1: mind running...
        Phase 2: body pending
        Phase 3: tongue+nose pending
    """
    visualizer = get_default_visualizer()

    if graph is None:
        graph = visualizer._read_taskgraph()

    if graph is None:
        return "No active task graph"

    # Get track and phases from metadata
    track = graph.get("track", "unknown")
    metadata = graph.get("metadata", {})
    phases = metadata.get("phases", [])

    if not phases:
        return "No phase information available"

    # Build node status map
    node_statuses = {}
    for node in graph.get("nodes", []):
        node_statuses[node["id"]] = node.get("status", "pending")

    lines = []

    # Add header
    lines.append(render_progress_header(track, phases))

    # Determine current phase if not provided
    if current_phase is None:
        for i, phase in enumerate(phases):
            phase_nodes = phase.get("nodes", [])
            all_done = all(node_statuses.get(nid) == "done" for nid in phase_nodes)
            any_running = any(node_statuses.get(nid) == "running" for nid in phase_nodes)
            if any_running or not all_done:
                current_phase = i
                break
        else:
            current_phase = len(phases) - 1

    # Render each phase
    for i, phase in enumerate(phases):
        phase_nodes = phase.get("nodes", [])
        if not phase_nodes:
            continue

        # Determine phase status
        all_done = all(node_statuses.get(nid) == "done" for nid in phase_nodes)
        any_running = any(node_statuses.get(nid) == "running" for nid in phase_nodes)
        any_failed = any(node_statuses.get(nid) == "failed" for nid in phase_nodes)

        if any_failed:
            phase_status = "failed"
        elif all_done:
            phase_status = "done"
        elif any_running:
            phase_status = "running"
        else:
            phase_status = "pending"

        lines.append(render_progress_line(i, phase_nodes, node_statuses, phase_status))

    return "\n".join(lines)
