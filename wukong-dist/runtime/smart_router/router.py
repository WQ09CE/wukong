"""
Wukong Smart Router - Main Router

Coordinates three-layer routing: L0 (rules) -> L1 (LLM classify) -> L2 (LLM plan)
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from .models import (
    Track,
    Complexity,
    Phase,
    RoutingResult,
    L0Result,
    L1Result,
)
from .rule_matcher import RuleMatcher, DEFAULT_TRACK_KEYWORDS
from .llm_classifier import LLMClassifier
from .llm_planner import LLMPlanner


# Default phases for each track (fallback when templates not available)
DEFAULT_TRACK_PHASES: Dict[str, List[Dict[str, Any]]] = {
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


class SmartRouter:
    """
    Smart Router - Three-layer conditional routing.

    Flow:
    1. L0 Rule Matcher (0ms) - Always runs
    2. L1 LLM Classifier (~300ms) - Only if L0 confidence < threshold
    3. L2 LLM Planner (~500ms) - Only if complexity == "complex"

    Fallback: Always fall back to L0 result on any LLM error.
    """

    def __init__(
        self,
        templates_dir: Optional[Path] = None,
        api_key: Optional[str] = None,
        l0_threshold: float = 0.7,
        enable_llm: bool = True,
    ):
        """
        Initialize Smart Router.

        Args:
            templates_dir: Path to DAG templates
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env)
            l0_threshold: Confidence threshold for L1 escalation (default: 0.7)
            enable_llm: Whether to enable LLM layers (default: True)
        """
        self.templates_dir = templates_dir
        self.l0_threshold = l0_threshold
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.enable_llm = enable_llm and bool(self.api_key)

        # Initialize components
        self.rule_matcher = RuleMatcher(DEFAULT_TRACK_KEYWORDS)

        if self.enable_llm:
            prompts_dir = None
            if templates_dir:
                prompts_dir = templates_dir.parent / "smart_router" / "prompts"
            self.classifier = LLMClassifier(
                api_key=self.api_key,
                prompts_dir=prompts_dir,
            )
            self.planner = LLMPlanner(
                api_key=self.api_key,
                templates_dir=templates_dir,
                prompts_dir=prompts_dir,
            )
        else:
            self.classifier = None
            self.planner = None

    async def route(self, task: str) -> RoutingResult:
        """
        Route task through layers.

        Returns RoutingResult with track, complexity, phases, and routing info.
        """
        # L0: Rule matching (always)
        l0_result = self.rule_matcher.match(task)

        # Fast path: High confidence or LLM disabled
        if l0_result.confidence >= self.l0_threshold or not self.enable_llm:
            return self._build_l0_result(l0_result)

        # L1: LLM Classification
        try:
            l1_result = await self.classifier.classify(task)

            if l1_result is None:
                # LLM failed, fallback to L0
                return self._build_fallback_result(l0_result, "L1 classification failed")

            # Check if complex task needs L2
            if l1_result.complexity != Complexity.COMPLEX:
                return self._build_l1_result(l0_result, l1_result)

            # L2: LLM Planning (only for complex tasks)
            l2_result = await self.planner.plan(task, l1_result)

            if l2_result is None:
                # L2 failed, use L1 result with template phases
                return self._build_l1_result(l0_result, l1_result)

            return self._build_l2_result(l0_result, l1_result, l2_result)

        except Exception as e:
            # Any error, fallback to L0
            return self._build_fallback_result(l0_result, str(e))

    def route_sync(self, task: str) -> RoutingResult:
        """Synchronous version of route."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.route(task))

    def _get_template_phases(self, track: Track) -> List[Phase]:
        """Get phases from template or defaults."""
        phases_data = DEFAULT_TRACK_PHASES.get(track.value, DEFAULT_TRACK_PHASES["direct"])
        return [
            Phase(
                phase=p["phase"],
                nodes=p["nodes"],
                parallel=p["parallel"],
            )
            for p in phases_data
        ]

    def _build_l0_result(self, l0_result: L0Result) -> RoutingResult:
        """Build result from L0 only."""
        # Infer complexity from track
        complexity = Complexity.SIMPLE
        if l0_result.track in (Track.FEATURE, Track.REFACTOR):
            complexity = Complexity.MEDIUM

        return RoutingResult(
            track=l0_result.track,
            complexity=complexity,
            confidence=l0_result.confidence,
            phases=self._get_template_phases(l0_result.track),
            routed_by="L0",
            keywords_matched=l0_result.keywords_matched,
            l0_result=l0_result,
        )

    def _build_l1_result(self, l0_result: L0Result, l1_result: L1Result) -> RoutingResult:
        """Build result from L1 classification."""
        return RoutingResult(
            track=l1_result.track,
            complexity=l1_result.complexity,
            confidence=l1_result.confidence,
            phases=self._get_template_phases(l1_result.track),
            routed_by="L1",
            keywords_matched=l0_result.keywords_matched,
            l0_result=l0_result,
            l1_result=l1_result,
        )

    def _build_l2_result(
        self,
        l0_result: L0Result,
        l1_result: L1Result,
        l2_result,  # L2Result
    ) -> RoutingResult:
        """Build result from L2 planning."""
        # Use L2 phases if dag_override, otherwise use template
        if l2_result.dag_override:
            phases = l2_result.phases
        else:
            phases = self._get_template_phases(l1_result.track)

        return RoutingResult(
            track=l1_result.track,
            complexity=l1_result.complexity,
            confidence=l1_result.confidence,
            phases=phases,
            routed_by="L2",
            keywords_matched=l0_result.keywords_matched,
            l0_result=l0_result,
            l1_result=l1_result,
            l2_result=l2_result,
        )

    def _build_fallback_result(self, l0_result: L0Result, reason: str) -> RoutingResult:
        """Build fallback result using L0."""
        complexity = Complexity.SIMPLE
        if l0_result.track in (Track.FEATURE, Track.REFACTOR):
            complexity = Complexity.MEDIUM

        return RoutingResult(
            track=l0_result.track,
            complexity=complexity,
            confidence=l0_result.confidence,
            phases=self._get_template_phases(l0_result.track),
            routed_by="L0",
            keywords_matched=l0_result.keywords_matched,
            l0_result=l0_result,
            fallback_used=True,
            fallback_reason=reason,
        )
