#!/usr/bin/env python3
"""
Wukong on_subagent_stop Hook - SubagentStop Event Handler

This hook is triggered when a subagent (avatar) completes its execution.
It performs:
1. Evidence validation according to the Evidence Skill
2. Output format verification
3. Downstream node triggering
4. Artifact archival

Usage:
    This hook is called by the runtime when a SubagentStop event is emitted.
    It can also be invoked directly:

    python3 on_subagent_stop.py --node-id eye_explore --graph-id tg_abc123 --output '{"summary": "..."}'
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple


# Add parent directory to path for imports
script_dir = Path(__file__).parent.resolve()
runtime_dir = script_dir.parent / "runtime"
if str(runtime_dir) not in sys.path:
    sys.path.insert(0, str(runtime_dir))


# Evidence level patterns
L0_PATTERNS = [
    r"应该可以",
    r"大概能",
    r"我觉得",
    r"我认为",
    r"一般来说",
    r"通常",
    r"显然",
    r"当然",
    r"没有问题",
    r"应该没事",
    r"probably",
    r"i think",
    r"i believe",
    r"usually",
    r"obviously",
    r"of course",
    r"should be fine",
    r"no problem",
]

# Healthy evidence patterns
HEALTHY_PATTERNS = [
    r"根据\s+[\w/\.]+:\d+",  # 根据 path:line
    r"执行\s+.+\s+输出",  # 执行 command 输出
    r"测试\s+\w+\s+通过",  # 测试 name 通过
    r"文件\s+.+\s+已创建",  # 文件 path 已创建
    r"according to\s+[\w/\.]+:\d+",
    r"executed\s+.+\s+output",
    r"test\s+\w+\s+passed",
    r"file\s+.+\s+created",
    r"\d+\s+passed",  # pytest output
    r"build\s+succeeded",
    r"构建成功",
]

# Track evidence thresholds
TRACK_THRESHOLDS = {
    "fix": "L2",
    "feature": "L2",
    "refactor": "L2",
    "direct": "L1",
}


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def detect_l0_signals(text: str) -> List[str]:
    """
    Detect L0 (speculation) signals in text.

    Args:
        text: Text to analyze

    Returns:
        List of matched L0 patterns
    """
    text_lower = text.lower()
    matches = []

    for pattern in L0_PATTERNS:
        if re.search(pattern, text_lower):
            matches.append(pattern)

    return matches


def detect_healthy_signals(text: str) -> List[str]:
    """
    Detect healthy evidence signals in text.

    Args:
        text: Text to analyze

    Returns:
        List of matched healthy patterns
    """
    text_lower = text.lower()
    matches = []

    for pattern in HEALTHY_PATTERNS:
        if re.search(pattern, text_lower):
            matches.append(pattern)

    return matches


def evaluate_evidence_level(output: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Evaluate the evidence level of subagent output.

    Args:
        output: Subagent output dictionary

    Returns:
        Tuple of (evidence_level, reasons)
    """
    # Extract text content
    text_parts = []

    if "summary" in output:
        text_parts.append(output["summary"])

    if "content" in output:
        text_parts.append(output["content"])

    if "findings" in output:
        if isinstance(output["findings"], list):
            text_parts.extend(str(f) for f in output["findings"])
        else:
            text_parts.append(str(output["findings"]))

    if "claims" in output:
        if isinstance(output["claims"], list):
            text_parts.extend(str(c) for c in output["claims"])
        else:
            text_parts.append(str(output["claims"]))

    full_text = "\n".join(text_parts)

    # Check for L0 signals (speculation)
    l0_signals = detect_l0_signals(full_text)
    if l0_signals:
        return "L0", [f"Speculation detected: {', '.join(l0_signals)}"]

    # Check for healthy signals
    healthy_signals = detect_healthy_signals(full_text)

    # Check for command execution evidence
    has_commands = "commands_executed" in output and output["commands_executed"]

    # Check for test results
    has_tests = any(
        key in output for key in ["test_results", "tests_passed", "pytest_output"]
    )

    # Determine level
    reasons = []

    if has_tests or "端到端" in full_text or "end-to-end" in full_text.lower():
        level = "L3"
        reasons.append("End-to-end or test verification present")
    elif has_commands or healthy_signals:
        level = "L2"
        if has_commands:
            reasons.append("Command execution recorded")
        if healthy_signals:
            reasons.append(f"Evidence patterns found: {', '.join(healthy_signals[:3])}")
    else:
        level = "L1"
        reasons.append("Reference only, no local verification")

    return level, reasons


def validate_output_format(output: Dict[str, Any], node_role: str) -> Tuple[bool, List[str]]:
    """
    Validate that output follows the expected format for the node role.

    Args:
        output: Subagent output dictionary
        node_role: Role of the node (eye, ear, nose, etc.)

    Returns:
        Tuple of (is_valid, issues)
    """
    issues = []

    # All outputs should have a summary
    if "summary" not in output:
        issues.append("Missing 'summary' field")

    # Role-specific validation
    if node_role in ("eye", "explorer"):
        # Explorer should have files or findings
        if "files" not in output and "findings" not in output:
            issues.append("Explorer output should have 'files' or 'findings'")

    elif node_role in ("nose", "reviewer"):
        # Reviewer should have issues or verdict
        if "issues" not in output and "verdict" not in output:
            issues.append("Reviewer output should have 'issues' or 'verdict'")

    elif node_role in ("body", "impl", "斗战胜佛"):
        # Implementation should have changes or artifacts
        if "changes" not in output and "artifacts" not in output and "files_modified" not in output:
            issues.append("Implementation output should have 'changes', 'artifacts', or 'files_modified'")

    elif node_role in ("tongue", "tester"):
        # Tester should have test results
        if "test_results" not in output and "tests" not in output:
            issues.append("Tester output should have 'test_results' or 'tests'")

    return len(issues) == 0, issues


def check_track_threshold(evidence_level: str, track: str) -> Tuple[bool, str]:
    """
    Check if evidence level meets track threshold.

    Args:
        evidence_level: Current evidence level (L0-L3)
        track: Track type (fix, feature, refactor, direct)

    Returns:
        Tuple of (meets_threshold, message)
    """
    threshold = TRACK_THRESHOLDS.get(track, "L2")

    level_order = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}
    current = level_order.get(evidence_level, 0)
    required = level_order.get(threshold, 2)

    if current >= required:
        return True, f"Evidence level {evidence_level} meets {track} track threshold ({threshold})"
    else:
        return False, f"Evidence level {evidence_level} below {track} track threshold ({threshold})"


def process_subagent_stop(
    node_id: str,
    graph_id: str,
    output: Dict[str, Any],
    track: str = "direct",
    node_role: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process a SubagentStop event.

    Args:
        node_id: ID of the completed node
        graph_id: ID of the task graph
        output: Subagent output dictionary
        track: Track type
        node_role: Role of the node

    Returns:
        Processing result dictionary
    """
    result = {
        "node_id": node_id,
        "graph_id": graph_id,
        "timestamp": get_timestamp(),
        "success": True,
        "evidence": {},
        "validation": {},
        "next_actions": [],
    }

    # Infer node role from node_id if not provided
    if not node_role:
        if "eye" in node_id or "explore" in node_id:
            node_role = "eye"
        elif "ear" in node_id or "understand" in node_id:
            node_role = "ear"
        elif "nose" in node_id or "review" in node_id:
            node_role = "nose"
        elif "tongue" in node_id or "test" in node_id or "verify" in node_id:
            node_role = "tongue"
        elif "body" in node_id or "impl" in node_id:
            node_role = "body"
        elif "mind" in node_id or "design" in node_id:
            node_role = "mind"
        else:
            node_role = "unknown"

    # 1. Evaluate evidence level
    evidence_level, evidence_reasons = evaluate_evidence_level(output)
    result["evidence"] = {
        "level": evidence_level,
        "reasons": evidence_reasons,
    }

    # 2. Check track threshold
    meets_threshold, threshold_msg = check_track_threshold(evidence_level, track)
    result["evidence"]["meets_threshold"] = meets_threshold
    result["evidence"]["threshold_message"] = threshold_msg

    # 3. Validate output format
    format_valid, format_issues = validate_output_format(output, node_role)
    result["validation"] = {
        "format_valid": format_valid,
        "issues": format_issues,
    }

    # 4. Determine overall success
    if evidence_level == "L0":
        result["success"] = False
        result["error"] = "Evidence level L0 (speculation) is not acceptable"
        result["next_actions"].append({
            "action": "request_verification",
            "message": "Subagent output contains speculation. Requires concrete evidence.",
        })
    elif not meets_threshold:
        result["success"] = False
        result["error"] = threshold_msg
        result["next_actions"].append({
            "action": "request_verification",
            "message": f"Evidence level {evidence_level} insufficient for {track} track.",
        })
    elif not format_valid:
        # Format issues are warnings, not failures
        result["warnings"] = format_issues
        result["next_actions"].append({
            "action": "note_format_issues",
            "message": f"Output format issues: {', '.join(format_issues)}",
        })

    # 5. If successful, suggest downstream actions
    if result["success"]:
        result["next_actions"].append({
            "action": "trigger_downstream",
            "message": f"Node {node_id} completed successfully. Ready to trigger downstream nodes.",
        })

        # Check for potential anchor candidates
        if evidence_level in ("L2", "L3"):
            result["next_actions"].append({
                "action": "check_anchor_candidate",
                "message": "High evidence level output may contain anchor candidates.",
            })

    return result


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Process SubagentStop event",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--node-id",
        required=True,
        help="ID of the completed node",
    )
    parser.add_argument(
        "--graph-id",
        required=True,
        help="ID of the task graph",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Subagent output as JSON string",
    )
    parser.add_argument(
        "--track",
        default="direct",
        choices=["fix", "feature", "refactor", "direct"],
        help="Track type (default: direct)",
    )
    parser.add_argument(
        "--role",
        help="Node role (eye, ear, nose, tongue, body, mind)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    # Parse output JSON
    try:
        output = json.loads(args.output)
    except json.JSONDecodeError as e:
        result = {
            "success": False,
            "error": f"Invalid JSON in output: {e}",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    # Process the event
    result = process_subagent_stop(
        node_id=args.node_id,
        graph_id=args.graph_id,
        output=output,
        track=args.track,
        node_role=args.role,
    )

    # Output result
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # Human-readable output
        print(f"Node: {result['node_id']}")
        print(f"Graph: {result['graph_id']}")
        print(f"Success: {'Yes' if result['success'] else 'No'}")
        print(f"\nEvidence Level: {result['evidence']['level']}")
        print(f"Meets Threshold: {'Yes' if result['evidence'].get('meets_threshold') else 'No'}")

        if result['evidence'].get('reasons'):
            print("Reasons:")
            for reason in result['evidence']['reasons']:
                print(f"  - {reason}")

        if not result['validation'].get('format_valid', True):
            print("\nFormat Issues:")
            for issue in result['validation'].get('issues', []):
                print(f"  - {issue}")

        if result.get('error'):
            print(f"\nError: {result['error']}")

        if result.get('warnings'):
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")

        if result.get('next_actions'):
            print("\nNext Actions:")
            for action in result['next_actions']:
                print(f"  - [{action['action']}] {action['message']}")

    # Exit with appropriate code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
