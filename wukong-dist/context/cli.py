#!/usr/bin/env python3
"""
Wukong Context CLI (悟空上下文命令行接口)

Usage:
    python3 cli.py snapshot create --session=xxx --context="缩形态内容" --anchors='[{"type":"D","content":"..."}]'
    python3 cli.py snapshot format --session=xxx --task=yyy
    python3 cli.py aggregate add --task=xxx --avatar=眼 --output="结果内容"
    python3 cli.py aggregate summary
"""

import sys
import json
import argparse
import os
import fcntl
import tempfile
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

try:
    from snapshot import ContextSnapshot, create_snapshot, get_snapshot_for_task, Anchor
    from importance import Importance, mark, compress_by_importance, format_marked_output, MarkedContent
    from aggregator import TaskResult, ResultAggregator
except ImportError:
    from .snapshot import ContextSnapshot, create_snapshot, get_snapshot_for_task, Anchor
    from .importance import Importance, mark, compress_by_importance, format_marked_output, MarkedContent
    from .aggregator import TaskResult, ResultAggregator


# Persistence paths
CONTEXT_DIR = Path(__file__).parent
STATE_DIR = CONTEXT_DIR / "state"
STATE_DIR.mkdir(exist_ok=True)


def _get_session_hash(session_id: str) -> str:
    """Generate short hash for session ID to use in filename"""
    return hashlib.md5(session_id.encode()).hexdigest()[:8]


def _get_aggregator_file(session_id: str) -> Path:
    """Get session-specific aggregator state file"""
    return STATE_DIR / f"aggregator_{_get_session_hash(session_id)}.json"


def _get_snapshot_file(session_id: str) -> Path:
    """Get session-specific snapshot state file"""
    return STATE_DIR / f"snapshot_{_get_session_hash(session_id)}.json"


@contextmanager
def _file_lock(filepath: Path, exclusive: bool = True):
    """
    Context manager for file locking (Unix compatible).

    Args:
        filepath: Path to the file to lock
        exclusive: True for write lock, False for read lock
    """
    lock_file = filepath.with_suffix('.lock')
    lock_file.touch(exist_ok=True)

    with open(lock_file, 'r+') as f:
        try:
            if exclusive:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def _atomic_write(filepath: Path, data: dict) -> None:
    """
    Atomic write using temp file + rename.

    Args:
        filepath: Target file path
        data: Data to write as JSON
    """
    # Write to temp file in same directory (for atomic rename)
    fd, temp_path = tempfile.mkstemp(
        dir=filepath.parent,
        prefix=f'.{filepath.stem}_',
        suffix='.tmp'
    )

    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Atomic rename (POSIX guarantees atomicity on same filesystem)
        os.rename(temp_path, filepath)
    except Exception:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def _load_aggregator(session_id: str) -> ResultAggregator:
    """Load aggregator state from session-specific file with locking"""
    aggregator = ResultAggregator()
    state_file = _get_aggregator_file(session_id)

    if not state_file.exists():
        return aggregator

    with _file_lock(state_file, exclusive=False):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for result_data in data.get('results', []):
                marked_items = []
                for item_data in result_data.get('marked_items', []):
                    importance = Importance[item_data.get('importance', 'MEDIUM').upper()]
                    marked_items.append(MarkedContent(
                        content=item_data.get('content', ''),
                        importance=importance,
                        category=item_data.get('category', 'general'),
                        source=item_data.get('source', '')
                    ))

                result = TaskResult(
                    task_id=result_data.get('task_id', ''),
                    avatar=result_data.get('avatar', ''),
                    status=result_data.get('status', 'completed'),
                    output=result_data.get('output', ''),
                    marked_items=marked_items,
                    metadata=result_data.get('metadata', {})
                )
                aggregator.results.append(result)
        except (json.JSONDecodeError, KeyError):
            # If file is corrupted, start fresh
            pass

    return aggregator


def _save_aggregator(aggregator: ResultAggregator, session_id: str) -> None:
    """Save aggregator state to session-specific file with locking and atomic write"""
    state_file = _get_aggregator_file(session_id)

    data = {
        'session_id': session_id,
        'results': [
            {
                'task_id': r.task_id,
                'avatar': r.avatar,
                'status': r.status,
                'output': r.output,
                'marked_items': [
                    {
                        'content': item.content,
                        'importance': item.importance.value,
                        'category': item.category,
                        'source': item.source
                    }
                    for item in r.marked_items
                ],
                'metadata': r.metadata
            }
            for r in aggregator.results
        ],
        'updated_at': datetime.now().isoformat()
    }

    with _file_lock(state_file, exclusive=True):
        _atomic_write(state_file, data)


def _load_snapshot(session_id: str) -> Optional[ContextSnapshot]:
    """Load snapshot state from session-specific file with locking"""
    state_file = _get_snapshot_file(session_id)

    if not state_file.exists():
        return None

    with _file_lock(state_file, exclusive=False):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            anchors = [
                {'type': a.get('type', 'P'), 'content': a.get('content', '')}
                for a in data.get('anchors', [])
            ]

            return create_snapshot(
                session_id=data.get('session_id', ''),
                compact_context=data.get('compact_context', ''),
                anchors=anchors,
                metadata=data.get('metadata', {})
            )
        except (json.JSONDecodeError, KeyError):
            return None


def _save_snapshot(snapshot: ContextSnapshot) -> None:
    """Save snapshot state to session-specific file with locking and atomic write"""
    state_file = _get_snapshot_file(snapshot.session_id)

    data = {
        'session_id': snapshot.session_id,
        'timestamp': snapshot.timestamp.isoformat(),
        'compact_context': snapshot.compact_context,
        'anchors': [
            {'type': a.anchor_type, 'content': a.content}
            for a in snapshot.anchors
        ],
        'metadata': dict(snapshot.metadata)
    }

    with _file_lock(state_file, exclusive=True):
        _atomic_write(state_file, data)


def _clear_session(session_id: str) -> None:
    """Clear all state files for a session"""
    for state_file in [_get_aggregator_file(session_id), _get_snapshot_file(session_id)]:
        if state_file.exists():
            lock_file = state_file.with_suffix('.lock')
            state_file.unlink()
            if lock_file.exists():
                lock_file.unlink()


# Global state (loaded on demand)
_current_snapshot: ContextSnapshot = None
_aggregator: ResultAggregator = None
_current_session: str = "default"


def cmd_snapshot_create(args) -> str:
    """Create a new context snapshot"""
    global _current_snapshot

    anchors = json.loads(args.anchors) if args.anchors else []
    metadata = json.loads(args.metadata) if args.metadata else {}

    _current_snapshot = create_snapshot(
        session_id=args.session,
        compact_context=args.context,
        anchors=anchors,
        metadata=metadata
    )

    # Persist to file
    _save_snapshot(_current_snapshot)

    return json.dumps({
        "status": "created",
        "session_id": _current_snapshot.session_id,
        "timestamp": _current_snapshot.timestamp.isoformat(),
        "context_length": len(_current_snapshot.compact_context),
        "anchor_count": len(_current_snapshot.anchors)
    }, ensure_ascii=False)


def cmd_snapshot_format(args) -> str:
    """Format snapshot for task injection"""
    if not _current_snapshot:
        # Create a minimal snapshot if none exists
        snapshot = create_snapshot(
            session_id=args.session or "default",
            compact_context=args.context or "",
            anchors=json.loads(args.anchors) if args.anchors else []
        )
    else:
        snapshot = _current_snapshot

    return get_snapshot_for_task(snapshot, args.task or "unknown")


def cmd_snapshot_show(args) -> str:
    """Show current snapshot info"""
    global _current_snapshot, _current_session

    session_id = args.session or _current_session

    # Load from file
    _current_snapshot = _load_snapshot(session_id)

    if not _current_snapshot:
        return json.dumps({"status": "no_snapshot", "session_id": session_id}, ensure_ascii=False)

    return json.dumps({
        "session_id": _current_snapshot.session_id,
        "timestamp": _current_snapshot.timestamp.isoformat(),
        "compact_context": _current_snapshot.compact_context[:200] + "..." if len(_current_snapshot.compact_context) > 200 else _current_snapshot.compact_context,
        "anchors": [
            {"type": a.anchor_type, "content": a.content[:50] + "..." if len(a.content) > 50 else a.content}
            for a in _current_snapshot.anchors
        ]
    }, indent=2, ensure_ascii=False)


def cmd_aggregate_add(args) -> str:
    """Add a task result to aggregator"""
    global _aggregator, _current_session

    session_id = args.session or _current_session

    # Load existing state for this session
    _aggregator = _load_aggregator(session_id)

    marked_items = []
    if args.items:
        items_data = json.loads(args.items)
        for item in items_data:
            importance = Importance[item.get("importance", "MEDIUM").upper()]
            marked_items.append(mark(
                content=item.get("content", ""),
                importance=importance,
                category=item.get("category", "general"),
                source=args.avatar
            ))

    result = TaskResult(
        task_id=args.task,
        avatar=args.avatar,
        status=args.status or "completed",
        output=args.output or "",
        marked_items=marked_items
    )

    _aggregator.add_result(result)

    # Persist to session-specific file
    _save_aggregator(_aggregator, session_id)

    return json.dumps({
        "status": "added",
        "session_id": session_id,
        "task_id": args.task,
        "total_results": len(_aggregator.results)
    }, ensure_ascii=False)


def cmd_aggregate_summary(args) -> str:
    """Get aggregated summary"""
    global _aggregator, _current_session

    session_id = args.session or _current_session

    # Load existing state for this session
    _aggregator = _load_aggregator(session_id)

    max_chars = args.max_chars or 2000

    if args.compact:
        return _aggregator.get_compact_summary(max_chars=500)
    else:
        return _aggregator.aggregate(max_chars=max_chars)


def cmd_aggregate_clear(args) -> str:
    """Clear aggregator for a session"""
    global _aggregator, _current_session

    session_id = args.session or _current_session

    _aggregator = ResultAggregator()

    # Remove session-specific state files
    _clear_session(session_id)

    return json.dumps({
        "status": "cleared",
        "session_id": session_id
    }, ensure_ascii=False)


def cmd_aggregate_list_sessions(args) -> str:
    """List all active sessions"""
    sessions = []
    for f in STATE_DIR.glob("aggregator_*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                sessions.append({
                    "session_id": data.get("session_id", "unknown"),
                    "result_count": len(data.get("results", [])),
                    "updated_at": data.get("updated_at", "")
                })
        except (json.JSONDecodeError, IOError):
            pass

    return json.dumps({"sessions": sessions}, indent=2, ensure_ascii=False)


def cmd_format_for_task(args) -> str:
    """
    Generate formatted context injection for a Task prompt.
    This is the main function used when summoning avatars.
    """
    # Parse inputs
    context = args.context or ""
    anchors = json.loads(args.anchors) if args.anchors else []
    task_id = args.task or f"task_{datetime.now().strftime('%H%M%S')}"
    session_id = args.session or "current"

    # Create snapshot
    snapshot = create_snapshot(
        session_id=session_id,
        compact_context=context,
        anchors=anchors
    )

    # Format for injection
    output = get_snapshot_for_task(snapshot, task_id)

    return output


def main():
    parser = argparse.ArgumentParser(description="Wukong Context CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # snapshot commands
    snapshot_parser = subparsers.add_parser("snapshot", help="Snapshot operations")
    snapshot_sub = snapshot_parser.add_subparsers(dest="subcommand")

    # snapshot create
    create_parser = snapshot_sub.add_parser("create", help="Create snapshot")
    create_parser.add_argument("--session", required=True, help="Session ID")
    create_parser.add_argument("--context", required=True, help="Compact context (<500 chars)")
    create_parser.add_argument("--anchors", default="[]", help="JSON array of anchors")
    create_parser.add_argument("--metadata", default="{}", help="JSON metadata")

    # snapshot format
    format_parser = snapshot_sub.add_parser("format", help="Format snapshot for task")
    format_parser.add_argument("--session", help="Session ID")
    format_parser.add_argument("--task", help="Task ID")
    format_parser.add_argument("--context", help="Compact context")
    format_parser.add_argument("--anchors", default="[]", help="JSON array of anchors")

    # snapshot show
    show_parser = snapshot_sub.add_parser("show", help="Show current snapshot")
    show_parser.add_argument("--session", default="default", help="Session ID")

    # aggregate commands
    agg_parser = subparsers.add_parser("aggregate", help="Aggregation operations")
    agg_sub = agg_parser.add_subparsers(dest="subcommand")

    # aggregate add
    add_parser = agg_sub.add_parser("add", help="Add task result")
    add_parser.add_argument("--session", default="default", help="Session ID (for isolation)")
    add_parser.add_argument("--task", required=True, help="Task ID")
    add_parser.add_argument("--avatar", required=True, help="Avatar name")
    add_parser.add_argument("--status", default="completed", help="Task status")
    add_parser.add_argument("--output", help="Task output")
    add_parser.add_argument("--items", help="JSON array of marked items")

    # aggregate summary
    summary_parser = agg_sub.add_parser("summary", help="Get summary")
    summary_parser.add_argument("--session", default="default", help="Session ID")
    summary_parser.add_argument("--compact", action="store_true", help="Use compact format")
    summary_parser.add_argument("--max-chars", type=int, default=2000, help="Max characters")

    # aggregate clear
    clear_parser = agg_sub.add_parser("clear", help="Clear aggregator")
    clear_parser.add_argument("--session", default="default", help="Session ID")

    # aggregate list-sessions
    list_parser = agg_sub.add_parser("list-sessions", help="List all sessions")

    # inject command (shortcut for task injection)
    inject_parser = subparsers.add_parser("inject", help="Generate context for Task prompt")
    inject_parser.add_argument("--session", help="Session ID")
    inject_parser.add_argument("--task", help="Task ID")
    inject_parser.add_argument("--context", required=True, help="Compact context")
    inject_parser.add_argument("--anchors", default="[]", help="JSON array of anchors")

    args = parser.parse_args()

    if args.command == "snapshot":
        if args.subcommand == "create":
            print(cmd_snapshot_create(args))
        elif args.subcommand == "format":
            print(cmd_snapshot_format(args))
        elif args.subcommand == "show":
            print(cmd_snapshot_show(args))
        else:
            snapshot_parser.print_help()
    elif args.command == "aggregate":
        if args.subcommand == "add":
            print(cmd_aggregate_add(args))
        elif args.subcommand == "summary":
            print(cmd_aggregate_summary(args))
        elif args.subcommand == "clear":
            print(cmd_aggregate_clear(args))
        elif args.subcommand == "list-sessions":
            print(cmd_aggregate_list_sessions(args))
        else:
            agg_parser.print_help()
    elif args.command == "inject":
        print(cmd_format_for_task(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
