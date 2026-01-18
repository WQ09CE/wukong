"""
Wukong Smart Router - Layer 2 LLM Planner

LLM-based task decomposition for complex tasks.
"""

import json
import os
from pathlib import Path
from typing import Optional, List

from .models import Track, L1Result, L2Result, Subtask, Phase


# Default planning prompt
DEFAULT_PLAN_PROMPT = """You are a task planner for the Wukong multi-agent code system.

Task: {task}
Track: {track}
Complexity: {complexity}

Available agents:
- eye (眼): Explorer - code exploration, file search, understanding structure
- ear (耳): Analyst - requirements analysis, understanding user intent
- nose (鼻): Reviewer - code review, security audit, quality check
- tongue (舌): Tester - writing tests, documentation, verification
- body (身): Implementer - writing code, making changes, fixing bugs
- mind (意): Architect - design decisions, architecture planning

Reference DAG template for {track} track:
{template_phases}

Plan the subtasks. Respond with JSON only (no markdown):
{{
  "subtasks": [
    {{"id": "subtask_1", "title": "Brief title", "agent": "eye|ear|nose|tongue|body|mind", "dependencies": []}}
  ],
  "phases": [
    {{"phase": 0, "nodes": ["subtask_1", "subtask_2"], "parallel": true}}
  ],
  "dag_override": false
}}

Rules:
1. Keep subtasks focused and actionable
2. Maximum 6 subtasks
3. Use parallel=true when tasks are independent
4. dag_override=true only if template phases are inadequate
5. Dependencies reference subtask IDs"""


class LLMPlanner:
    """
    Layer 2: Haiku LLM planner for complex tasks.

    Only triggered when L1 returns complexity="complex".
    Timeout: 8 seconds
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        templates_dir: Optional[Path] = None,
        timeout: float = 8.0,
        prompts_dir: Optional[Path] = None,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.templates_dir = templates_dir
        self.timeout = timeout
        self.model = "claude-3-haiku-20240307"
        self.prompts_dir = prompts_dir

        # Load custom prompt if available
        self.plan_prompt = self._load_prompt("plan.txt") or DEFAULT_PLAN_PROMPT

    def _load_prompt(self, filename: str) -> Optional[str]:
        """Load prompt from file if available."""
        if not self.prompts_dir:
            return None
        prompt_file = self.prompts_dir / filename
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8")
        return None

    def _load_template_phases(self, track: Track) -> str:
        """Load template phases for reference."""
        # Default phases if no template found
        default_phases = {
            Track.FEATURE: [
                {"phase": 0, "nodes": ["ear_understand", "eye_explore"], "parallel": True},
                {"phase": 1, "nodes": ["mind_design"], "parallel": False},
                {"phase": 2, "nodes": ["body_implement"], "parallel": False},
                {"phase": 3, "nodes": ["tongue_verify", "nose_review"], "parallel": True},
            ],
            Track.FIX: [
                {"phase": 0, "nodes": ["eye_explore", "nose_analyze"], "parallel": True},
                {"phase": 1, "nodes": ["body_implement"], "parallel": False},
                {"phase": 2, "nodes": ["tongue_verify"], "parallel": False},
            ],
            Track.REFACTOR: [
                {"phase": 0, "nodes": ["eye_explore"], "parallel": False},
                {"phase": 1, "nodes": ["mind_design"], "parallel": False},
                {"phase": 2, "nodes": ["body_implement"], "parallel": False},
                {"phase": 3, "nodes": ["nose_review", "tongue_verify"], "parallel": True},
            ],
            Track.RESEARCH: [
                {"phase": 0, "nodes": ["eye_explore"], "parallel": False},
            ],
            Track.DIRECT: [
                {"phase": 0, "nodes": [], "parallel": False},
            ],
        }

        phases = default_phases.get(track, default_phases[Track.DIRECT])
        return json.dumps(phases, indent=2)

    async def plan(self, task: str, l1_result: L1Result) -> Optional[L2Result]:
        """
        Plan subtasks for complex task.

        Returns L2Result or None on error.
        """
        if not self.api_key:
            return None

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            # Build prompt
            template_phases = self._load_template_phases(l1_result.track)
            prompt = self.plan_prompt.format(
                task=task,
                track=l1_result.track.value,
                complexity=l1_result.complexity.value,
                template_phases=template_phases,
            )

            # Call API
            response = client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            return self._parse_response(response.content[0].text)

        except ImportError:
            return None
        except Exception:
            return None

    def plan_sync(self, task: str, l1_result: L1Result) -> Optional[L2Result]:
        """Synchronous version of plan."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.plan(task, l1_result))

    def _parse_response(self, response: str) -> Optional[L2Result]:
        """Parse LLM response into L2Result."""
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])

            data = json.loads(response)

            # Parse subtasks
            subtasks: List[Subtask] = []
            for st_data in data.get("subtasks", []):
                subtask = Subtask(
                    id=st_data.get("id", f"subtask_{len(subtasks)}"),
                    title=st_data.get("title", "Untitled"),
                    agent=st_data.get("agent", "body"),
                    inputs=st_data.get("inputs", []),
                    dependencies=st_data.get("dependencies", []),
                )
                subtasks.append(subtask)

            # Parse phases
            phases: List[Phase] = []
            for p_data in data.get("phases", []):
                phase = Phase(
                    phase=p_data.get("phase", len(phases)),
                    nodes=p_data.get("nodes", []),
                    parallel=p_data.get("parallel", False),
                )
                phases.append(phase)

            # If no phases, create default based on subtasks
            if not phases and subtasks:
                phases = [Phase(phase=0, nodes=[st.id for st in subtasks], parallel=False)]

            dag_override = data.get("dag_override", False)

            return L2Result(
                subtasks=subtasks,
                phases=phases,
                dag_override=dag_override,
            )

        except (json.JSONDecodeError, KeyError, TypeError):
            return None
