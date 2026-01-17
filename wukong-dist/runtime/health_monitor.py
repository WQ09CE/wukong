"""
Wukong HealthMonitor - Subagent health monitoring via heartbeat tracking

Tracks heartbeats from subagents and detects stalled/timeout conditions.
Uses configurable thresholds based on subagent cost tier.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class HealthStatus(Enum):
    """Health status of a subagent node."""
    HEALTHY = "healthy"
    STALLED = "stalled"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class HeartbeatConfig:
    """Configuration for heartbeat thresholds per cost tier."""

    # Heartbeat interval in seconds
    heartbeat_interval_sec: int

    # Warning threshold in seconds (triggers STALLED)
    warning_threshold_sec: int

    # Timeout threshold in seconds (triggers TIMEOUT)
    timeout_threshold_sec: int


# Default configurations by cost tier
# 眼/鼻 (CHEAP, background): longer intervals
# 耳/舌 (MEDIUM): medium intervals
# 身/意 (EXPENSIVE, foreground): shorter intervals
DEFAULT_CONFIGS: Dict[str, HeartbeatConfig] = {
    "cheap": HeartbeatConfig(
        heartbeat_interval_sec=60,     # 60s interval
        warning_threshold_sec=180,      # 3 min warning
        timeout_threshold_sec=300,      # 5 min timeout
    ),
    "medium": HeartbeatConfig(
        heartbeat_interval_sec=45,     # 45s interval
        warning_threshold_sec=120,      # 2 min warning
        timeout_threshold_sec=240,      # 4 min timeout
    ),
    "expensive": HeartbeatConfig(
        heartbeat_interval_sec=30,     # 30s interval
        warning_threshold_sec=90,       # 1.5 min warning
        timeout_threshold_sec=120,      # 2 min timeout
    ),
}

# Mapping from role to cost tier
ROLE_TO_TIER: Dict[str, str] = {
    "eye": "cheap",
    "nose": "cheap",
    "ear": "medium",
    "tongue": "medium",
    "body": "expensive",
    "mind": "expensive",
}


@dataclass
class HeartbeatRecord:
    """A single heartbeat record from a subagent."""

    node_id: str
    timestamp: str
    progress: Dict[str, Any] = field(default_factory=dict)
    status: str = "running"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "progress": self.progress,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HeartbeatRecord":
        """Create from dictionary."""
        return cls(
            node_id=data["node_id"],
            timestamp=data["timestamp"],
            progress=data.get("progress", {}),
            status=data.get("status", "running"),
        )


@dataclass
class NodeHealthReport:
    """Health report for a single node."""

    node_id: str
    status: HealthStatus
    last_heartbeat: Optional[str]
    seconds_since_heartbeat: Optional[float]
    progress: Dict[str, Any]
    cost_tier: str
    warning_threshold_sec: int
    timeout_threshold_sec: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat,
            "seconds_since_heartbeat": self.seconds_since_heartbeat,
            "progress": self.progress,
            "cost_tier": self.cost_tier,
            "warning_threshold_sec": self.warning_threshold_sec,
            "timeout_threshold_sec": self.timeout_threshold_sec,
        }


@dataclass
class HealthReport:
    """Overall health report for all monitored nodes."""

    timestamp: str
    healthy_count: int
    stalled_count: int
    timeout_count: int
    nodes: Dict[str, NodeHealthReport]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "summary": {
                "healthy": self.healthy_count,
                "stalled": self.stalled_count,
                "timeout": self.timeout_count,
                "total": len(self.nodes),
            },
            "nodes": {
                node_id: report.to_dict()
                for node_id, report in self.nodes.items()
            },
        }


class HealthMonitor:
    """
    Monitors health of subagent nodes via heartbeat tracking.

    Uses state.json for heartbeat storage and events.jsonl for alerts.
    Supports configurable thresholds based on cost tier.

    Example:
        monitor = HealthMonitor(state_file, events_file)
        monitor.record_heartbeat("eye_explore", {"files_scanned": 10})
        report = monitor.check_health()
        stalled = monitor.get_stalled_nodes()
    """

    def __init__(
        self,
        state_file: Path,
        events_file: Path,
        taskgraph_file: Optional[Path] = None,
        configs: Optional[Dict[str, HeartbeatConfig]] = None,
    ):
        """
        Initialize the HealthMonitor.

        Args:
            state_file: Path to state.json file
            events_file: Path to events.jsonl file
            taskgraph_file: Path to taskgraph.json file (for node metadata)
            configs: Custom heartbeat configurations by tier (uses defaults if None)
        """
        self.state_file = Path(state_file).expanduser()
        self.events_file = Path(events_file).expanduser()
        self.taskgraph_file = Path(taskgraph_file).expanduser() if taskgraph_file else None
        self.configs = configs or DEFAULT_CONFIGS

        # Ensure directories exist
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.events_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()

    def _parse_timestamp(self, timestamp: str) -> datetime:
        """Parse ISO 8601 timestamp to datetime object."""
        # Handle both Z suffix and +00:00 format
        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"
        return datetime.fromisoformat(timestamp)

    def _load_state(self) -> Dict[str, Any]:
        """Load current state from state.json."""
        if not self.state_file.exists():
            return {}

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_state(self, state: Dict[str, Any]) -> None:
        """Save state to state.json atomically."""
        import tempfile
        import os

        temp_dir = self.state_file.parent
        fd, temp_path = tempfile.mkstemp(
            suffix=".json.tmp",
            dir=temp_dir,
            prefix="state_"
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, self.state_file)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def _load_taskgraph(self) -> Optional[Dict[str, Any]]:
        """Load task graph for node metadata."""
        if not self.taskgraph_file or not self.taskgraph_file.exists():
            return None

        try:
            with open(self.taskgraph_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _get_node_tier(self, node_id: str) -> str:
        """
        Get cost tier for a node.

        Tries to determine from taskgraph, falls back to role prefix.
        """
        # Try to get from taskgraph
        taskgraph = self._load_taskgraph()
        if taskgraph:
            for node in taskgraph.get("nodes", []):
                if node.get("id") == node_id:
                    constraints = node.get("constraints", {})
                    tier = constraints.get("cost_tier")
                    if tier:
                        return tier.lower()
                    # Fall back to role
                    role = node.get("role", "")
                    if role in ROLE_TO_TIER:
                        return ROLE_TO_TIER[role]

        # Fall back to parsing node_id prefix
        for role, tier in ROLE_TO_TIER.items():
            if node_id.startswith(role):
                return tier

        # Default to medium
        return "medium"

    def _get_config(self, node_id: str) -> HeartbeatConfig:
        """Get heartbeat config for a node based on its tier."""
        tier = self._get_node_tier(node_id)
        return self.configs.get(tier, self.configs["medium"])

    def _write_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        node_id: Optional[str] = None,
    ) -> None:
        """Write an event to the events file."""
        import uuid

        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "type": event_type,
            "timestamp": self._get_timestamp(),
            "session_id": "health_monitor",
            "payload": payload,
            "source": "system",
        }

        if node_id:
            event["node_id"] = node_id

        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def record_heartbeat(
        self,
        node_id: str,
        progress: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a heartbeat from a subagent.

        Args:
            node_id: ID of the node sending heartbeat
            progress: Optional progress information (e.g., files_scanned, lines_written)
        """
        state = self._load_state()

        # Initialize heartbeats dict if needed
        if "heartbeats" not in state:
            state["heartbeats"] = {}

        # Create heartbeat record
        record = HeartbeatRecord(
            node_id=node_id,
            timestamp=self._get_timestamp(),
            progress=progress or {},
            status="running",
        )

        # Store heartbeat
        state["heartbeats"][node_id] = record.to_dict()

        # Update timestamp
        state["updated_at"] = self._get_timestamp()

        self._save_state(state)

        # Write progress event
        self._write_event(
            "SubagentProgress",
            {
                "node_id": node_id,
                "progress": progress or {},
            },
            node_id=node_id,
        )

    def check_health(self) -> HealthReport:
        """
        Check health status of all monitored nodes.

        Returns:
            HealthReport with status of all nodes
        """
        state = self._load_state()
        heartbeats = state.get("heartbeats", {})
        active_nodes = state.get("active_nodes", [])

        now = datetime.now(timezone.utc)
        nodes: Dict[str, NodeHealthReport] = {}
        healthy_count = 0
        stalled_count = 0
        timeout_count = 0

        # Check all nodes that have heartbeats or are active
        all_node_ids = set(heartbeats.keys()) | set(active_nodes)

        for node_id in all_node_ids:
            config = self._get_config(node_id)
            tier = self._get_node_tier(node_id)

            heartbeat_data = heartbeats.get(node_id)

            if not heartbeat_data:
                # Node is active but never sent heartbeat
                status = HealthStatus.UNKNOWN
                last_heartbeat = None
                seconds_since = None
                progress = {}
            else:
                record = HeartbeatRecord.from_dict(heartbeat_data)
                last_heartbeat = record.timestamp
                progress = record.progress

                last_time = self._parse_timestamp(record.timestamp)
                seconds_since = (now - last_time).total_seconds()

                # Determine status based on thresholds
                if seconds_since > config.timeout_threshold_sec:
                    status = HealthStatus.TIMEOUT
                    timeout_count += 1
                elif seconds_since > config.warning_threshold_sec:
                    status = HealthStatus.STALLED
                    stalled_count += 1
                else:
                    status = HealthStatus.HEALTHY
                    healthy_count += 1

            report = NodeHealthReport(
                node_id=node_id,
                status=status,
                last_heartbeat=last_heartbeat,
                seconds_since_heartbeat=seconds_since,
                progress=progress,
                cost_tier=tier,
                warning_threshold_sec=config.warning_threshold_sec,
                timeout_threshold_sec=config.timeout_threshold_sec,
            )
            nodes[node_id] = report

            # Emit events for stalled/timeout nodes
            if status == HealthStatus.STALLED:
                self._write_event(
                    "SubagentStalled",
                    {
                        "node_id": node_id,
                        "seconds_since_heartbeat": seconds_since,
                        "warning_threshold_sec": config.warning_threshold_sec,
                    },
                    node_id=node_id,
                )
            elif status == HealthStatus.TIMEOUT:
                self._write_event(
                    "SubagentTimeout",
                    {
                        "node_id": node_id,
                        "seconds_since_heartbeat": seconds_since,
                        "timeout_threshold_sec": config.timeout_threshold_sec,
                    },
                    node_id=node_id,
                )

        return HealthReport(
            timestamp=self._get_timestamp(),
            healthy_count=healthy_count,
            stalled_count=stalled_count,
            timeout_count=timeout_count,
            nodes=nodes,
        )

    def get_stalled_nodes(self) -> List[str]:
        """
        Get list of nodes in STALLED state.

        Returns:
            List of node IDs that are stalled (warning threshold exceeded)
        """
        report = self.check_health()
        return [
            node_id
            for node_id, node_report in report.nodes.items()
            if node_report.status == HealthStatus.STALLED
        ]

    def get_timeout_nodes(self) -> List[str]:
        """
        Get list of nodes in TIMEOUT state.

        Returns:
            List of node IDs that have timed out
        """
        report = self.check_health()
        return [
            node_id
            for node_id, node_report in report.nodes.items()
            if node_report.status == HealthStatus.TIMEOUT
        ]

    def get_node_health(self, node_id: str) -> Optional[NodeHealthReport]:
        """
        Get health status for a specific node.

        Args:
            node_id: ID of the node to check

        Returns:
            NodeHealthReport or None if node not found
        """
        report = self.check_health()
        return report.nodes.get(node_id)

    def clear_heartbeat(self, node_id: str) -> bool:
        """
        Clear heartbeat record for a node (e.g., when node completes).

        Args:
            node_id: ID of the node to clear

        Returns:
            True if heartbeat was cleared, False if not found
        """
        state = self._load_state()
        heartbeats = state.get("heartbeats", {})

        if node_id in heartbeats:
            del heartbeats[node_id]
            state["heartbeats"] = heartbeats
            state["updated_at"] = self._get_timestamp()
            self._save_state(state)
            return True

        return False

    def clear_all_heartbeats(self) -> int:
        """
        Clear all heartbeat records.

        Returns:
            Number of heartbeats cleared
        """
        state = self._load_state()
        heartbeats = state.get("heartbeats", {})
        count = len(heartbeats)

        state["heartbeats"] = {}
        state["updated_at"] = self._get_timestamp()
        self._save_state(state)

        return count
