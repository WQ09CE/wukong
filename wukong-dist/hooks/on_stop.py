#!/usr/bin/env python3
"""
Wukong on_stop Hook - Stop Event Handler (Task Completion)

This hook is triggered when a task graph completes (all nodes done).
It performs:
1. Aggregation of all node outputs
2. Extraction of potential anchor candidates
3. Writing candidates to the anchor system
4. Generation of task completion summary

Usage:
    This hook is called by the runtime when a Stop event is emitted.
    It can also be invoked directly:

    python3 on_stop.py --graph-id tg_abc123 --artifacts-dir ~/.wukong/artifacts
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


# Default paths
DEFAULT_WUKONG_DIR = Path.home() / ".wukong"
DEFAULT_ARTIFACTS_DIR = DEFAULT_WUKONG_DIR / "artifacts"
DEFAULT_ANCHORS_DIR = DEFAULT_WUKONG_DIR / "anchors"


# Anchor extraction patterns
DECISION_PATTERNS = [
    (r"(?:我们)?决定\s*[:：]?\s*(.+?)(?:\.|。|$)", "zh"),
    (r"(?:我们)?选择\s*[:：]?\s*(.+?)(?:\.|。|$)", "zh"),
    (r"(?:我们)?采用\s*[:：]?\s*(.+?)(?:\.|。|$)", "zh"),
    (r"decided\s+to\s+(.+?)(?:\.|$)", "en"),
    (r"chose\s+to\s+(?:use\s+)?(.+?)(?:\.|$)", "en"),
    (r"selected\s+(.+?)(?:\s+for|\.|$)", "en"),
    (r"using\s+(.+?)\s+(?:for|because|as)", "en"),
]

CONSTRAINT_PATTERNS = [
    (r"必须\s*[:：]?\s*(.+?)(?:\.|。|$)", "zh"),
    (r"不能\s*[:：]?\s*(.+?)(?:\.|。|$)", "zh"),
    (r"限制\s*[:：]?\s*(.+?)(?:\.|。|$)", "zh"),
    (r"要求\s*[:：]?\s*(.+?)(?:\.|。|$)", "zh"),
    (r"must\s+(.+?)(?:\.|$)", "en"),
    (r"cannot\s+(.+?)(?:\.|$)", "en"),
    (r"constraint[:\s]+(.+?)(?:\.|$)", "en"),
    (r"require(?:s|d)?\s+(.+?)(?:\.|$)", "en"),
]

LESSON_PATTERNS = [
    (r"教训\s*[:：]?\s*(.+?)(?:\.|。|$)", "zh"),
    (r"发现\s*[:：]?\s*(.+?)(?:\.|。|$)", "zh"),
    (r"注意\s*[:：]?\s*(.+?)(?:\.|。|$)", "zh"),
    (r"lesson[:\s]+(.+?)(?:\.|$)", "en"),
    (r"learned\s+(?:that\s+)?(.+?)(?:\.|$)", "en"),
    (r"discovered\s+(?:that\s+)?(.+?)(?:\.|$)", "en"),
    (r"found\s+(?:that\s+)?(.+?)(?:\.|$)", "en"),
    (r"gotcha[:\s]+(.+?)(?:\.|$)", "en"),
]

INTERFACE_PATTERNS = [
    (r"接口\s*[:：]?\s*(.+?)(?:\.|。|$)", "zh"),
    (r"API\s*[:：]?\s*(.+?)(?:\.|$)", "en"),
    (r"schema\s*[:：]?\s*(.+?)(?:\.|$)", "en"),
    (r"endpoint\s*[:：]?\s*(.+?)(?:\.|$)", "en"),
    (r"定义(?:了)?\s*(.+?)\s*(?:接口|格式|协议)", "zh"),
]


def get_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    Extract keywords from text.

    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords

    Returns:
        List of keywords
    """
    # Common stop words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall",
        "can", "need", "to", "of", "in", "for", "on", "with", "at",
        "by", "from", "as", "into", "through", "during", "before",
        "after", "above", "below", "between", "under", "and", "but",
        "if", "or", "because", "until", "while", "this", "that",
        "的", "了", "是", "在", "我", "有", "和", "就", "不",
        "都", "一", "一个", "上", "也", "很", "到", "说", "要",
    }

    # Tokenize
    words = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())

    # Filter and count
    word_counts: Dict[str, int] = {}
    for word in words:
        if word not in stop_words and len(word) > 1:
            word_counts[word] = word_counts.get(word, 0) + 1

    # Sort by frequency and return top keywords
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:max_keywords]]


def extract_anchor_candidates(
    text: str,
    source: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Extract potential anchor candidates from text.

    Args:
        text: Text to analyze
        source: Optional source information (graph_id, node_id)

    Returns:
        List of anchor candidate dictionaries
    """
    candidates = []

    # Try each pattern type
    pattern_configs = [
        ("decision", DECISION_PATTERNS),
        ("constraint", CONSTRAINT_PATTERNS),
        ("lesson", LESSON_PATTERNS),
        ("interface", INTERFACE_PATTERNS),
    ]

    for anchor_type, patterns in pattern_configs:
        for pattern, lang in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                content = match.group(1).strip()

                # Skip very short or very long matches
                if len(content) < 10 or len(content) > 500:
                    continue

                # Generate title from content
                title = content[:50] + "..." if len(content) > 50 else content

                # Extract keywords
                keywords = extract_keywords(content)

                candidate = {
                    "type": anchor_type,
                    "title": title,
                    "content": content,
                    "keywords": keywords,
                    "evidence_level": "L1",  # Default to L1, will be upgraded if verified
                }

                if source:
                    candidate["source"] = source

                candidates.append(candidate)

    # Deduplicate by content similarity
    unique_candidates = []
    seen_content = set()
    for candidate in candidates:
        # Simple dedup by first 50 chars of content
        key = candidate["content"][:50].lower()
        if key not in seen_content:
            seen_content.add(key)
            unique_candidates.append(candidate)

    return unique_candidates


def aggregate_node_outputs(
    graph_id: str,
    artifacts_dir: Path,
) -> Dict[str, Any]:
    """
    Aggregate outputs from all nodes in a task graph.

    Args:
        graph_id: Task graph ID
        artifacts_dir: Path to artifacts directory

    Returns:
        Aggregated output dictionary
    """
    graph_dir = artifacts_dir / graph_id
    aggregated = {
        "graph_id": graph_id,
        "nodes": {},
        "all_text": "",
        "summaries": [],
    }

    if not graph_dir.exists():
        return aggregated

    # Read each node's output
    for node_dir in graph_dir.iterdir():
        if not node_dir.is_dir():
            continue

        node_id = node_dir.name
        output_file = node_dir / "output.json"
        summary_file = node_dir / "summary.md"

        if output_file.exists():
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    aggregated["nodes"][node_id] = data.get("output", {})

                    # Add to all_text for pattern matching
                    if "summary" in data.get("output", {}):
                        aggregated["all_text"] += data["output"]["summary"] + "\n"
                        aggregated["summaries"].append({
                            "node_id": node_id,
                            "summary": data["output"]["summary"],
                        })
            except (json.JSONDecodeError, IOError):
                pass

        if summary_file.exists():
            try:
                with open(summary_file, "r", encoding="utf-8") as f:
                    summary_content = f.read()
                    aggregated["all_text"] += summary_content + "\n"
            except IOError:
                pass

    return aggregated


def write_anchor_candidates(
    candidates: List[Dict[str, Any]],
    anchors_dir: Path,
) -> List[str]:
    """
    Write anchor candidates to the anchor system.

    Args:
        candidates: List of anchor candidates
        anchors_dir: Path to anchors directory

    Returns:
        List of generated candidate IDs
    """
    import uuid

    anchors_dir.mkdir(parents=True, exist_ok=True)
    candidates_file = anchors_dir / "candidates.json"

    # Load existing candidates
    if candidates_file.exists():
        try:
            with open(candidates_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = {"candidates": {}}
    else:
        data = {"candidates": {}, "created_at": get_timestamp()}

    # Add new candidates
    candidate_ids = []
    for candidate in candidates:
        candidate_id = f"cand_{uuid.uuid4().hex[:12]}"
        candidate["id"] = candidate_id
        candidate["created_at"] = get_timestamp()
        data["candidates"][candidate_id] = candidate
        candidate_ids.append(candidate_id)

    # Update timestamp
    data["updated_at"] = get_timestamp()

    # Write back
    with open(candidates_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return candidate_ids


def generate_completion_summary(
    graph_id: str,
    aggregated: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> str:
    """
    Generate a task completion summary.

    Args:
        graph_id: Task graph ID
        aggregated: Aggregated outputs
        candidates: Extracted anchor candidates

    Returns:
        Markdown formatted summary
    """
    lines = [
        "# Task Completion Summary",
        "",
        f"**Graph ID**: `{graph_id}`",
        f"**Completed At**: {get_timestamp()}",
        f"**Nodes Completed**: {len(aggregated.get('nodes', {}))}",
        "",
        "## Node Summaries",
        "",
    ]

    for summary in aggregated.get("summaries", []):
        lines.append(f"### {summary['node_id']}")
        lines.append("")
        lines.append(summary["summary"])
        lines.append("")

    if candidates:
        lines.append("## Extracted Anchor Candidates")
        lines.append("")
        lines.append(f"**Total Candidates**: {len(candidates)}")
        lines.append("")

        for candidate in candidates:
            lines.append(f"### [{candidate['type'].upper()}] {candidate['title']}")
            lines.append("")
            lines.append(f"**ID**: `{candidate.get('id', 'N/A')}`")
            lines.append(f"**Keywords**: {', '.join(candidate.get('keywords', []))}")
            lines.append("")
            lines.append(candidate["content"][:200])
            if len(candidate["content"]) > 200:
                lines.append("...")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_Use `cli.py anchor list-candidates` to review and promote candidates._")

    return "\n".join(lines)


def process_stop_event(
    graph_id: str,
    artifacts_dir: Path,
    anchors_dir: Path,
    project: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Process a Stop event (task completion).

    Args:
        graph_id: Task graph ID
        artifacts_dir: Path to artifacts directory
        anchors_dir: Path to anchors directory
        project: Optional project name

    Returns:
        Processing result dictionary
    """
    result = {
        "graph_id": graph_id,
        "timestamp": get_timestamp(),
        "success": True,
        "aggregation": {},
        "candidates": [],
        "summary": "",
    }

    # 1. Aggregate node outputs
    aggregated = aggregate_node_outputs(graph_id, artifacts_dir)
    result["aggregation"] = {
        "nodes_processed": len(aggregated.get("nodes", {})),
        "text_length": len(aggregated.get("all_text", "")),
    }

    # 2. Extract anchor candidates
    candidates = extract_anchor_candidates(
        aggregated.get("all_text", ""),
        source={"graph_id": graph_id, "node_id": "aggregate"},
    )
    result["candidates_extracted"] = len(candidates)

    # 3. Write candidates to anchor system
    if candidates:
        candidate_ids = write_anchor_candidates(candidates, anchors_dir)
        result["candidates"] = candidate_ids

    # 4. Generate completion summary
    summary = generate_completion_summary(graph_id, aggregated, candidates)
    result["summary"] = summary

    # 5. Write summary to artifacts
    summary_file = artifacts_dir / graph_id / "completion_summary.md"
    try:
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary)
        result["summary_file"] = str(summary_file)
    except IOError as e:
        result["warnings"] = [f"Failed to write summary: {e}"]

    return result


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Process Stop event (task completion)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--graph-id",
        required=True,
        help="ID of the completed task graph",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=DEFAULT_ARTIFACTS_DIR,
        help=f"Path to artifacts directory (default: {DEFAULT_ARTIFACTS_DIR})",
    )
    parser.add_argument(
        "--anchors-dir",
        type=Path,
        default=DEFAULT_ANCHORS_DIR,
        help=f"Path to anchors directory (default: {DEFAULT_ANCHORS_DIR})",
    )
    parser.add_argument(
        "--project",
        help="Project name for project-specific anchors",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    # Process the stop event
    result = process_stop_event(
        graph_id=args.graph_id,
        artifacts_dir=args.artifacts_dir,
        anchors_dir=args.anchors_dir,
        project=args.project,
    )

    # Output result
    if args.json:
        # For JSON output, don't include the full summary text
        json_result = {k: v for k, v in result.items() if k != "summary"}
        json_result["summary_length"] = len(result.get("summary", ""))
        print(json.dumps(json_result, ensure_ascii=False, indent=2))
    else:
        # Human-readable output
        print(f"Task Completion: {result['graph_id']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"\nAggregation:")
        print(f"  Nodes processed: {result['aggregation'].get('nodes_processed', 0)}")
        print(f"  Text analyzed: {result['aggregation'].get('text_length', 0)} chars")

        print(f"\nAnchor Candidates Extracted: {result.get('candidates_extracted', 0)}")
        if result.get("candidates"):
            print("  Candidate IDs:")
            for cid in result["candidates"]:
                print(f"    - {cid}")

        if result.get("summary_file"):
            print(f"\nSummary written to: {result['summary_file']}")

        if result.get("warnings"):
            print("\nWarnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")

        print("\n" + "=" * 60)
        print(result.get("summary", ""))

    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
