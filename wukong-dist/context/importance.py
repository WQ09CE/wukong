"""
重要性标注系统 (Importance Marking System)

为分身输出内容标注重要性级别，用于智能压缩和优先级排序。
"""

from dataclasses import dataclass
from enum import Enum
from typing import List


class Importance(Enum):
    """重要性级别"""
    HIGH = "high"      # 必须保留 (关键文件、严重问题、核心决策)
    MEDIUM = "medium"  # 优先保留 (相关文件、一般问题、辅助信息)
    LOW = "low"        # 可丢弃 (辅助文件、细节信息、冗余内容)


@dataclass
class MarkedContent:
    """带重要性标记的内容"""
    content: str
    importance: Importance
    category: str  # file, issue, decision, suggestion, etc.
    source: str    # avatar name (眼分身, 鼻分身, etc.)

    def __len__(self) -> int:
        """返回内容长度"""
        return len(self.content)


def mark(
    content: str,
    importance: Importance,
    category: str,
    source: str
) -> MarkedContent:
    """
    标注内容的重要性

    Args:
        content: 内容文本
        importance: 重要性级别
        category: 内容类别 (file, issue, decision, etc.)
        source: 来源分身名称

    Returns:
        MarkedContent 对象
    """
    return MarkedContent(
        content=content,
        importance=importance,
        category=category,
        source=source
    )


def compress_by_importance(
    items: List[MarkedContent],
    max_chars: int
) -> List[MarkedContent]:
    """
    按重要性压缩内容，优先保留 HIGH，然后 MEDIUM，最后 LOW

    Args:
        items: 标注内容列表
        max_chars: 最大字符数限制

    Returns:
        压缩后的内容列表 (按重要性排序)
    """
    # 按重要性排序 (HIGH -> MEDIUM -> LOW)
    importance_order = {Importance.HIGH: 0, Importance.MEDIUM: 1, Importance.LOW: 2}
    sorted_items = sorted(items, key=lambda x: importance_order[x.importance])

    # 贪婪选择，直到达到字符限制
    result = []
    total_chars = 0

    for item in sorted_items:
        item_len = len(item)
        if total_chars + item_len <= max_chars:
            result.append(item)
            total_chars += item_len
        elif item.importance == Importance.HIGH:
            # 对于 HIGH 级别，即使超出也尝试截断保留
            remaining = max_chars - total_chars
            if remaining > 50:  # 至少保留 50 字符才有意义
                truncated = MarkedContent(
                    content=item.content[:remaining] + "...",
                    importance=item.importance,
                    category=item.category,
                    source=item.source
                )
                result.append(truncated)
            break

    return result


def format_marked_output(items: List[MarkedContent]) -> str:
    """
    格式化带标记的输出，便于阅读和注入到 prompt

    Args:
        items: 标注内容列表

    Returns:
        格式化的字符串
    """
    if not items:
        return ""

    lines = []

    # 按重要性分组
    high_items = [x for x in items if x.importance == Importance.HIGH]
    medium_items = [x for x in items if x.importance == Importance.MEDIUM]
    low_items = [x for x in items if x.importance == Importance.LOW]

    if high_items:
        lines.append("### 高优先级 (HIGH)")
        for item in high_items:
            lines.append(f"- [{item.category}] ({item.source}) {item.content}")
        lines.append("")

    if medium_items:
        lines.append("### 中优先级 (MEDIUM)")
        for item in medium_items:
            lines.append(f"- [{item.category}] ({item.source}) {item.content}")
        lines.append("")

    if low_items:
        lines.append("### 低优先级 (LOW)")
        for item in low_items:
            lines.append(f"- [{item.category}] ({item.source}) {item.content}")
        lines.append("")

    return "\n".join(lines)
