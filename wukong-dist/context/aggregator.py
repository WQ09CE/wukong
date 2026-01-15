"""
结果自动聚合 (Result Aggregator)

聚合多个后台分身的输出结果，自动压缩为常形态或缩形态。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

try:
    from .importance import MarkedContent, Importance, compress_by_importance, format_marked_output
except ImportError:
    from importance import MarkedContent, Importance, compress_by_importance, format_marked_output


@dataclass
class TaskResult:
    """后台任务结果"""
    task_id: str
    avatar: str  # 分身名称 (眼分身, 鼻分身, etc.)
    status: str  # completed, failed, pending
    output: str
    marked_items: List[MarkedContent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResultAggregator:
    """结果聚合器"""

    def __init__(self):
        self.results: List[TaskResult] = []

    def add_result(self, result: TaskResult) -> None:
        """
        添加任务结果

        Args:
            result: TaskResult 对象
        """
        self.results.append(result)

    def aggregate(self, max_chars: int = 2000) -> str:
        """
        聚合为常形态 (结构化输出，默认 2000 字符)

        Args:
            max_chars: 最大字符数限制

        Returns:
            格式化的聚合结果
        """
        if not self.results:
            return "无任务结果"

        # 收集所有标注内容
        all_items = []
        for result in self.results:
            all_items.extend(result.marked_items)

        # 按重要性压缩
        compressed = compress_by_importance(all_items, max_chars)

        # 格式化输出
        lines = [
            f"## 聚合结果 ({len(self.results)} 个任务)",
            ""
        ]

        # 添加任务状态概览
        completed = sum(1 for r in self.results if r.status == "completed")
        failed = sum(1 for r in self.results if r.status == "failed")
        lines.append(f"状态: {completed} 完成, {failed} 失败")
        lines.append("")

        # 添加标注内容
        lines.append(format_marked_output(compressed))

        result_text = "\n".join(lines)

        # 如果还是超长，强制截断
        if len(result_text) > max_chars:
            result_text = result_text[:max_chars] + "\n...(已截断)"

        return result_text

    def get_compact_summary(self, max_chars: int = 500) -> str:
        """
        聚合为缩形态 (极简摘要，默认 500 字符)

        Args:
            max_chars: 最大字符数限制

        Returns:
            极简摘要
        """
        if not self.results:
            return "无任务结果"

        # 只保留 HIGH 重要性内容
        high_items = self.get_high_importance_only()

        # 压缩
        compressed = compress_by_importance(high_items, max_chars - 100)  # 留空间给状态信息

        # 极简格式
        lines = [
            f"{len(self.results)}个任务: ",
        ]

        for item in compressed:
            lines.append(f"- [{item.source}] {item.content}")

        result_text = "\n".join(lines)

        # 强制截断
        if len(result_text) > max_chars:
            result_text = result_text[:max_chars] + "..."

        return result_text

    def get_high_importance_only(self) -> List[MarkedContent]:
        """
        只获取高重要性内容

        Returns:
            HIGH 重要性的标注内容列表
        """
        high_items = []
        for result in self.results:
            high_items.extend([
                item for item in result.marked_items
                if item.importance == Importance.HIGH
            ])
        return high_items

    def clear(self) -> None:
        """清空所有结果"""
        self.results.clear()
