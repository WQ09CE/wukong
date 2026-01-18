"""
Wukong Smart Router - Layer 1 LLM Classifier

Lightweight LLM-based task classification using Haiku.
"""

import json
import os
from pathlib import Path
from typing import Optional

from .models import Track, Complexity, L1Result


# Default classify prompt
DEFAULT_CLASSIFY_PROMPT = """You are a task classifier for a code agent system.

Classify the following task:
<task>{task}</task>

Respond with JSON only (no markdown, no explanation):
{{"track": "feature|fix|refactor|research|direct", "complexity": "simple|medium|complex", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}

Track definitions:
- feature: Adding new functionality, implementing new features
- fix: Fixing bugs, errors, crashes, issues
- refactor: Code cleanup, restructuring, optimization without new features
- research: Exploration, investigation, understanding code, learning
- direct: Simple direct actions, single command, trivial changes

Complexity definitions:
- simple: Single file, <50 lines change, straightforward
- medium: 2-3 files, moderate changes, clear approach
- complex: Multiple files, architectural changes, needs planning, uncertain approach"""


class LLMClassifier:
    """
    Layer 1: Haiku LLM classifier.

    Uses Claude Haiku for fast, lightweight classification.
    Timeout: 5 seconds
    Fallback: Returns None on error (router handles fallback)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 5.0,
        prompts_dir: Optional[Path] = None,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.timeout = timeout
        self.model = "claude-3-haiku-20240307"
        self.prompts_dir = prompts_dir

        # Load custom prompt if available
        self.classify_prompt = self._load_prompt("classify.txt") or DEFAULT_CLASSIFY_PROMPT

    def _load_prompt(self, filename: str) -> Optional[str]:
        """Load prompt from file if available."""
        if not self.prompts_dir:
            return None
        prompt_file = self.prompts_dir / filename
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return None

    async def classify(self, task: str) -> Optional[L1Result]:
        """
        Classify task using LLM.

        Returns L1Result or None on error.
        """
        if not self.api_key:
            return None

        try:
            # Try to import anthropic
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            # Build prompt
            prompt = self.classify_prompt.format(task=task)

            # Call API (sync for simplicity, can be made async later)
            response = client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            return self._parse_response(response.content[0].text)

        except ImportError:
            # anthropic not installed
            return None
        except Exception:
            # Any other error (timeout, API error, etc.)
            return None

    def classify_sync(self, task: str) -> Optional[L1Result]:
        """Synchronous version of classify."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.classify(task))

    def _parse_response(self, response: str) -> Optional[L1Result]:
        """Parse LLM response into L1Result."""
        try:
            # Clean response (remove markdown if present)
            response = response.strip()
            if response.startswith("```"):
                # Remove markdown code fence
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            data = json.loads(response)

            # Validate and extract fields
            track_str = data.get("track", "direct").lower()
            complexity_str = data.get("complexity", "medium").lower()
            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning")

            # Validate track
            try:
                track = Track(track_str)
            except ValueError:
                track = Track.DIRECT

            # Validate complexity
            try:
                complexity = Complexity(complexity_str)
            except ValueError:
                complexity = Complexity.MEDIUM

            # Clamp confidence
            confidence = max(0.0, min(1.0, confidence))

            return L1Result(
                track=track,
                complexity=complexity,
                confidence=round(confidence, 2),
                reasoning=reasoning,
            )

        except (json.JSONDecodeError, KeyError, TypeError):
            return None
