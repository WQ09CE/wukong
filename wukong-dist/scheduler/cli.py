#!/usr/bin/env python3
"""
Wukong Scheduler CLI (悟空调度器命令行接口)

Usage:
    python3 cli.py analyze "任务描述"
    python3 cli.py plan "任务描述"
"""

import sys
import json
from typing import Optional

try:
    from scheduler import WukongScheduler, TrackType, AvatarType, AVATAR_CONFIG, TRACK_DAG
    from todo_integration import TodoWriteIntegration, generate_summoning_declaration
except ImportError:
    from .scheduler import WukongScheduler, TrackType, AvatarType, AVATAR_CONFIG, TRACK_DAG
    from .todo_integration import TodoWriteIntegration, generate_summoning_declaration


def analyze_task(task: str) -> dict:
    """Analyze task and return scheduling info"""
    scheduler = WukongScheduler()
    track = scheduler.detect_track(task)

    # Get DAG for this track
    dag = TRACK_DAG.get(track, [])

    phases = []
    for phase_idx, avatars in enumerate(dag):
        phase_info = {
            "phase": phase_idx + 1,
            "avatars": [],
            "parallel": len(avatars) > 1,
        }
        for avatar in avatars:
            config = AVATAR_CONFIG[avatar]
            phase_info["avatars"].append({
                "type": avatar.value,
                "name": avatar.name,
                "model": config["model"],
                "background": config["background"],
                "cost": config["cost"].value,
            })
        phases.append(phase_info)

    return {
        "task": task,
        "track": track.value,
        "phases": phases,
        "total_phases": len(phases),
    }


def format_analysis(analysis: dict) -> str:
    """Format analysis result as markdown"""
    lines = [
        "## Scheduler Analysis Result",
        "",
        "### Task Info",
        f"- **Description**: {analysis['task']}",
        f"- **Track**: {analysis['track'].upper()}",
        "",
        "### Execution Plan",
        "",
        "| Phase | Avatar | Model | Background | Cost |",
        "|-------|--------|-------|------------|------|",
    ]

    for phase in analysis["phases"]:
        phase_num = phase["phase"]
        for avatar in phase["avatars"]:
            emoji_map = {"EYE": "eye", "EAR": "ear", "NOSE": "nose",
                        "TONGUE": "tongue", "BODY": "body", "MIND": "mind"}
            lines.append(
                f"| {phase_num} | {avatar['type']} ({avatar['name']}) | "
                f"{avatar['model']} | {avatar['background']} | {avatar['cost']} |"
            )

    lines.extend([
        "",
        "### Parallel Strategy",
    ])

    for phase in analysis["phases"]:
        parallel_str = "parallel" if phase["parallel"] else "sequential"
        avatars_str = " + ".join(a["type"] for a in phase["avatars"])
        lines.append(f"- **Phase {phase['phase']}**: {avatars_str} ({parallel_str})")

    return "\n".join(lines)


def generate_todo_items(analysis: dict) -> list:
    """Generate TodoWrite-compatible items from analysis"""
    todos = []
    for phase in analysis["phases"]:
        for avatar in phase["avatars"]:
            todos.append({
                "content": f"[Phase {phase['phase']}] {avatar['type']}分身: {analysis['task'][:50]}",
                "status": "pending",
                "activeForm": f"Executing {avatar['type']}分身 task",
            })
    return todos


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 cli.py <command> <task>")
        print("Commands: analyze, plan, todo")
        sys.exit(1)

    command = sys.argv[1]
    task = sys.argv[2]

    if command == "analyze":
        analysis = analyze_task(task)
        print(format_analysis(analysis))

    elif command == "plan":
        analysis = analyze_task(task)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))

    elif command == "todo":
        analysis = analyze_task(task)
        todos = generate_todo_items(analysis)
        print(json.dumps(todos, indent=2, ensure_ascii=False))

    elif command == "json":
        # Full JSON output for programmatic use
        analysis = analyze_task(task)
        analysis["todos"] = generate_todo_items(analysis)
        print(json.dumps(analysis, ensure_ascii=False))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
