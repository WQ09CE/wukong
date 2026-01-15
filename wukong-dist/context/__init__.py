"""
Wukong Context Optimization Modules

提供三个核心模块:
1. snapshot - 并行快照机制
2. importance - 重要性标注系统
3. aggregator - 结果自动聚合
"""

from .snapshot import ContextSnapshot, create_snapshot, get_snapshot_for_task
from .importance import Importance, MarkedContent, mark, compress_by_importance, format_marked_output
from .aggregator import TaskResult, ResultAggregator

__all__ = [
    # snapshot
    'ContextSnapshot',
    'create_snapshot',
    'get_snapshot_for_task',
    # importance
    'Importance',
    'MarkedContent',
    'mark',
    'compress_by_importance',
    'format_marked_output',
    # aggregator
    'TaskResult',
    'ResultAggregator',
]
