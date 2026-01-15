"""
并行快照机制 (Parallel Snapshot Mechanism)

提供不可变的上下文快照，用于并行分身召唤时传递一致的上下文。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any


@dataclass(frozen=True)
class Anchor:
    """锚点数据"""
    anchor_type: str  # P(问题), C(约束), M(模式), D(决策), I(接口)
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ContextSnapshot:
    """不可变的上下文快照"""
    session_id: str
    timestamp: datetime
    compact_context: str  # 缩形态 (<500字)
    anchors: List[Anchor]  # 相关锚点
    metadata: Dict[str, Any] = field(default_factory=dict)


def create_snapshot(
    session_id: str,
    compact_context: str,
    anchors: List[Dict[str, Any]],
    metadata: Dict[str, Any] = None
) -> ContextSnapshot:
    """
    创建上下文快照

    Args:
        session_id: 会话 ID
        compact_context: 缩形态上下文 (应 <500 字)
        anchors: 锚点列表，每个锚点是字典 {"type": "D", "content": "...", ...}
        metadata: 可选的元数据

    Returns:
        不可变的 ContextSnapshot 对象
    """
    anchor_objects = [
        Anchor(
            anchor_type=a.get('type', 'P'),
            content=a.get('content', ''),
            metadata={k: v for k, v in a.items() if k not in ('type', 'content')}
        )
        for a in anchors
    ]

    return ContextSnapshot(
        session_id=session_id,
        timestamp=datetime.now(),
        compact_context=compact_context,
        anchors=anchor_objects,
        metadata=metadata or {}
    )


def get_snapshot_for_task(snapshot: ContextSnapshot, task_id: str) -> str:
    """
    将快照格式化为 prompt 片段，用于注入到分身 Task 中

    Args:
        snapshot: 上下文快照
        task_id: 任务 ID (用于日志追踪)

    Returns:
        格式化的 prompt 字符串
    """
    lines = [
        "## 上下文快照 (Context Snapshot)",
        f"Session: {snapshot.session_id}",
        f"Task: {task_id}",
        "",
        "### 缩形态上下文",
        snapshot.compact_context,
        "",
    ]

    if snapshot.anchors:
        lines.append("### 相关锚点")
        for anchor in snapshot.anchors:
            lines.append(f"- [{anchor.anchor_type}] {anchor.content}")
        lines.append("")

    return "\n".join(lines)
