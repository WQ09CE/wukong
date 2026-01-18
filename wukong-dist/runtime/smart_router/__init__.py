"""
Wukong Smart Router

Three-layer intelligent task routing:
- L0: Rule-based matching (0ms)
- L1: LLM classification (~300ms, Haiku)
- L2: LLM planning (~500ms, Haiku, complex tasks only)
"""

from .models import (
    Track,
    Complexity,
    L0Result,
    L1Result,
    L2Result,
    Phase,
    Subtask,
    RoutingResult,
    AGENT_ALIASES,
    AGENT_TO_TRACK,
)
from .rule_matcher import RuleMatcher, DEFAULT_TRACK_KEYWORDS
from .llm_classifier import LLMClassifier
from .llm_planner import LLMPlanner
from .router import SmartRouter, DEFAULT_TRACK_PHASES

__all__ = [
    # Models
    "Track",
    "Complexity",
    "L0Result",
    "L1Result",
    "L2Result",
    "Phase",
    "Subtask",
    "RoutingResult",
    "AGENT_ALIASES",
    "AGENT_TO_TRACK",
    # Components
    "RuleMatcher",
    "LLMClassifier",
    "LLMPlanner",
    "SmartRouter",
    # Constants
    "DEFAULT_TRACK_KEYWORDS",
    "DEFAULT_TRACK_PHASES",
]
