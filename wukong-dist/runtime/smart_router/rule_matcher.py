"""
Wukong Smart Router - Layer 0 Rule Matcher

Zero-latency rule-based matching for common patterns.
"""

import re
from typing import Dict, List, Optional, Tuple

from .models import (
    Track,
    L0Result,
    AGENT_ALIASES,
    AGENT_TO_TRACK,
)


# Default track keywords (same as cli.py)
DEFAULT_TRACK_KEYWORDS = {
    "fix": ["修复", "修正", "解决", "bug", "fix", "error", "crash", "issue", "问题"],
    "feature": ["添加", "创建", "新增", "实现", "开发", "add", "create", "new", "implement", "feature", "功能"],
    "refactor": ["重构", "优化", "清理", "整理", "refactor", "clean", "optimize", "modernize"],
    "research": ["研究", "调研", "了解", "学习", "探索", "看看", "查一下", "research", "explore", "investigate"],
}


class RuleMatcher:
    """
    Layer 0: Zero-latency rule matcher.

    Priority:
    1. @ syntax (e.g., "@眼 探索代码") -> confidence=1.0
    2. /command (e.g., "/schedule fix") -> confidence=1.0
    3. Keyword matching -> confidence based on match count
    4. Default to direct -> confidence=0.3
    """

    def __init__(self, keywords: Optional[Dict[str, List[str]]] = None):
        self.keywords = keywords or DEFAULT_TRACK_KEYWORDS

    def match(self, task: str) -> L0Result:
        """
        Match task to track using rules.

        Returns L0Result with track, confidence, and match info.
        """
        # Try each matcher in priority order

        # 1. @ syntax
        result = self._parse_at_syntax(task)
        if result:
            return result

        # 2. /command (track directive)
        result = self._parse_track_directive(task)
        if result:
            return result

        # 3. Keyword matching
        return self._match_keywords(task)

    def _parse_at_syntax(self, task: str) -> Optional[L0Result]:
        """
        Parse @ syntax for explicit agent specification.

        Examples:
        - "@眼 探索认证模块" -> eye agent, research track
        - "@身 实现登录接口" -> body agent, feature track
        """
        # Pattern: @<agent> at the start or after whitespace
        pattern = r'@([\u4e00-\u9fff\w]+)'
        match = re.search(pattern, task)

        if not match:
            return None

        agent_key = match.group(1).lower()

        # Normalize agent name
        agent = AGENT_ALIASES.get(agent_key)
        if not agent:
            return None

        # Map agent to track
        track = AGENT_TO_TRACK.get(agent, Track.DIRECT)

        return L0Result(
            track=track,
            confidence=1.0,
            matched_by="at_syntax",
            keywords_matched=[f"@{match.group(1)}"],
            agent_specified=agent,
        )

    def _parse_track_directive(self, task: str) -> Optional[L0Result]:
        """
        Parse explicit track directive.

        Examples:
        - "/schedule fix" -> fix track
        - "track:feature" -> feature track
        """
        # Pattern 1: /schedule <track>
        pattern1 = r'/schedule\s+(fix|feature|refactor|research|direct)'
        match = re.search(pattern1, task.lower())
        if match:
            track_str = match.group(1)
            return L0Result(
                track=Track(track_str),
                confidence=1.0,
                matched_by="command",
                keywords_matched=[f"/schedule {track_str}"],
            )

        # Pattern 2: track:<track>
        pattern2 = r'track:\s*(fix|feature|refactor|research|direct)'
        match = re.search(pattern2, task.lower())
        if match:
            track_str = match.group(1)
            return L0Result(
                track=Track(track_str),
                confidence=1.0,
                matched_by="command",
                keywords_matched=[f"track:{track_str}"],
            )

        return None

    def _match_keywords(self, task: str) -> L0Result:
        """
        Match task to track using keywords.

        Confidence is based on:
        - Number of matched keywords / total keywords for that track
        - Minimum 0.5 if any keyword matches
        - Default 0.3 for no matches
        """
        task_lower = task.lower()

        best_track = Track.DIRECT
        best_confidence = 0.0
        matched_keywords: List[str] = []

        for track_str, keywords in self.keywords.items():
            matches = [kw for kw in keywords if kw in task_lower]
            if matches:
                # Calculate confidence based on match ratio
                confidence = len(matches) / len(keywords)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_track = Track(track_str)
                    matched_keywords = matches

        # Adjust confidence thresholds
        if matched_keywords:
            # At least 0.5 if any keyword matched
            if best_confidence < 0.5:
                best_confidence = 0.5
        else:
            # Default to direct with low confidence
            best_confidence = 0.3

        return L0Result(
            track=best_track,
            confidence=round(best_confidence, 2),
            matched_by="keyword" if matched_keywords else "default",
            keywords_matched=matched_keywords,
        )

    def get_confidence_threshold(self) -> float:
        """Get the recommended threshold for L1 escalation."""
        return 0.7
