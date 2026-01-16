"""
Wukong 2.0 Runtime MVP

This module provides the core runtime components for the Wukong multi-agent system:
- EventBus: Event-driven communication via events.jsonl
- StateManager: Atomic state management via state.json
- Scheduler: DAG-based task graph scheduling
- ArtifactManager: Output artifact archival

Usage:
    from wukong_runtime import EventBus, StateManager, Scheduler, ArtifactManager
"""

from .event_bus import EventBus
from .state_manager import StateManager
from .scheduler import Scheduler
from .artifact_manager import ArtifactManager

__version__ = "2.0.0-mvp"
__all__ = ["EventBus", "StateManager", "Scheduler", "ArtifactManager"]
