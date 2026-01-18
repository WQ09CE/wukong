"""
Wukong Smart Router - Data Models

Dataclasses for routing results across all layers.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class Track(str, Enum):
    """Task track types."""
    FEATURE = "feature"
    FIX = "fix"
    REFACTOR = "refactor"
    RESEARCH = "research"
    DIRECT = "direct"


class Complexity(str, Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


# Agent name mappings for @ syntax
AGENT_ALIASES = {
    # Chinese
    "眼": "eye",
    "耳": "ear",
    "鼻": "nose",
    "舌": "tongue",
    "身": "body",
    "意": "mind",
    "斗战胜佛": "body",
    # English
    "explorer": "eye",
    "analyst": "ear",
    "reviewer": "nose",
    "tester": "tongue",
    "impl": "body",
    "implementer": "body",
    "architect": "mind",
}

# Agent to track mapping (for @ syntax routing)
AGENT_TO_TRACK = {
    "eye": Track.RESEARCH,
    "ear": Track.FEATURE,
    "nose": Track.FIX,
    "tongue": Track.FEATURE,
    "body": Track.FEATURE,
    "mind": Track.FEATURE,
}


@dataclass
class L0Result:
    """Layer 0 rule matching result."""
    track: Track
    confidence: float  # 0.0-1.0
    matched_by: str  # "at_syntax" | "command" | "keyword" | "default"
    keywords_matched: List[str] = field(default_factory=list)
    agent_specified: Optional[str] = None  # If @ syntax was used

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track": self.track.value,
            "confidence": self.confidence,
            "matched_by": self.matched_by,
            "keywords_matched": self.keywords_matched,
            "agent_specified": self.agent_specified,
        }


@dataclass
class L1Result:
    """Layer 1 LLM classification result."""
    track: Track
    complexity: Complexity
    confidence: float
    reasoning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track": self.track.value,
            "complexity": self.complexity.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


@dataclass
class Subtask:
    """L2 planning subtask."""
    id: str
    title: str
    agent: str  # "eye" | "ear" | "nose" | "tongue" | "body" | "mind"
    inputs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class Phase:
    """Execution phase."""
    phase: int
    nodes: List[str]  # Using 'nodes' for compatibility with existing format
    parallel: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "nodes": self.nodes,
            "parallel": self.parallel,
        }


@dataclass
class L2Result:
    """Layer 2 LLM planning result."""
    subtasks: List[Subtask]
    phases: List[Phase]
    dag_override: bool = False  # Whether to override template DAG

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subtasks": [
                {
                    "id": st.id,
                    "title": st.title,
                    "agent": st.agent,
                    "inputs": st.inputs,
                    "dependencies": st.dependencies,
                }
                for st in self.subtasks
            ],
            "phases": [p.to_dict() for p in self.phases],
            "dag_override": self.dag_override,
        }


@dataclass
class RoutingResult:
    """Final routing result."""
    track: Track
    complexity: Complexity
    confidence: float
    phases: List[Phase]

    # Routing path
    routed_by: str  # "L0" | "L1" | "L2"
    keywords_matched: List[str] = field(default_factory=list)

    # Optional detailed results
    l0_result: Optional[L0Result] = None
    l1_result: Optional[L1Result] = None
    l2_result: Optional[L2Result] = None

    # Fallback info
    fallback_used: bool = False
    fallback_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON output (CLI compatible format)."""
        result = {
            "track": self.track.value,
            "complexity": self.complexity.value,
            "confidence": round(self.confidence, 2),
            "phases": [p.to_dict() for p in self.phases],
            "routed_by": self.routed_by,
            "keywords_matched": self.keywords_matched,
        }

        if self.fallback_used:
            result["fallback_used"] = True
            result["fallback_reason"] = self.fallback_reason

        return result
