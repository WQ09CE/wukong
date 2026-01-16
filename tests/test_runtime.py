#!/usr/bin/env python3
"""
Wukong Runtime Module Tests

Tests for:
- EventBus: Event-driven communication via events.jsonl
- StateManager: Atomic state management via state.json
- MetricsCollector: Cost and duration tracking
- Scheduler: DAG-based task graph scheduling
- AnchorManager: Anchor management for cross-session knowledge persistence

Run with: python -m pytest tests/test_runtime.py -v
Or: python tests/test_runtime.py
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

# Add runtime directory to path for imports
test_dir = Path(__file__).parent.resolve()
project_root = test_dir.parent
runtime_dir = project_root / "wukong-dist" / "runtime"

if str(runtime_dir) not in sys.path:
    sys.path.insert(0, str(runtime_dir))

from event_bus import Event, EventBus, EVENT_TYPES, EVENT_SOURCES
from state_manager import RuntimeState, StateManager
from metrics import (
    NodeMetrics,
    GraphMetrics,
    MetricsCollector,
    COST_TIERS,
    ROLE_TO_TIER,
)
from scheduler import Scheduler, TRACK_TYPES, NODE_STATUS, GRAPH_STATUS
from anchor_manager import AnchorManager, ANCHOR_TYPES, EVIDENCE_LEVELS


# =============================================================================
# Event Tests
# =============================================================================


class TestEvent(unittest.TestCase):
    """Tests for Event dataclass."""

    def test_event_creation(self):
        """Test creating an Event with all fields."""
        event = Event(
            event_id="evt_abc123",
            type="UserPromptSubmit",
            timestamp="2024-01-15T10:30:00+00:00",
            session_id="sess_xyz",
            payload={"prompt": "Fix the bug"},
            node_id="node_001",
            graph_id="graph_001",
            source="user",
            correlation_id="corr_001",
        )

        self.assertEqual(event.event_id, "evt_abc123")
        self.assertEqual(event.type, "UserPromptSubmit")
        self.assertEqual(event.session_id, "sess_xyz")
        self.assertEqual(event.payload["prompt"], "Fix the bug")
        self.assertEqual(event.node_id, "node_001")
        self.assertEqual(event.graph_id, "graph_001")
        self.assertEqual(event.source, "user")
        self.assertEqual(event.correlation_id, "corr_001")

    def test_event_default_values(self):
        """Test Event with default values for optional fields."""
        event = Event(
            event_id="evt_123",
            type="NodeScheduled",
            timestamp="2024-01-15T10:30:00+00:00",
            session_id="sess_001",
        )

        self.assertEqual(event.payload, {})
        self.assertIsNone(event.node_id)
        self.assertIsNone(event.graph_id)
        self.assertEqual(event.source, "system")
        self.assertIsNone(event.correlation_id)

    def test_event_to_dict(self):
        """Test converting Event to dictionary."""
        event = Event(
            event_id="evt_abc",
            type="SubagentStart",
            timestamp="2024-01-15T12:00:00+00:00",
            session_id="sess_123",
            payload={"role": "eye"},
            node_id="node_01",
            graph_id=None,
            source="scheduler",
        )

        result = event.to_dict()

        self.assertEqual(result["event_id"], "evt_abc")
        self.assertEqual(result["type"], "SubagentStart")
        self.assertEqual(result["timestamp"], "2024-01-15T12:00:00+00:00")
        self.assertEqual(result["session_id"], "sess_123")
        self.assertEqual(result["payload"], {"role": "eye"})
        self.assertEqual(result["node_id"], "node_01")
        self.assertEqual(result["source"], "scheduler")
        # None values should not be included
        self.assertNotIn("graph_id", result)
        self.assertNotIn("correlation_id", result)

    def test_event_from_dict(self):
        """Test creating Event from dictionary."""
        data = {
            "event_id": "evt_xyz",
            "type": "NodeCompleted",
            "timestamp": "2024-01-15T14:00:00+00:00",
            "session_id": "sess_456",
            "payload": {"result": "success"},
            "node_id": "node_02",
            "graph_id": "graph_02",
            "source": "subagent",
            "correlation_id": "corr_02",
        }

        event = Event.from_dict(data)

        self.assertEqual(event.event_id, "evt_xyz")
        self.assertEqual(event.type, "NodeCompleted")
        self.assertEqual(event.payload["result"], "success")
        self.assertEqual(event.node_id, "node_02")
        self.assertEqual(event.graph_id, "graph_02")
        self.assertEqual(event.source, "subagent")
        self.assertEqual(event.correlation_id, "corr_02")

    def test_event_from_dict_with_defaults(self):
        """Test creating Event from dictionary with missing optional fields."""
        data = {
            "event_id": "evt_min",
            "type": "Stop",
            "timestamp": "2024-01-15T15:00:00+00:00",
            "session_id": "sess_789",
        }

        event = Event.from_dict(data)

        self.assertEqual(event.payload, {})
        self.assertIsNone(event.node_id)
        self.assertIsNone(event.graph_id)
        self.assertEqual(event.source, "system")
        self.assertIsNone(event.correlation_id)


# =============================================================================
# EventBus Tests
# =============================================================================


class TestEventBus(unittest.TestCase):
    """Tests for EventBus class."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.events_file = Path(self.temp_dir) / "events.jsonl"
        self.bus = EventBus(self.events_file)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_parent_directory(self):
        """Test that EventBus creates parent directory if it doesn't exist."""
        nested_path = Path(self.temp_dir) / "nested" / "dir" / "events.jsonl"
        bus = EventBus(nested_path)

        self.assertTrue(nested_path.parent.exists())

    def test_init_generates_session_id(self):
        """Test that EventBus generates a session ID if not provided."""
        bus = EventBus(self.events_file)
        self.assertIsNotNone(bus.session_id)
        self.assertTrue(bus.session_id.startswith("sess_"))

    def test_init_uses_provided_session_id(self):
        """Test that EventBus uses provided session ID."""
        bus = EventBus(self.events_file, session_id="my_session")
        self.assertEqual(bus.session_id, "my_session")

    def test_write_event_creates_file(self):
        """Test that write_event creates the events file."""
        self.assertFalse(self.events_file.exists())

        event_id = self.bus.write_event(
            "UserPromptSubmit",
            {"prompt": "Test prompt"},
            source="user",
        )

        self.assertTrue(self.events_file.exists())
        self.assertTrue(event_id.startswith("evt_"))

    def test_write_event_appends_to_file(self):
        """Test that write_event appends events to the file."""
        self.bus.write_event("UserPromptSubmit", {"prompt": "First"}, source="user")
        self.bus.write_event("NodeScheduled", {"node": "node_1"}, source="scheduler")

        with open(self.events_file, "r") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), 2)

        event1 = json.loads(lines[0])
        event2 = json.loads(lines[1])
        self.assertEqual(event1["type"], "UserPromptSubmit")
        self.assertEqual(event2["type"], "NodeScheduled")

    def test_write_event_invalid_type_raises(self):
        """Test that write_event raises ValueError for invalid event type."""
        with self.assertRaises(ValueError) as ctx:
            self.bus.write_event("InvalidEventType", {}, source="system")

        self.assertIn("Invalid event type", str(ctx.exception))
        self.assertIn("InvalidEventType", str(ctx.exception))

    def test_write_event_invalid_source_raises(self):
        """Test that write_event raises ValueError for invalid source."""
        with self.assertRaises(ValueError) as ctx:
            self.bus.write_event("UserPromptSubmit", {}, source="invalid_source")

        self.assertIn("Invalid source", str(ctx.exception))
        self.assertIn("invalid_source", str(ctx.exception))

    def test_write_event_with_all_options(self):
        """Test write_event with all optional parameters."""
        event_id = self.bus.write_event(
            "SubagentStart",
            {"role": "body"},
            node_id="node_123",
            graph_id="graph_456",
            source="scheduler",
            correlation_id="corr_789",
            session_id="custom_session",
        )

        events = self.bus.read_events()
        self.assertEqual(len(events), 1)

        event = events[0]
        self.assertEqual(event.type, "SubagentStart")
        self.assertEqual(event.node_id, "node_123")
        self.assertEqual(event.graph_id, "graph_456")
        self.assertEqual(event.source, "scheduler")
        self.assertEqual(event.correlation_id, "corr_789")
        self.assertEqual(event.session_id, "custom_session")

    def test_read_events_empty_file(self):
        """Test reading events from non-existent file returns empty list."""
        events = self.bus.read_events()
        self.assertEqual(events, [])

    def test_read_events_basic(self):
        """Test basic event reading."""
        self.bus.write_event("UserPromptSubmit", {"prompt": "Test"}, source="user")
        self.bus.write_event("TaskGraphCreated", {"graph_id": "g1"}, source="scheduler")

        events = self.bus.read_events()

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].type, "UserPromptSubmit")
        self.assertEqual(events[1].type, "TaskGraphCreated")

    def test_read_events_with_type_filter(self):
        """Test reading events with type filter."""
        self.bus.write_event("UserPromptSubmit", {}, source="user")
        self.bus.write_event("NodeScheduled", {}, source="scheduler")
        self.bus.write_event("NodeScheduled", {}, source="scheduler")
        self.bus.write_event("NodeCompleted", {}, source="subagent")

        events = self.bus.read_events(filter_type="NodeScheduled")

        self.assertEqual(len(events), 2)
        self.assertTrue(all(e.type == "NodeScheduled" for e in events))

    def test_read_events_with_node_filter(self):
        """Test reading events with node_id filter."""
        self.bus.write_event(
            "NodeScheduled", {}, source="scheduler", node_id="node_A"
        )
        self.bus.write_event(
            "NodeScheduled", {}, source="scheduler", node_id="node_B"
        )
        self.bus.write_event(
            "NodeCompleted", {}, source="subagent", node_id="node_A"
        )

        events = self.bus.read_events(filter_node_id="node_A")

        self.assertEqual(len(events), 2)
        self.assertTrue(all(e.node_id == "node_A" for e in events))

    def test_read_events_with_graph_filter(self):
        """Test reading events with graph_id filter."""
        self.bus.write_event("NodeScheduled", {}, source="scheduler", graph_id="g1")
        self.bus.write_event("NodeScheduled", {}, source="scheduler", graph_id="g2")
        self.bus.write_event("NodeCompleted", {}, source="subagent", graph_id="g1")

        events = self.bus.read_events(filter_graph_id="g1")

        self.assertEqual(len(events), 2)
        self.assertTrue(all(e.graph_id == "g1" for e in events))

    def test_read_events_with_session_filter(self):
        """Test reading events with session_id filter."""
        self.bus.write_event(
            "UserPromptSubmit", {}, source="user", session_id="sess_A"
        )
        self.bus.write_event(
            "UserPromptSubmit", {}, source="user", session_id="sess_B"
        )

        events = self.bus.read_events(filter_session_id="sess_A")

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].session_id, "sess_A")

    def test_read_events_with_limit(self):
        """Test reading events with limit."""
        for i in range(10):
            self.bus.write_event("NodeScheduled", {"index": i}, source="scheduler")

        events = self.bus.read_events(limit=3)

        self.assertEqual(len(events), 3)
        # Should return last 3 events
        self.assertEqual(events[0].payload["index"], 7)
        self.assertEqual(events[2].payload["index"], 9)

    def test_read_events_handles_malformed_json(self):
        """Test that read_events handles malformed JSON lines gracefully."""
        # Write valid events
        self.bus.write_event("UserPromptSubmit", {}, source="user")

        # Inject malformed line
        with open(self.events_file, "a") as f:
            f.write("this is not valid json\n")

        # Write more valid events
        self.bus.write_event("NodeCompleted", {}, source="subagent")

        events = self.bus.read_events()

        # Should only return valid events
        self.assertEqual(len(events), 2)

    def test_get_latest_event(self):
        """Test getting the latest event."""
        self.bus.write_event("UserPromptSubmit", {"order": 1}, source="user")
        self.bus.write_event("NodeScheduled", {"order": 2}, source="scheduler")
        self.bus.write_event("NodeCompleted", {"order": 3}, source="subagent")

        event = self.bus.get_latest_event()

        self.assertIsNotNone(event)
        self.assertEqual(event.type, "NodeCompleted")
        self.assertEqual(event.payload["order"], 3)

    def test_get_latest_event_with_type_filter(self):
        """Test getting the latest event with type filter."""
        self.bus.write_event("NodeScheduled", {"order": 1}, source="scheduler")
        self.bus.write_event("NodeCompleted", {"order": 2}, source="subagent")
        self.bus.write_event("NodeScheduled", {"order": 3}, source="scheduler")

        event = self.bus.get_latest_event(event_type="NodeScheduled")

        self.assertEqual(event.payload["order"], 3)

    def test_get_latest_event_returns_none_if_no_match(self):
        """Test that get_latest_event returns None if no events match."""
        self.bus.write_event("UserPromptSubmit", {}, source="user")

        event = self.bus.get_latest_event(event_type="NodeCompleted")

        self.assertIsNone(event)

    def test_get_events_since(self):
        """Test getting events since a specific event."""
        id1 = self.bus.write_event("UserPromptSubmit", {"order": 1}, source="user")
        id2 = self.bus.write_event("NodeScheduled", {"order": 2}, source="scheduler")
        id3 = self.bus.write_event("NodeCompleted", {"order": 3}, source="subagent")

        events = self.bus.get_events_since(id1)

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].payload["order"], 2)
        self.assertEqual(events[1].payload["order"], 3)

    def test_get_events_since_returns_empty_if_not_found(self):
        """Test get_events_since returns empty list if event_id not found."""
        self.bus.write_event("UserPromptSubmit", {}, source="user")

        events = self.bus.get_events_since("nonexistent_id")

        self.assertEqual(events, [])

    def test_get_events_since_last_event(self):
        """Test get_events_since returns empty for the last event."""
        id1 = self.bus.write_event("UserPromptSubmit", {}, source="user")

        events = self.bus.get_events_since(id1)

        self.assertEqual(events, [])

    def test_clear_events(self):
        """Test clearing all events."""
        self.bus.write_event("UserPromptSubmit", {}, source="user")
        self.bus.write_event("NodeScheduled", {}, source="scheduler")

        self.assertTrue(self.events_file.exists())

        self.bus.clear_events()

        self.assertFalse(self.events_file.exists())

    def test_clear_events_nonexistent_file(self):
        """Test clearing events when file doesn't exist doesn't raise."""
        self.assertFalse(self.events_file.exists())

        # Should not raise
        self.bus.clear_events()


# =============================================================================
# RuntimeState Tests
# =============================================================================


class TestRuntimeState(unittest.TestCase):
    """Tests for RuntimeState dataclass."""

    def test_default_values(self):
        """Test RuntimeState with default values."""
        state = RuntimeState()

        self.assertIsNone(state.current_graph_id)
        self.assertEqual(state.current_phase, 0)
        self.assertEqual(state.active_nodes, [])
        self.assertEqual(state.completed_nodes, [])
        self.assertEqual(state.failed_nodes, [])
        self.assertEqual(state.status, "idle")
        self.assertIsNone(state.updated_at)
        self.assertIsNone(state.session_id)
        self.assertEqual(state.metadata, {})

    def test_custom_values(self):
        """Test RuntimeState with custom values."""
        state = RuntimeState(
            current_graph_id="graph_123",
            current_phase=2,
            active_nodes=["node_1", "node_2"],
            completed_nodes=["node_0"],
            failed_nodes=[],
            status="running",
            updated_at="2024-01-15T10:00:00+00:00",
            session_id="sess_abc",
            metadata={"key": "value"},
        )

        self.assertEqual(state.current_graph_id, "graph_123")
        self.assertEqual(state.current_phase, 2)
        self.assertEqual(len(state.active_nodes), 2)
        self.assertEqual(state.status, "running")

    def test_to_dict(self):
        """Test converting RuntimeState to dictionary."""
        state = RuntimeState(
            current_graph_id="g1",
            current_phase=1,
            active_nodes=["n1"],
            status="running",
        )

        result = state.to_dict()

        self.assertEqual(result["current_graph_id"], "g1")
        self.assertEqual(result["current_phase"], 1)
        self.assertEqual(result["active_nodes"], ["n1"])
        self.assertEqual(result["status"], "running")
        self.assertIn("completed_nodes", result)
        self.assertIn("failed_nodes", result)
        self.assertIn("metadata", result)

    def test_from_dict(self):
        """Test creating RuntimeState from dictionary."""
        data = {
            "current_graph_id": "graph_xyz",
            "current_phase": 3,
            "active_nodes": ["a", "b"],
            "completed_nodes": ["c"],
            "failed_nodes": ["d"],
            "status": "paused",
            "updated_at": "2024-01-15T12:00:00+00:00",
            "session_id": "sess_test",
            "metadata": {"retry_counts": {"a": 1}},
        }

        state = RuntimeState.from_dict(data)

        self.assertEqual(state.current_graph_id, "graph_xyz")
        self.assertEqual(state.current_phase, 3)
        self.assertEqual(state.active_nodes, ["a", "b"])
        self.assertEqual(state.completed_nodes, ["c"])
        self.assertEqual(state.failed_nodes, ["d"])
        self.assertEqual(state.status, "paused")
        self.assertEqual(state.metadata["retry_counts"]["a"], 1)

    def test_from_dict_with_defaults(self):
        """Test creating RuntimeState from partial dictionary."""
        data = {
            "status": "running",
        }

        state = RuntimeState.from_dict(data)

        self.assertIsNone(state.current_graph_id)
        self.assertEqual(state.current_phase, 0)
        self.assertEqual(state.active_nodes, [])
        self.assertEqual(state.status, "running")


# =============================================================================
# StateManager Tests
# =============================================================================


class TestStateManager(unittest.TestCase):
    """Tests for StateManager class."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = Path(self.temp_dir) / "state.json"
        self.manager = StateManager(self.state_file)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_parent_directory(self):
        """Test that StateManager creates parent directory if needed."""
        nested_path = Path(self.temp_dir) / "nested" / "dir" / "state.json"
        manager = StateManager(nested_path)

        self.assertTrue(nested_path.parent.exists())

    def test_get_state_default(self):
        """Test get_state returns default state when file doesn't exist."""
        state = self.manager.get_state()

        self.assertIsNone(state["current_graph_id"])
        self.assertEqual(state["current_phase"], 0)
        self.assertEqual(state["status"], "idle")
        self.assertEqual(state["active_nodes"], [])

    def test_set_state_creates_file(self):
        """Test that set_state creates the state file."""
        self.assertFalse(self.state_file.exists())

        self.manager.set_state({"status": "running"})

        self.assertTrue(self.state_file.exists())

    def test_set_state_and_get_state(self):
        """Test setting and getting state."""
        self.manager.set_state({
            "status": "running",
            "current_graph_id": "g1",
            "current_phase": 2,
        })

        state = self.manager.get_state()

        self.assertEqual(state["status"], "running")
        self.assertEqual(state["current_graph_id"], "g1")
        self.assertEqual(state["current_phase"], 2)

    def test_set_state_updates_timestamp(self):
        """Test that set_state automatically updates the timestamp."""
        self.manager.set_state({"status": "running"})

        state = self.manager.get_state()

        self.assertIsNotNone(state["updated_at"])
        # Check it's a valid ISO timestamp
        datetime.fromisoformat(state["updated_at"].replace("Z", "+00:00"))

    def test_update_state(self):
        """Test updating specific fields in state."""
        self.manager.set_state({
            "status": "idle",
            "current_phase": 0,
        })

        result = self.manager.update_state(status="running", current_phase=1)

        self.assertEqual(result["status"], "running")
        self.assertEqual(result["current_phase"], 1)

    def test_get_runtime_state(self):
        """Test getting state as RuntimeState object."""
        self.manager.set_state({
            "status": "running",
            "current_graph_id": "graph_001",
            "active_nodes": ["node_1"],
        })

        state = self.manager.get_runtime_state()

        self.assertIsInstance(state, RuntimeState)
        self.assertEqual(state.status, "running")
        self.assertEqual(state.current_graph_id, "graph_001")

    def test_atomic_write_basic(self):
        """Test that atomic write creates valid JSON."""
        self.manager.set_state({
            "status": "running",
            "metadata": {"key": "value"},
        })

        # Verify we can read it back as valid JSON
        with open(self.state_file, "r") as f:
            data = json.load(f)

        self.assertEqual(data["status"], "running")
        self.assertEqual(data["metadata"]["key"], "value")

    def test_atomic_write_preserves_unicode(self):
        """Test that atomic write preserves unicode characters."""
        self.manager.set_state({
            "status": "running",
            "metadata": {"message": "Chinese"},
        })

        state = self.manager.get_state()
        self.assertEqual(state["metadata"]["message"], "Chinese")

    def test_reset_state(self):
        """Test resetting state to defaults."""
        self.manager.set_state({
            "status": "running",
            "current_graph_id": "g1",
            "active_nodes": ["n1", "n2"],
        })

        result = self.manager.reset_state()

        self.assertEqual(result["status"], "idle")
        self.assertIsNone(result["current_graph_id"])
        self.assertEqual(result["active_nodes"], [])

    def test_start_graph(self):
        """Test starting a task graph."""
        result = self.manager.start_graph("graph_123", "sess_456")

        self.assertEqual(result["current_graph_id"], "graph_123")
        self.assertEqual(result["session_id"], "sess_456")
        self.assertEqual(result["status"], "running")
        self.assertEqual(result["current_phase"], 0)
        self.assertEqual(result["active_nodes"], [])
        self.assertEqual(result["completed_nodes"], [])
        self.assertEqual(result["failed_nodes"], [])

    def test_complete_graph(self):
        """Test completing a task graph."""
        self.manager.start_graph("g1", "s1")
        self.manager.activate_node("n1")

        result = self.manager.complete_graph()

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["active_nodes"], [])

    def test_abort_graph(self):
        """Test aborting a task graph."""
        self.manager.start_graph("g1", "s1")
        self.manager.activate_node("n1")

        result = self.manager.abort_graph(reason="User cancelled")

        self.assertEqual(result["status"], "aborted")
        self.assertEqual(result["active_nodes"], [])
        self.assertEqual(result["metadata"]["abort_reason"], "User cancelled")

    def test_abort_graph_without_reason(self):
        """Test aborting a graph without providing a reason."""
        self.manager.start_graph("g1", "s1")

        result = self.manager.abort_graph()

        self.assertEqual(result["status"], "aborted")
        self.assertNotIn("abort_reason", result.get("metadata", {}))

    def test_activate_node(self):
        """Test activating a node."""
        self.manager.start_graph("g1", "s1")

        result = self.manager.activate_node("node_001")

        self.assertIn("node_001", result["active_nodes"])

    def test_activate_node_idempotent(self):
        """Test that activating the same node twice doesn't duplicate."""
        self.manager.start_graph("g1", "s1")
        self.manager.activate_node("node_001")
        result = self.manager.activate_node("node_001")

        self.assertEqual(result["active_nodes"].count("node_001"), 1)

    def test_complete_node(self):
        """Test completing a node."""
        self.manager.start_graph("g1", "s1")
        self.manager.activate_node("node_001")

        result = self.manager.complete_node("node_001")

        self.assertNotIn("node_001", result["active_nodes"])
        self.assertIn("node_001", result["completed_nodes"])

    def test_complete_node_idempotent(self):
        """Test that completing the same node twice doesn't duplicate."""
        self.manager.start_graph("g1", "s1")
        self.manager.activate_node("node_001")
        self.manager.complete_node("node_001")
        result = self.manager.complete_node("node_001")

        self.assertEqual(result["completed_nodes"].count("node_001"), 1)

    def test_fail_node(self):
        """Test marking a node as failed."""
        self.manager.start_graph("g1", "s1")
        self.manager.activate_node("node_001")

        result = self.manager.fail_node("node_001")

        self.assertNotIn("node_001", result["active_nodes"])
        self.assertIn("node_001", result["failed_nodes"])

    def test_fail_node_idempotent(self):
        """Test that failing the same node twice doesn't duplicate."""
        self.manager.start_graph("g1", "s1")
        self.manager.activate_node("node_001")
        self.manager.fail_node("node_001")
        result = self.manager.fail_node("node_001")

        self.assertEqual(result["failed_nodes"].count("node_001"), 1)

    def test_node_lifecycle(self):
        """Test complete node lifecycle: pending -> active -> completed."""
        self.manager.start_graph("g1", "s1")

        # Initially no active nodes
        state = self.manager.get_state()
        self.assertEqual(state["active_nodes"], [])

        # Activate
        self.manager.activate_node("n1")
        state = self.manager.get_state()
        self.assertIn("n1", state["active_nodes"])
        self.assertNotIn("n1", state["completed_nodes"])

        # Complete
        self.manager.complete_node("n1")
        state = self.manager.get_state()
        self.assertNotIn("n1", state["active_nodes"])
        self.assertIn("n1", state["completed_nodes"])

    def test_advance_phase(self):
        """Test advancing execution phase."""
        self.manager.start_graph("g1", "s1")
        self.assertEqual(self.manager.get_state()["current_phase"], 0)

        self.manager.advance_phase()
        self.assertEqual(self.manager.get_state()["current_phase"], 1)

        self.manager.advance_phase()
        self.assertEqual(self.manager.get_state()["current_phase"], 2)

    def test_pause_graph(self):
        """Test pausing a graph."""
        self.manager.start_graph("g1", "s1")

        result = self.manager.pause_graph()

        self.assertEqual(result["status"], "paused")

    def test_get_interrupted_nodes(self):
        """Test getting interrupted nodes."""
        self.manager.start_graph("g1", "s1")
        self.manager.activate_node("n1")
        self.manager.activate_node("n2")

        interrupted = self.manager.get_interrupted_nodes()

        self.assertEqual(len(interrupted), 2)
        self.assertIn("n1", interrupted)
        self.assertIn("n2", interrupted)

    def test_prepare_for_resume_success(self):
        """Test preparing for resume with active nodes."""
        self.manager.start_graph("g1", "s1")
        self.manager.activate_node("n1")
        self.manager.activate_node("n2")
        self.manager.pause_graph()

        result = self.manager.prepare_for_resume()

        self.assertTrue(result["success"])
        self.assertEqual(set(result["resumed_nodes"]), {"n1", "n2"})
        self.assertEqual(result["status"], "running")
        self.assertEqual(result["graph_id"], "g1")

        # Verify state is updated
        state = self.manager.get_state()
        self.assertEqual(state["status"], "running")
        self.assertEqual(state["active_nodes"], [])

    def test_prepare_for_resume_no_graph(self):
        """Test prepare_for_resume fails when no graph is active."""
        result = self.manager.prepare_for_resume()

        self.assertFalse(result["success"])
        self.assertIn("No task to resume", result["error"])

    def test_prepare_for_resume_completed_graph(self):
        """Test prepare_for_resume fails when graph is completed."""
        self.manager.start_graph("g1", "s1")
        self.manager.complete_graph()

        result = self.manager.prepare_for_resume()

        self.assertFalse(result["success"])
        self.assertIn("already completed", result["error"])

    def test_prepare_for_resume_running_no_interrupted(self):
        """Test prepare_for_resume fails when running with no interrupted nodes."""
        self.manager.start_graph("g1", "s1")
        # Status is running, but no active nodes

        result = self.manager.prepare_for_resume()

        self.assertFalse(result["success"])
        self.assertIn("no interrupted nodes", result["error"])

    def test_record_retry(self):
        """Test recording a retry attempt."""
        self.manager.start_graph("g1", "s1")
        self.manager.activate_node("n1")
        self.manager.fail_node("n1")

        result = self.manager.record_retry("n1")

        self.assertEqual(result["metadata"]["retry_counts"]["n1"], 1)
        self.assertNotIn("n1", result["failed_nodes"])

    def test_record_retry_increments(self):
        """Test that retry count increments."""
        self.manager.start_graph("g1", "s1")

        self.manager.record_retry("n1")
        self.manager.record_retry("n1")
        result = self.manager.record_retry("n1")

        self.assertEqual(result["metadata"]["retry_counts"]["n1"], 3)

    def test_get_retry_count(self):
        """Test getting retry count for a node."""
        self.manager.start_graph("g1", "s1")

        # Initially zero
        self.assertEqual(self.manager.get_retry_count("n1"), 0)

        self.manager.record_retry("n1")
        self.manager.record_retry("n1")

        self.assertEqual(self.manager.get_retry_count("n1"), 2)

    def test_retry_tracking_multiple_nodes(self):
        """Test retry tracking for multiple nodes."""
        self.manager.start_graph("g1", "s1")

        self.manager.record_retry("n1")
        self.manager.record_retry("n2")
        self.manager.record_retry("n1")
        self.manager.record_retry("n2")
        self.manager.record_retry("n2")

        self.assertEqual(self.manager.get_retry_count("n1"), 2)
        self.assertEqual(self.manager.get_retry_count("n2"), 3)

    def test_handles_corrupted_file(self):
        """Test that get_state handles corrupted JSON file."""
        with open(self.state_file, "w") as f:
            f.write("not valid json {{{")

        state = self.manager.get_state()

        # Should return default state
        self.assertEqual(state["status"], "idle")


# =============================================================================
# NodeMetrics Tests
# =============================================================================


class TestNodeMetrics(unittest.TestCase):
    """Tests for NodeMetrics dataclass."""

    def test_node_metrics_creation(self):
        """Test creating NodeMetrics with all fields."""
        metrics = NodeMetrics(
            node_id="node_001",
            role="body",
            cost_tier="expensive",
            started_at="2024-01-15T10:00:00+00:00",
            completed_at="2024-01-15T10:05:00+00:00",
            duration_sec=300.0,
            estimated_cost=0.10,
            status="done",
            retry_count=1,
        )

        self.assertEqual(metrics.node_id, "node_001")
        self.assertEqual(metrics.role, "body")
        self.assertEqual(metrics.cost_tier, "expensive")
        self.assertEqual(metrics.duration_sec, 300.0)
        self.assertEqual(metrics.estimated_cost, 0.10)
        self.assertEqual(metrics.status, "done")
        self.assertEqual(metrics.retry_count, 1)

    def test_node_metrics_default_values(self):
        """Test NodeMetrics with default values."""
        metrics = NodeMetrics(
            node_id="n1",
            role="eye",
            cost_tier="cheap",
        )

        self.assertIsNone(metrics.started_at)
        self.assertIsNone(metrics.completed_at)
        self.assertIsNone(metrics.duration_sec)
        self.assertEqual(metrics.estimated_cost, 0.0)
        self.assertEqual(metrics.status, "pending")
        self.assertEqual(metrics.retry_count, 0)

    def test_node_metrics_to_dict(self):
        """Test converting NodeMetrics to dictionary."""
        metrics = NodeMetrics(
            node_id="n1",
            role="tongue",
            cost_tier="medium",
            estimated_cost=0.01,
        )

        result = metrics.to_dict()

        self.assertEqual(result["node_id"], "n1")
        self.assertEqual(result["role"], "tongue")
        self.assertEqual(result["cost_tier"], "medium")
        self.assertEqual(result["estimated_cost"], 0.01)


# =============================================================================
# GraphMetrics Tests
# =============================================================================


class TestGraphMetrics(unittest.TestCase):
    """Tests for GraphMetrics dataclass."""

    def test_graph_metrics_creation(self):
        """Test creating GraphMetrics with all fields."""
        metrics = GraphMetrics(
            graph_id="graph_001",
            track="feature",
            title="Add login feature",
            started_at="2024-01-15T10:00:00+00:00",
            completed_at="2024-01-15T10:30:00+00:00",
            total_duration_sec=1800.0,
            total_estimated_cost=0.25,
            status="completed",
        )

        self.assertEqual(metrics.graph_id, "graph_001")
        self.assertEqual(metrics.track, "feature")
        self.assertEqual(metrics.title, "Add login feature")
        self.assertEqual(metrics.total_duration_sec, 1800.0)
        self.assertEqual(metrics.total_estimated_cost, 0.25)
        self.assertEqual(metrics.status, "completed")

    def test_graph_metrics_default_values(self):
        """Test GraphMetrics with default values."""
        metrics = GraphMetrics(
            graph_id="g1",
            track="fix",
            title="Fix bug",
        )

        self.assertIsNone(metrics.started_at)
        self.assertIsNone(metrics.completed_at)
        self.assertIsNone(metrics.total_duration_sec)
        self.assertEqual(metrics.total_estimated_cost, 0.0)
        self.assertEqual(metrics.nodes, {})
        self.assertEqual(metrics.cost_by_role, {})
        self.assertEqual(metrics.cost_by_tier, {})
        self.assertEqual(metrics.status, "created")

    def test_graph_metrics_to_dict(self):
        """Test converting GraphMetrics to dictionary."""
        node_metrics = NodeMetrics("n1", "eye", "cheap", estimated_cost=0.001)
        metrics = GraphMetrics(
            graph_id="g1",
            track="feature",
            title="Test",
            total_estimated_cost=0.12345,
            nodes={"n1": node_metrics},
            cost_by_role={"eye": 0.001, "body": 0.1},
            cost_by_tier={"cheap": 0.001, "expensive": 0.1},
        )

        result = metrics.to_dict()

        self.assertEqual(result["graph_id"], "g1")
        self.assertEqual(result["total_estimated_cost"], 0.1235)  # Rounded
        self.assertIn("n1", result["nodes"])
        self.assertEqual(result["cost_by_role"]["eye"], 0.001)
        self.assertEqual(result["cost_by_tier"]["expensive"], 0.1)


# =============================================================================
# Cost Tier Tests
# =============================================================================


class TestCostTiers(unittest.TestCase):
    """Tests for cost tier definitions."""

    def test_cost_tiers_exist(self):
        """Test that all cost tiers are defined."""
        self.assertIn("cheap", COST_TIERS)
        self.assertIn("medium", COST_TIERS)
        self.assertIn("expensive", COST_TIERS)

    def test_cost_tier_values(self):
        """Test cost tier values are reasonable."""
        self.assertEqual(COST_TIERS["cheap"], 0.001)
        self.assertEqual(COST_TIERS["medium"], 0.01)
        self.assertEqual(COST_TIERS["expensive"], 0.10)

    def test_role_to_tier_mapping(self):
        """Test role to tier mapping is complete."""
        expected_mappings = {
            "eye": "cheap",
            "ear": "cheap",
            "nose": "cheap",
            "tongue": "medium",
            "body": "expensive",
            "mind": "expensive",
        }

        for role, expected_tier in expected_mappings.items():
            self.assertEqual(
                ROLE_TO_TIER[role],
                expected_tier,
                f"Role {role} should map to {expected_tier}",
            )


# =============================================================================
# MetricsCollector Tests
# =============================================================================


class TestMetricsCollector(unittest.TestCase):
    """Tests for MetricsCollector class."""

    def setUp(self):
        """Create temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.events_file = Path(self.temp_dir) / "events.jsonl"
        self.state_file = Path(self.temp_dir) / "state.json"
        self.taskgraph_file = Path(self.temp_dir) / "taskgraph.json"

        self.collector = MetricsCollector(
            events_file=self.events_file,
            state_file=self.state_file,
            taskgraph_file=self.taskgraph_file,
        )

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_events(self, events):
        """Helper to write events to the events file."""
        with open(self.events_file, "w") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")

    def _write_taskgraph(self, graph):
        """Helper to write task graph to file."""
        with open(self.taskgraph_file, "w") as f:
            json.dump(graph, f)

    def test_calculate_duration(self):
        """Test duration calculation between timestamps."""
        start = "2024-01-15T10:00:00+00:00"
        end = "2024-01-15T10:05:00+00:00"

        duration = self.collector._calculate_duration(start, end)

        self.assertEqual(duration, 300.0)  # 5 minutes = 300 seconds

    def test_calculate_duration_with_none(self):
        """Test duration calculation with None values."""
        self.assertIsNone(self.collector._calculate_duration(None, "2024-01-15T10:00:00+00:00"))
        self.assertIsNone(self.collector._calculate_duration("2024-01-15T10:00:00+00:00", None))
        self.assertIsNone(self.collector._calculate_duration(None, None))

    def test_estimate_node_cost_cheap(self):
        """Test cost estimation for cheap tier node."""
        node = {"role": "eye", "constraints": {}}

        cost = self.collector._estimate_node_cost(node)

        self.assertEqual(cost, COST_TIERS["cheap"])

    def test_estimate_node_cost_expensive(self):
        """Test cost estimation for expensive tier node."""
        node = {"role": "body", "constraints": {}}

        cost = self.collector._estimate_node_cost(node)

        self.assertEqual(cost, COST_TIERS["expensive"])

    def test_estimate_node_cost_with_retries(self):
        """Test cost estimation increases with retries."""
        node = {"role": "eye", "constraints": {}}

        cost_no_retry = self.collector._estimate_node_cost(node, retry_count=0)
        cost_one_retry = self.collector._estimate_node_cost(node, retry_count=1)
        cost_two_retries = self.collector._estimate_node_cost(node, retry_count=2)

        self.assertEqual(cost_no_retry, COST_TIERS["cheap"])
        self.assertEqual(cost_one_retry, COST_TIERS["cheap"] * 2)
        self.assertEqual(cost_two_retries, COST_TIERS["cheap"] * 3)

    def test_estimate_node_cost_with_explicit_tier(self):
        """Test cost estimation with explicit cost_tier constraint."""
        node = {
            "role": "eye",  # Would normally be cheap
            "constraints": {"cost_tier": "expensive"},  # Override to expensive
        }

        cost = self.collector._estimate_node_cost(node)

        self.assertEqual(cost, COST_TIERS["expensive"])

    def test_get_node_cost_tier_from_constraints(self):
        """Test getting cost tier from node constraints."""
        node = {
            "role": "eye",
            "constraints": {"cost_tier": "medium"},
        }

        tier = self.collector._get_node_cost_tier(node)

        self.assertEqual(tier, "medium")

    def test_get_node_cost_tier_from_role(self):
        """Test getting cost tier from role when no constraint."""
        node = {"role": "tongue", "constraints": {}}

        tier = self.collector._get_node_cost_tier(node)

        self.assertEqual(tier, "medium")

    def test_collect_graph_metrics_no_graph(self):
        """Test collect_graph_metrics returns None when no graph exists."""
        result = self.collector.collect_graph_metrics()

        self.assertIsNone(result)

    def test_collect_graph_metrics_basic(self):
        """Test collecting metrics for a basic task graph."""
        # Create a simple task graph
        graph = {
            "id": "graph_001",
            "track": "feature",
            "title": "Add login",
            "status": "running",
            "nodes": [
                {"id": "n1", "role": "eye", "status": "done"},
                {"id": "n2", "role": "body", "status": "running"},
            ],
        }
        self._write_taskgraph(graph)

        # Create events
        events = [
            {
                "type": "TaskGraphCreated",
                "timestamp": "2024-01-15T10:00:00+00:00",
                "graph_id": "graph_001",
            },
            {
                "type": "NodeScheduled",
                "timestamp": "2024-01-15T10:00:30+00:00",
                "graph_id": "graph_001",
                "node_id": "n1",
            },
            {
                "type": "NodeCompleted",
                "timestamp": "2024-01-15T10:01:00+00:00",
                "graph_id": "graph_001",
                "node_id": "n1",
            },
        ]
        self._write_events(events)

        metrics = self.collector.collect_graph_metrics()

        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.graph_id, "graph_001")
        self.assertEqual(metrics.track, "feature")
        self.assertEqual(metrics.title, "Add login")
        self.assertEqual(len(metrics.nodes), 2)
        self.assertIn("n1", metrics.nodes)
        self.assertIn("n2", metrics.nodes)

    def test_collect_graph_metrics_with_timing(self):
        """Test that node timing is extracted from events."""
        graph = {
            "id": "g1",
            "track": "fix",
            "title": "Fix bug",
            "status": "completed",
            "nodes": [
                {"id": "n1", "role": "eye", "status": "done"},
            ],
        }
        self._write_taskgraph(graph)

        events = [
            {
                "type": "NodeScheduled",
                "timestamp": "2024-01-15T10:00:00+00:00",
                "graph_id": "g1",
                "node_id": "n1",
            },
            {
                "type": "NodeCompleted",
                "timestamp": "2024-01-15T10:02:00+00:00",
                "graph_id": "g1",
                "node_id": "n1",
            },
        ]
        self._write_events(events)

        metrics = self.collector.collect_graph_metrics()

        node_metrics = metrics.nodes["n1"]
        self.assertEqual(node_metrics.started_at, "2024-01-15T10:00:00+00:00")
        self.assertEqual(node_metrics.completed_at, "2024-01-15T10:02:00+00:00")
        self.assertEqual(node_metrics.duration_sec, 120.0)

    def test_collect_graph_metrics_cost_aggregation(self):
        """Test that costs are aggregated correctly."""
        graph = {
            "id": "g1",
            "track": "feature",
            "title": "Test",
            "status": "completed",
            "nodes": [
                {"id": "n1", "role": "eye", "status": "done"},
                {"id": "n2", "role": "body", "status": "done"},
                {"id": "n3", "role": "eye", "status": "done"},
            ],
        }
        self._write_taskgraph(graph)
        self._write_events([])

        metrics = self.collector.collect_graph_metrics()

        # 2 cheap + 1 expensive
        expected_cost = 2 * COST_TIERS["cheap"] + COST_TIERS["expensive"]
        self.assertAlmostEqual(metrics.total_estimated_cost, expected_cost, places=4)

        self.assertIn("eye", metrics.cost_by_role)
        self.assertIn("body", metrics.cost_by_role)
        self.assertIn("cheap", metrics.cost_by_tier)
        self.assertIn("expensive", metrics.cost_by_tier)

    def test_get_total_cost(self):
        """Test getting total cost for a graph."""
        graph = {
            "id": "g1",
            "track": "fix",
            "title": "Test",
            "status": "done",
            "nodes": [
                {"id": "n1", "role": "body", "status": "done"},
            ],
        }
        self._write_taskgraph(graph)
        self._write_events([])

        cost = self.collector.get_total_cost()

        self.assertEqual(cost, COST_TIERS["expensive"])

    def test_get_total_cost_no_graph(self):
        """Test get_total_cost returns 0 when no graph exists."""
        cost = self.collector.get_total_cost()

        self.assertEqual(cost, 0.0)

    def test_get_cost_breakdown(self):
        """Test getting cost breakdown by role and tier."""
        graph = {
            "id": "g1",
            "track": "feature",
            "title": "Test",
            "status": "done",
            "nodes": [
                {"id": "n1", "role": "eye", "status": "done"},
                {"id": "n2", "role": "tongue", "status": "done"},
                {"id": "n3", "role": "body", "status": "done"},
            ],
        }
        self._write_taskgraph(graph)
        self._write_events([])

        breakdown = self.collector.get_cost_breakdown()

        self.assertIn("by_role", breakdown)
        self.assertIn("by_tier", breakdown)
        self.assertIn("eye", breakdown["by_role"])
        self.assertIn("tongue", breakdown["by_role"])
        self.assertIn("body", breakdown["by_role"])
        self.assertIn("cheap", breakdown["by_tier"])
        self.assertIn("medium", breakdown["by_tier"])
        self.assertIn("expensive", breakdown["by_tier"])

    def test_get_cost_breakdown_no_graph(self):
        """Test get_cost_breakdown returns empty when no graph exists."""
        breakdown = self.collector.get_cost_breakdown()

        self.assertEqual(breakdown, {"by_role": {}, "by_tier": {}})

    def test_export_report(self):
        """Test exporting metrics as JSON report."""
        graph = {
            "id": "g1",
            "track": "fix",
            "title": "Fix bug",
            "status": "completed",
            "nodes": [
                {"id": "n1", "role": "eye", "status": "done"},
            ],
        }
        self._write_taskgraph(graph)
        self._write_events([])

        report = self.collector.export_report()
        data = json.loads(report)

        self.assertEqual(data["graph_id"], "g1")
        self.assertEqual(data["track"], "fix")
        self.assertIn("nodes", data)
        self.assertIn("total_estimated_cost", data)

    def test_export_report_no_graph(self):
        """Test export_report returns error when no graph exists."""
        report = self.collector.export_report()
        data = json.loads(report)

        self.assertIn("error", data)
        self.assertEqual(data["error"], "Graph not found")


# =============================================================================
# Scheduler Tests
# =============================================================================


class TestScheduler(unittest.TestCase):
    """Tests for Scheduler class."""

    def setUp(self):
        """Create temporary directory with test templates."""
        self.temp_dir = tempfile.mkdtemp()
        self.template_dir = Path(self.temp_dir) / "templates"
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.scheduler = Scheduler(self.template_dir)

        # Create test templates
        self._create_test_templates()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_templates(self):
        """Create test template files."""
        # Fix track template
        fix_template = {
            "track": "fix",
            "title": "Fix Bug",
            "nodes": [
                {"id": "n1", "role": "eye", "title": "Investigate"},
                {"id": "n2", "role": "body", "title": "Implement fix"},
            ],
            "edges": [
                {"from": "n1", "to": "n2", "condition": "on_success"}
            ],
        }
        with open(self.template_dir / "fix_track.json", "w") as f:
            json.dump(fix_template, f)

        # Feature track template
        feature_template = {
            "track": "feature",
            "title": "Add Feature",
            "nodes": [
                {"id": "n1", "role": "ear", "title": "Gather requirements"},
                {"id": "n2", "role": "mind", "title": "Design"},
                {"id": "n3", "role": "body", "title": "Implement"},
            ],
            "edges": [
                {"from": "n1", "to": "n2", "condition": "on_success"},
                {"from": "n2", "to": "n3", "condition": "on_success"},
            ],
        }
        with open(self.template_dir / "feature_track.json", "w") as f:
            json.dump(feature_template, f)

    def test_load_template_success(self):
        """Test loading a valid template."""
        template = self.scheduler.load_template("fix")

        self.assertEqual(template["track"], "fix")
        self.assertEqual(len(template["nodes"]), 2)
        self.assertEqual(len(template["edges"]), 1)

    def test_load_template_invalid_track(self):
        """Test loading invalid track raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.scheduler.load_template("invalid_track")

        self.assertIn("Invalid track", str(ctx.exception))

    def test_load_template_file_not_found(self):
        """Test loading non-existent template raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            self.scheduler.load_template("direct")

    def test_instantiate_graph(self):
        """Test creating a graph instance from template."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Fix login bug")

        self.assertTrue(graph["id"].startswith("tg_"))
        self.assertIn("created_at", graph)
        self.assertIn("updated_at", graph)
        self.assertEqual(graph["status"], "created")
        self.assertIn("Fix login bug", graph["title"])
        self.assertEqual(graph["metadata"]["user_prompt"], "Fix login bug")

    def test_instantiate_graph_with_options(self):
        """Test instantiating graph with working_dir and tags."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(
            template,
            "Fix bug",
            working_dir="/tmp/project",
            tags=["urgent", "security"],
        )

        self.assertEqual(graph["context"]["working_dir"], "/tmp/project")
        self.assertEqual(graph["metadata"]["tags"], ["urgent", "security"])

    def test_instantiate_graph_resets_node_status(self):
        """Test that instantiate_graph resets all node statuses to pending."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        for node in graph["nodes"]:
            self.assertEqual(node["status"], "pending")
            self.assertEqual(node["outputs"], {})

    def test_get_ready_nodes_initial(self):
        """Test getting ready nodes at start (root nodes)."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        ready = self.scheduler.get_ready_nodes(graph)

        # Only n1 should be ready (no incoming edges)
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0]["id"], "n1")

    def test_get_ready_nodes_after_completion(self):
        """Test getting ready nodes after completing a node."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        # Complete n1
        self.scheduler.mark_node_status(graph, "n1", "done")

        ready = self.scheduler.get_ready_nodes(graph)

        # Now n2 should be ready
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0]["id"], "n2")

    def test_get_ready_nodes_no_pending(self):
        """Test get_ready_nodes returns empty when all nodes done."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        # Complete all nodes
        self.scheduler.mark_node_status(graph, "n1", "done")
        self.scheduler.mark_node_status(graph, "n2", "done")

        ready = self.scheduler.get_ready_nodes(graph)

        self.assertEqual(len(ready), 0)

    def test_mark_node_status_running(self):
        """Test marking a node as running."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        self.scheduler.mark_node_status(graph, "n1", "running")

        node = self.scheduler._get_node_by_id(graph, "n1")
        self.assertEqual(node["status"], "running")
        self.assertIn("n1", graph["execution"]["active_nodes"])

    def test_mark_node_status_done(self):
        """Test marking a node as done with outputs."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        self.scheduler.mark_node_status(
            graph,
            "n1",
            "done",
            outputs={"found_files": ["a.py", "b.py"]},
        )

        node = self.scheduler._get_node_by_id(graph, "n1")
        self.assertEqual(node["status"], "done")
        self.assertEqual(node["outputs"]["found_files"], ["a.py", "b.py"])
        self.assertIn("n1", graph["execution"]["completed_nodes"])
        self.assertNotIn("n1", graph["execution"]["active_nodes"])

    def test_mark_node_status_failed(self):
        """Test marking a node as failed with error info."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        self.scheduler.mark_node_status(
            graph,
            "n1",
            "failed",
            error={"message": "Timeout", "code": "ETIMEDOUT"},
        )

        node = self.scheduler._get_node_by_id(graph, "n1")
        self.assertEqual(node["status"], "failed")
        self.assertEqual(node["error"]["message"], "Timeout")
        self.assertIn("n1", graph["execution"]["failed_nodes"])

    def test_mark_node_status_invalid_status(self):
        """Test marking node with invalid status raises ValueError."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        with self.assertRaises(ValueError) as ctx:
            self.scheduler.mark_node_status(graph, "n1", "invalid_status")

        self.assertIn("Invalid status", str(ctx.exception))

    def test_mark_node_status_node_not_found(self):
        """Test marking non-existent node raises ValueError."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        with self.assertRaises(ValueError) as ctx:
            self.scheduler.mark_node_status(graph, "nonexistent", "done")

        self.assertIn("Node not found", str(ctx.exception))

    def test_get_downstream_nodes(self):
        """Test getting downstream nodes."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        downstream = self.scheduler.get_downstream_nodes(graph, "n1")

        self.assertEqual(downstream, ["n2"])

    def test_get_upstream_nodes(self):
        """Test getting upstream nodes."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        upstream = self.scheduler.get_upstream_nodes(graph, "n2")

        self.assertEqual(upstream, ["n1"])

    def test_is_graph_complete(self):
        """Test checking if graph execution is complete."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        # Initially not complete
        self.assertFalse(self.scheduler.is_graph_complete(graph))

        # Complete all nodes
        self.scheduler.mark_node_status(graph, "n1", "done")
        self.scheduler.mark_node_status(graph, "n2", "done")

        # Now complete
        self.assertTrue(self.scheduler.is_graph_complete(graph))

    def test_get_graph_status(self):
        """Test getting overall graph status."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        # Initial status
        self.assertEqual(self.scheduler.get_graph_status(graph), "created")

        # Start a node
        self.scheduler.mark_node_status(graph, "n1", "running")
        self.assertEqual(self.scheduler.get_graph_status(graph), "running")

        # Complete all nodes
        self.scheduler.mark_node_status(graph, "n1", "done")
        self.scheduler.mark_node_status(graph, "n2", "done")
        self.assertEqual(self.scheduler.get_graph_status(graph), "completed")

    def test_get_execution_summary(self):
        """Test getting execution summary."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        self.scheduler.mark_node_status(graph, "n1", "running")

        summary = self.scheduler.get_execution_summary(graph)

        self.assertEqual(summary["total_nodes"], 2)
        self.assertEqual(summary["running"]["count"], 1)
        self.assertEqual(summary["pending"]["count"], 1)
        self.assertEqual(summary["done"]["count"], 0)
        self.assertIn("n1", summary["running"]["nodes"])
        self.assertIn("n2", summary["pending"]["nodes"])

    def test_topological_sort(self):
        """Test topological sorting of nodes."""
        template = self.scheduler.load_template("feature")
        graph = self.scheduler.instantiate_graph(template, "Test")

        sorted_ids = self.scheduler.topological_sort(graph)

        # Should be: n1 -> n2 -> n3
        self.assertEqual(sorted_ids, ["n1", "n2", "n3"])

    def test_render_mermaid(self):
        """Test rendering graph as Mermaid diagram."""
        template = self.scheduler.load_template("fix")
        graph = self.scheduler.instantiate_graph(template, "Test")

        # Mark one node as done
        self.scheduler.mark_node_status(graph, "n1", "done")

        diagram = self.scheduler.render_mermaid(graph, include_status=True)

        self.assertIn("graph TD", diagram)
        self.assertIn("n1", diagram)
        self.assertIn("n2", diagram)
        self.assertIn("n1 --> n2", diagram)
        self.assertIn("classDef done", diagram)


# =============================================================================
# AnchorManager Tests
# =============================================================================


class TestAnchorManager(unittest.TestCase):
    """Tests for AnchorManager class."""

    def setUp(self):
        """Create temporary directory for anchors."""
        self.temp_dir = tempfile.mkdtemp()
        self.anchors_dir = Path(self.temp_dir) / "anchors"
        self.manager = AnchorManager(self.anchors_dir)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_directories(self):
        """Test that AnchorManager creates necessary directories."""
        self.assertTrue(self.anchors_dir.exists())
        self.assertTrue((self.anchors_dir / "anchors.json").exists())
        self.assertTrue((self.anchors_dir / "candidates.json").exists())

    def test_add_candidate_basic(self):
        """Test adding a basic candidate anchor."""
        candidate_id = self.manager.add_candidate({
            "type": "decision",
            "title": "Use PostgreSQL",
            "content": "PostgreSQL chosen for ACID compliance",
            "keywords": ["database", "postgresql"],
        })

        self.assertTrue(candidate_id.startswith("cand_"))

        # Verify it was saved
        candidate = self.manager.get_candidate(candidate_id)
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["type"], "decision")
        self.assertEqual(candidate["title"], "Use PostgreSQL")

    def test_add_candidate_with_source(self):
        """Test adding candidate with source information."""
        candidate_id = self.manager.add_candidate(
            {
                "type": "constraint",
                "title": "Max 100 concurrent users",
                "content": "System designed for max 100 concurrent users",
                "keywords": ["performance", "limits"],
            },
            source={"graph_id": "g1", "node_id": "n1"},
        )

        candidate = self.manager.get_candidate(candidate_id)
        self.assertEqual(candidate["source"]["graph_id"], "g1")
        self.assertEqual(candidate["source"]["node_id"], "n1")

    def test_add_candidate_invalid_type(self):
        """Test adding candidate with invalid type raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.manager.add_candidate({
                "type": "invalid_type",
                "title": "Test",
                "content": "Test content",
            })

        self.assertIn("Invalid anchor type", str(ctx.exception))

    def test_add_candidate_missing_title(self):
        """Test adding candidate without title raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.manager.add_candidate({
                "type": "decision",
                "content": "Test content",
            })

        self.assertIn("must have a non-empty 'title' field", str(ctx.exception))

    def test_promote_anchor(self):
        """Test promoting a candidate to an anchor."""
        candidate_id = self.manager.add_candidate({
            "type": "decision",
            "title": "Use Redis",
            "content": "Redis chosen for caching",
            "keywords": ["cache", "redis"],
        })

        anchor_id = self.manager.promote_anchor(candidate_id)

        self.assertTrue(anchor_id.startswith("anc_"))

        # Verify anchor exists
        anchor = self.manager.get_anchor(anchor_id)
        self.assertIsNotNone(anchor)
        self.assertEqual(anchor["title"], "Use Redis")

        # Verify candidate is removed
        candidate = self.manager.get_candidate(candidate_id)
        self.assertIsNone(candidate)

    def test_promote_anchor_to_project(self):
        """Test promoting anchor to a project-specific location."""
        candidate_id = self.manager.add_candidate({
            "type": "interface",
            "title": "API Contract",
            "content": "REST API definition",
            "keywords": ["api", "rest"],
        })

        anchor_id = self.manager.promote_anchor(candidate_id, project="myproject")

        # Verify project directory was created
        project_dir = self.anchors_dir / "myproject"
        self.assertTrue(project_dir.exists())

        # Verify anchor is in project file
        anchor = self.manager.get_anchor(anchor_id)
        self.assertIsNotNone(anchor)

    def test_promote_anchor_candidate_not_found(self):
        """Test promoting non-existent candidate raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.manager.promote_anchor("nonexistent_id")

        self.assertIn("Candidate not found", str(ctx.exception))

    def test_search_anchors_by_keywords(self):
        """Test searching anchors by keywords."""
        # Add and promote some anchors
        cand1 = self.manager.add_candidate({
            "type": "decision",
            "title": "Use PostgreSQL",
            "content": "PostgreSQL for database",
            "keywords": ["database", "postgresql", "sql"],
        })
        self.manager.promote_anchor(cand1)

        cand2 = self.manager.add_candidate({
            "type": "decision",
            "title": "Use MongoDB",
            "content": "MongoDB for documents",
            "keywords": ["database", "mongodb", "nosql"],
        })
        self.manager.promote_anchor(cand2)

        # Search for database-related anchors
        results = self.manager.search_anchors(["database"])

        self.assertEqual(len(results), 2)

        # Search for specific technology
        results = self.manager.search_anchors(["postgresql"])
        self.assertEqual(len(results), 1)
        self.assertIn("PostgreSQL", results[0]["title"])

    def test_search_anchors_by_type(self):
        """Test filtering search by anchor type."""
        cand1 = self.manager.add_candidate({
            "type": "decision",
            "title": "Decision 1",
            "content": "Content",
            "keywords": ["test"],
        })
        self.manager.promote_anchor(cand1)

        cand2 = self.manager.add_candidate({
            "type": "constraint",
            "title": "Constraint 1",
            "content": "Content",
            "keywords": ["test"],
        })
        self.manager.promote_anchor(cand2)

        # Search for decisions only
        results = self.manager.search_anchors(["test"], anchor_type="decision")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "decision")

    def test_get_relevant_anchors(self):
        """Test getting anchors relevant to a task description."""
        # Add anchors
        cand1 = self.manager.add_candidate({
            "type": "decision",
            "title": "Authentication Strategy",
            "content": "Use JWT for authentication",
            "keywords": ["auth", "jwt", "security"],
        })
        self.manager.promote_anchor(cand1)

        # Get relevant anchors for authentication task
        results = self.manager.get_relevant_anchors(
            "Implement user authentication using JWT tokens"
        )

        self.assertGreater(len(results), 0)
        self.assertIn("Authentication", results[0]["title"])

    def test_list_candidates(self):
        """Test listing all pending candidates."""
        cand1 = self.manager.add_candidate({
            "type": "decision",
            "title": "Test 1",
            "content": "Content 1",
        })
        cand2 = self.manager.add_candidate({
            "type": "lesson",
            "title": "Test 2",
            "content": "Content 2",
        })

        candidates = self.manager.list_candidates()

        self.assertEqual(len(candidates), 2)

    def test_delete_candidate(self):
        """Test deleting a candidate."""
        cand_id = self.manager.add_candidate({
            "type": "decision",
            "title": "Test",
            "content": "Content",
        })

        result = self.manager.delete_candidate(cand_id)
        self.assertTrue(result)

        # Verify it's gone
        candidate = self.manager.get_candidate(cand_id)
        self.assertIsNone(candidate)

    def test_delete_candidate_not_found(self):
        """Test deleting non-existent candidate returns False."""
        result = self.manager.delete_candidate("nonexistent")
        self.assertFalse(result)

    def test_delete_anchor(self):
        """Test deleting an anchor."""
        cand_id = self.manager.add_candidate({
            "type": "decision",
            "title": "Test",
            "content": "Content",
        })
        anc_id = self.manager.promote_anchor(cand_id)

        result = self.manager.delete_anchor(anc_id)
        self.assertTrue(result)

        # Verify it's gone
        anchor = self.manager.get_anchor(anc_id)
        self.assertIsNone(anchor)

    def test_get_statistics(self):
        """Test getting anchor statistics."""
        # Add some anchors
        cand1 = self.manager.add_candidate({
            "type": "decision",
            "title": "Test 1",
            "content": "Content",
            "evidence_level": "L2",
        })
        anc1 = self.manager.promote_anchor(cand1)

        cand2 = self.manager.add_candidate({
            "type": "constraint",
            "title": "Test 2",
            "content": "Content",
            "evidence_level": "L3",
        })
        anc2 = self.manager.promote_anchor(cand2)

        # Add a pending candidate
        cand3 = self.manager.add_candidate({
            "type": "lesson",
            "title": "Test 3",
            "content": "Content",
        })

        stats = self.manager.get_statistics()

        self.assertEqual(stats["total_anchors"], 2)
        self.assertEqual(stats["total_candidates"], 1)
        self.assertGreater(stats["by_type"]["decision"], 0)
        self.assertGreater(stats["by_type"]["constraint"], 0)

    def test_export_anchors_md(self):
        """Test exporting anchors to Markdown format."""
        cand_id = self.manager.add_candidate({
            "type": "decision",
            "title": "Use TypeScript",
            "content": "TypeScript chosen for type safety",
            "keywords": ["typescript", "safety"],
            "evidence_level": "L2",
        })
        self.manager.promote_anchor(cand_id)

        md = self.manager.export_anchors_md()

        self.assertIn("# Anchors", md)
        self.assertIn("Use TypeScript", md)
        self.assertIn("L2", md)
        self.assertIn("Architecture Decisions", md)


# =============================================================================
# Integration Tests
# =============================================================================


class TestRuntimeIntegration(unittest.TestCase):
    """Integration tests for runtime modules working together."""

    def setUp(self):
        """Create temporary directory with all runtime files."""
        self.temp_dir = tempfile.mkdtemp()
        self.events_file = Path(self.temp_dir) / "events.jsonl"
        self.state_file = Path(self.temp_dir) / "state.json"
        self.taskgraph_file = Path(self.temp_dir) / "taskgraph.json"

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_task_lifecycle(self):
        """Test complete task lifecycle through all runtime components."""
        # Initialize components
        event_bus = EventBus(self.events_file, session_id="test_session")
        state_manager = StateManager(self.state_file)

        # 1. User submits prompt
        event_bus.write_event(
            "UserPromptSubmit",
            {"prompt": "Add user authentication"},
            source="user",
        )

        # 2. Task graph is created
        graph_id = "graph_auth_001"
        event_bus.write_event(
            "TaskGraphCreated",
            {"track": "feature"},
            graph_id=graph_id,
            source="scheduler",
        )

        # 3. Start graph in state manager
        state_manager.start_graph(graph_id, event_bus.session_id)
        state = state_manager.get_state()
        self.assertEqual(state["status"], "running")
        self.assertEqual(state["current_graph_id"], graph_id)

        # 4. Schedule and run node
        node_id = "node_eye_001"
        event_bus.write_event(
            "NodeScheduled",
            {"role": "eye"},
            node_id=node_id,
            graph_id=graph_id,
            source="scheduler",
        )
        state_manager.activate_node(node_id)

        state = state_manager.get_state()
        self.assertIn(node_id, state["active_nodes"])

        # 5. Complete node
        event_bus.write_event(
            "NodeCompleted",
            {"output": "Found relevant files"},
            node_id=node_id,
            graph_id=graph_id,
            source="subagent",
        )
        state_manager.complete_node(node_id)

        state = state_manager.get_state()
        self.assertNotIn(node_id, state["active_nodes"])
        self.assertIn(node_id, state["completed_nodes"])

        # 6. Complete graph
        event_bus.write_event(
            "Stop",
            {"reason": "completed"},
            graph_id=graph_id,
            source="system",
        )
        state_manager.complete_graph()

        state = state_manager.get_state()
        self.assertEqual(state["status"], "completed")

        # 7. Verify events were recorded
        events = event_bus.read_events()
        self.assertEqual(len(events), 5)

        # Verify event types
        event_types = [e.type for e in events]
        self.assertEqual(event_types[0], "UserPromptSubmit")
        self.assertEqual(event_types[1], "TaskGraphCreated")
        self.assertEqual(event_types[-1], "Stop")

    def test_failure_and_retry(self):
        """Test node failure and retry workflow."""
        event_bus = EventBus(self.events_file, session_id="test_session")
        state_manager = StateManager(self.state_file)

        # Start graph and node
        state_manager.start_graph("g1", "sess_1")
        state_manager.activate_node("n1")

        # Node fails
        event_bus.write_event(
            "NodeFailed",
            {"error": "Connection timeout"},
            node_id="n1",
            graph_id="g1",
            source="subagent",
        )
        state_manager.fail_node("n1")

        state = state_manager.get_state()
        self.assertIn("n1", state["failed_nodes"])
        self.assertEqual(state_manager.get_retry_count("n1"), 0)

        # Retry the node
        state_manager.record_retry("n1")
        self.assertEqual(state_manager.get_retry_count("n1"), 1)

        state = state_manager.get_state()
        self.assertNotIn("n1", state["failed_nodes"])

        # Activate again for retry
        state_manager.activate_node("n1")

        state = state_manager.get_state()
        self.assertIn("n1", state["active_nodes"])

    def test_pause_and_resume(self):
        """Test pausing and resuming execution."""
        state_manager = StateManager(self.state_file)

        # Start and activate nodes
        state_manager.start_graph("g1", "sess_1")
        state_manager.activate_node("n1")
        state_manager.activate_node("n2")

        # Pause
        state_manager.pause_graph()
        state = state_manager.get_state()
        self.assertEqual(state["status"], "paused")

        # Resume
        result = state_manager.prepare_for_resume()

        self.assertTrue(result["success"])
        self.assertEqual(set(result["resumed_nodes"]), {"n1", "n2"})

        state = state_manager.get_state()
        self.assertEqual(state["status"], "running")
        self.assertEqual(state["active_nodes"], [])  # Cleared for re-scheduling


if __name__ == "__main__":
    unittest.main(verbosity=2)
