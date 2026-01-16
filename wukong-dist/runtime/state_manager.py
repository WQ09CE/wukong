"""
Wukong StateManager - Atomic state management via state.json

Provides safe, atomic read/write operations for the runtime state.
Uses write-to-temp + rename pattern for crash safety.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class RuntimeState:
    """Represents the current runtime state of Wukong."""

    # Current task graph ID being executed
    current_graph_id: Optional[str] = None

    # Current execution phase (0-indexed)
    current_phase: int = 0

    # List of currently active node IDs
    active_nodes: list = field(default_factory=list)

    # List of completed node IDs
    completed_nodes: list = field(default_factory=list)

    # List of failed node IDs
    failed_nodes: list = field(default_factory=list)

    # Overall status: idle, running, paused, completed, aborted
    status: str = "idle"

    # Last update timestamp
    updated_at: Optional[str] = None

    # Session ID for current execution
    session_id: Optional[str] = None

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "current_graph_id": self.current_graph_id,
            "current_phase": self.current_phase,
            "active_nodes": self.active_nodes,
            "completed_nodes": self.completed_nodes,
            "failed_nodes": self.failed_nodes,
            "status": self.status,
            "updated_at": self.updated_at,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuntimeState":
        """Create RuntimeState from dictionary."""
        return cls(
            current_graph_id=data.get("current_graph_id"),
            current_phase=data.get("current_phase", 0),
            active_nodes=data.get("active_nodes", []),
            completed_nodes=data.get("completed_nodes", []),
            failed_nodes=data.get("failed_nodes", []),
            status=data.get("status", "idle"),
            updated_at=data.get("updated_at"),
            session_id=data.get("session_id"),
            metadata=data.get("metadata", {}),
        )


class StateManager:
    """
    Manages runtime state with atomic read/write operations.

    Uses write-to-temp + rename pattern to ensure crash safety:
    - Write state to a temporary file
    - Atomically rename temp file to target file
    - This ensures the state file is never corrupted mid-write

    Example:
        manager = StateManager(Path("~/.wukong/state.json"))
        state = manager.get_state()
        state["status"] = "running"
        manager.set_state(state)
    """

    def __init__(self, state_file: Path):
        """
        Initialize the StateManager.

        Args:
            state_file: Path to the state.json file
        """
        self.state_file = Path(state_file).expanduser()

        # Ensure parent directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()

    def _atomic_write(self, data: Dict[str, Any]) -> None:
        """
        Atomically write data to the state file.

        Uses write-to-temp + rename for crash safety.
        """
        # Create temp file in same directory (for atomic rename to work)
        temp_dir = self.state_file.parent

        # Write to temp file
        fd, temp_path = tempfile.mkstemp(
            suffix=".json.tmp",
            dir=temp_dir,
            prefix="state_"
        )

        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename (POSIX guarantees atomicity for rename)
            os.replace(temp_path, self.state_file)
        except Exception:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def get_state(self) -> Dict[str, Any]:
        """
        Read the current state.

        Returns:
            Current state as a dictionary.
            Returns default empty state if file doesn't exist.
        """
        if not self.state_file.exists():
            return RuntimeState().to_dict()

        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Return default state on error
            return RuntimeState().to_dict()

    def get_runtime_state(self) -> RuntimeState:
        """
        Read the current state as a RuntimeState object.

        Returns:
            Current state as RuntimeState dataclass.
        """
        return RuntimeState.from_dict(self.get_state())

    def set_state(self, state: Dict[str, Any]) -> None:
        """
        Set the entire state (atomic write).

        Args:
            state: New state dictionary to save
        """
        # Update timestamp
        state["updated_at"] = self._get_timestamp()
        self._atomic_write(state)

    def update_state(self, **kwargs) -> Dict[str, Any]:
        """
        Update specific fields in the state.

        Args:
            **kwargs: Fields to update

        Returns:
            The updated state
        """
        state = self.get_state()
        state.update(kwargs)
        self.set_state(state)
        return state

    def reset_state(self) -> Dict[str, Any]:
        """
        Reset state to default values.

        Returns:
            The reset state
        """
        state = RuntimeState().to_dict()
        self.set_state(state)
        return state

    def start_graph(self, graph_id: str, session_id: str) -> Dict[str, Any]:
        """
        Start execution of a task graph.

        Args:
            graph_id: ID of the task graph to execute
            session_id: Session ID for this execution

        Returns:
            Updated state
        """
        return self.update_state(
            current_graph_id=graph_id,
            session_id=session_id,
            status="running",
            current_phase=0,
            active_nodes=[],
            completed_nodes=[],
            failed_nodes=[],
        )

    def complete_graph(self) -> Dict[str, Any]:
        """
        Mark current graph as completed.

        Returns:
            Updated state
        """
        return self.update_state(
            status="completed",
            active_nodes=[],
        )

    def abort_graph(self, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Abort current graph execution.

        Args:
            reason: Optional reason for abortion

        Returns:
            Updated state
        """
        state = self.get_state()
        metadata = state.get("metadata", {})
        if reason:
            metadata["abort_reason"] = reason

        return self.update_state(
            status="aborted",
            active_nodes=[],
            metadata=metadata,
        )

    def activate_node(self, node_id: str) -> Dict[str, Any]:
        """
        Mark a node as active (running).

        Args:
            node_id: ID of the node to activate

        Returns:
            Updated state
        """
        state = self.get_state()
        active = state.get("active_nodes", [])
        if node_id not in active:
            active.append(node_id)
        return self.update_state(active_nodes=active)

    def complete_node(self, node_id: str) -> Dict[str, Any]:
        """
        Mark a node as completed.

        Args:
            node_id: ID of the completed node

        Returns:
            Updated state
        """
        state = self.get_state()

        # Remove from active
        active = state.get("active_nodes", [])
        if node_id in active:
            active.remove(node_id)

        # Add to completed
        completed = state.get("completed_nodes", [])
        if node_id not in completed:
            completed.append(node_id)

        return self.update_state(
            active_nodes=active,
            completed_nodes=completed,
        )

    def fail_node(self, node_id: str) -> Dict[str, Any]:
        """
        Mark a node as failed.

        Args:
            node_id: ID of the failed node

        Returns:
            Updated state
        """
        state = self.get_state()

        # Remove from active
        active = state.get("active_nodes", [])
        if node_id in active:
            active.remove(node_id)

        # Add to failed
        failed = state.get("failed_nodes", [])
        if node_id not in failed:
            failed.append(node_id)

        return self.update_state(
            active_nodes=active,
            failed_nodes=failed,
        )

    def advance_phase(self) -> Dict[str, Any]:
        """
        Advance to the next execution phase.

        Returns:
            Updated state
        """
        state = self.get_state()
        current = state.get("current_phase", 0)
        return self.update_state(current_phase=current + 1)

    def pause_graph(self) -> Dict[str, Any]:
        """
        Pause the current graph execution.

        Returns:
            Updated state
        """
        return self.update_state(status="paused")

    def get_interrupted_nodes(self) -> list:
        """
        Get list of nodes that were running when execution was interrupted.

        These are nodes in the active_nodes list that should be re-scheduled.

        Returns:
            List of node IDs that were interrupted
        """
        state = self.get_state()
        return state.get("active_nodes", [])

    def prepare_for_resume(self) -> Dict[str, Any]:
        """
        Prepare state for resuming execution.

        Moves active (interrupted) nodes back to a state where they can
        be re-scheduled. Returns information about what was recovered.

        Returns:
            Dictionary with recovery information:
            - resumed_nodes: List of node IDs that were re-queued
            - status: New status ('running')
            - graph_id: Current graph ID
        """
        state = self.get_state()

        if not state.get("current_graph_id"):
            return {
                "success": False,
                "error": "No task to resume",
            }

        current_status = state.get("status", "idle")
        if current_status == "completed":
            return {
                "success": False,
                "error": "Task is already completed",
            }

        if current_status == "running" and not state.get("active_nodes"):
            return {
                "success": False,
                "error": "Task is already running with no interrupted nodes",
            }

        # Get interrupted nodes (nodes that were running)
        interrupted = state.get("active_nodes", [])

        # Update state to running, clear active_nodes
        # (they will be re-added when scheduled again)
        self.update_state(
            status="running",
            active_nodes=[],
        )

        return {
            "success": True,
            "resumed_nodes": interrupted,
            "status": "running",
            "graph_id": state.get("current_graph_id"),
        }

    def record_retry(self, node_id: str) -> Dict[str, Any]:
        """
        Record a retry attempt for a node.

        Updates the metadata to track retry counts.

        Args:
            node_id: ID of the node being retried

        Returns:
            Updated state with retry count
        """
        state = self.get_state()
        metadata = state.get("metadata", {})

        # Initialize or update retry tracking
        if "retry_counts" not in metadata:
            metadata["retry_counts"] = {}

        current_count = metadata["retry_counts"].get(node_id, 0)
        metadata["retry_counts"][node_id] = current_count + 1

        # Remove from failed nodes if present
        failed = state.get("failed_nodes", [])
        if node_id in failed:
            failed.remove(node_id)

        return self.update_state(
            metadata=metadata,
            failed_nodes=failed,
        )

    def get_retry_count(self, node_id: str) -> int:
        """
        Get the retry count for a node.

        Args:
            node_id: ID of the node

        Returns:
            Number of retries for this node
        """
        state = self.get_state()
        metadata = state.get("metadata", {})
        retry_counts = metadata.get("retry_counts", {})
        return retry_counts.get(node_id, 0)
