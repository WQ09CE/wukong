"""
Wukong EventBus - Event-driven communication via events.jsonl

Events are appended to a JSONL file for durability and auditability.
Each event follows the event.schema.json specification.
"""

import json
import uuid
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


# Valid event types from event.schema.json
EVENT_TYPES = {
    "UserPromptSubmit",
    "TaskGraphCreated",
    "NodeScheduled",
    "SubagentStart",
    "SubagentProgress",
    "SubagentStop",
    "NodeCompleted",
    "NodeFailed",
    "NodeBlocked",
    "ValidationPass",
    "ValidationFail",
    "Stop",
    "PreCompact",
    "ContextSnapshot",
    "AnchorExtracted",
}

# Valid event sources
EVENT_SOURCES = {"user", "scheduler", "subagent", "validator", "system"}


@dataclass
class Event:
    """Represents a single event in the Wukong system."""

    event_id: str
    type: str
    timestamp: str
    session_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    node_id: Optional[str] = None
    graph_id: Optional[str] = None
    source: str = "system"
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary, excluding None values."""
        result = {
            "event_id": self.event_id,
            "type": self.type,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "payload": self.payload,
            "source": self.source,
        }
        if self.node_id is not None:
            result["node_id"] = self.node_id
        if self.graph_id is not None:
            result["graph_id"] = self.graph_id
        if self.correlation_id is not None:
            result["correlation_id"] = self.correlation_id
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create an Event from a dictionary."""
        return cls(
            event_id=data["event_id"],
            type=data["type"],
            timestamp=data["timestamp"],
            session_id=data["session_id"],
            payload=data.get("payload", {}),
            node_id=data.get("node_id"),
            graph_id=data.get("graph_id"),
            source=data.get("source", "system"),
            correlation_id=data.get("correlation_id"),
        )


class EventBus:
    """
    Event bus for Wukong system communication.

    Events are persisted to a JSONL file (one JSON object per line)
    for durability and auditability.

    Example:
        bus = EventBus(Path("~/.wukong/events.jsonl"))
        event_id = bus.write_event(
            "UserPromptSubmit",
            {"prompt": "Fix the bug"},
            session_id="sess_123"
        )
        events = bus.read_events(filter_type="UserPromptSubmit")
    """

    def __init__(self, events_file: Path, session_id: Optional[str] = None):
        """
        Initialize the EventBus.

        Args:
            events_file: Path to the events.jsonl file
            session_id: Default session ID for events (auto-generated if not provided)
        """
        self.events_file = Path(events_file).expanduser()
        self.session_id = session_id or self._generate_session_id()

        # Ensure parent directory exists
        self.events_file.parent.mkdir(parents=True, exist_ok=True)

    def _generate_event_id(self) -> str:
        """Generate a unique event ID matching pattern ^evt_[a-z0-9]+$."""
        return f"evt_{uuid.uuid4().hex[:12]}"

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"sess_{uuid.uuid4().hex[:8]}"

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()

    def write_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        *,
        node_id: Optional[str] = None,
        graph_id: Optional[str] = None,
        source: str = "system",
        correlation_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Write an event to the event log.

        Args:
            event_type: Type of event (must be in EVENT_TYPES)
            payload: Event-specific data
            node_id: Associated node ID (optional)
            graph_id: Associated task graph ID (optional)
            source: Event source (default: "system")
            correlation_id: ID for correlating related events (optional)
            session_id: Override default session ID (optional)

        Returns:
            The generated event_id

        Raises:
            ValueError: If event_type or source is invalid
        """
        # Validate event type
        if event_type not in EVENT_TYPES:
            raise ValueError(
                f"Invalid event type: {event_type}. "
                f"Must be one of: {sorted(EVENT_TYPES)}"
            )

        # Validate source
        if source not in EVENT_SOURCES:
            raise ValueError(
                f"Invalid source: {source}. "
                f"Must be one of: {sorted(EVENT_SOURCES)}"
            )

        # Create event
        event = Event(
            event_id=self._generate_event_id(),
            type=event_type,
            timestamp=self._get_timestamp(),
            session_id=session_id or self.session_id,
            payload=payload,
            node_id=node_id,
            graph_id=graph_id,
            source=source,
            correlation_id=correlation_id,
        )

        # Append to file (create if not exists)
        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

        return event.event_id

    def read_events(
        self,
        filter_type: Optional[str] = None,
        filter_node_id: Optional[str] = None,
        filter_graph_id: Optional[str] = None,
        filter_session_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Event]:
        """
        Read events from the event log with optional filtering.

        Args:
            filter_type: Filter by event type
            filter_node_id: Filter by node ID
            filter_graph_id: Filter by graph ID
            filter_session_id: Filter by session ID
            limit: Maximum number of events to return (from end)

        Returns:
            List of matching Event objects
        """
        if not self.events_file.exists():
            return []

        events = []

        with open(self.events_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    event = Event.from_dict(data)

                    # Apply filters
                    if filter_type and event.type != filter_type:
                        continue
                    if filter_node_id and event.node_id != filter_node_id:
                        continue
                    if filter_graph_id and event.graph_id != filter_graph_id:
                        continue
                    if filter_session_id and event.session_id != filter_session_id:
                        continue

                    events.append(event)
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue

        # Apply limit (return last N events)
        if limit and len(events) > limit:
            events = events[-limit:]

        return events

    def get_latest_event(
        self,
        event_type: Optional[str] = None,
        node_id: Optional[str] = None,
        graph_id: Optional[str] = None,
    ) -> Optional[Event]:
        """
        Get the most recent event matching the filters.

        Args:
            event_type: Filter by event type
            node_id: Filter by node ID
            graph_id: Filter by graph ID

        Returns:
            The latest matching Event, or None if no match
        """
        events = self.read_events(
            filter_type=event_type,
            filter_node_id=node_id,
            filter_graph_id=graph_id,
        )
        return events[-1] if events else None

    def get_events_since(self, event_id: str) -> List[Event]:
        """
        Get all events after a specific event ID.

        Args:
            event_id: The event ID to start after

        Returns:
            List of events after the specified event
        """
        events = self.read_events()

        # Find the index of the target event
        for i, event in enumerate(events):
            if event.event_id == event_id:
                return events[i + 1:]

        return []

    def clear_events(self) -> None:
        """Clear all events from the log file."""
        if self.events_file.exists():
            self.events_file.unlink()
