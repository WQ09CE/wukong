"""
测试上下文优化模块

运行: python -m pytest tests/test_context.py -v
"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

# 添加 context 模块目录到路径
tests_dir = Path(__file__).parent.resolve()
project_root = tests_dir.parent
context_dir = project_root / 'wukong-dist' / 'context'
if str(context_dir) not in sys.path:
    sys.path.insert(0, str(context_dir))

from snapshot import ContextSnapshot, Anchor, create_snapshot, get_snapshot_for_task
from importance import Importance, MarkedContent, mark, compress_by_importance, format_marked_output
from aggregator import TaskResult, ResultAggregator


class TestSnapshot(unittest.TestCase):
    """测试并行快照机制"""

    def test_create_snapshot(self):
        """测试创建快照"""
        snapshot = create_snapshot(
            session_id="test123",
            compact_context="正在实现用户认证模块",
            anchors=[
                {"type": "D", "content": "使用 JWT 认证"},
                {"type": "C", "content": "必须支持 HTTPS"}
            ]
        )

        self.assertEqual(snapshot.session_id, "test123")
        self.assertEqual(snapshot.compact_context, "正在实现用户认证模块")
        self.assertEqual(len(snapshot.anchors), 2)
        self.assertEqual(snapshot.anchors[0].anchor_type, "D")
        self.assertEqual(snapshot.anchors[0].content, "使用 JWT 认证")
        self.assertIsInstance(snapshot.timestamp, datetime)

    def test_snapshot_immutable(self):
        """测试快照不可变性"""
        snapshot = create_snapshot(
            session_id="test123",
            compact_context="测试",
            anchors=[]
        )

        with self.assertRaises(Exception):  # dataclass frozen=True 会抛出异常
            snapshot.session_id = "modified"  # type: ignore

    def test_get_snapshot_for_task(self):
        """测试格式化快照为 prompt"""
        snapshot = create_snapshot(
            session_id="test123",
            compact_context="正在实现用户认证模块",
            anchors=[
                {"type": "D", "content": "使用 JWT 认证"},
            ]
        )

        prompt = get_snapshot_for_task(snapshot, "task-001")

        self.assertIn("test123", prompt)
        self.assertIn("task-001", prompt)
        self.assertIn("正在实现用户认证模块", prompt)
        self.assertIn("[D] 使用 JWT 认证", prompt)

    def test_empty_anchors(self):
        """测试空锚点"""
        snapshot = create_snapshot(
            session_id="test123",
            compact_context="测试",
            anchors=[]
        )

        self.assertEqual(len(snapshot.anchors), 0)
        prompt = get_snapshot_for_task(snapshot, "task-001")
        self.assertNotIn("相关锚点", prompt)


class TestImportance(unittest.TestCase):
    """测试重要性标注系统"""

    def test_mark(self):
        """测试标注内容"""
        content = mark(
            content="src/auth/login.py",
            importance=Importance.HIGH,
            category="file",
            source="眼分身"
        )

        self.assertEqual(content.content, "src/auth/login.py")
        self.assertEqual(content.importance, Importance.HIGH)
        self.assertEqual(content.category, "file")
        self.assertEqual(content.source, "眼分身")

    def test_compress_by_importance(self):
        """测试按重要性压缩"""
        items = [
            mark("LOW1", Importance.LOW, "info", "眼分身"),        # 4 chars
            mark("HIGH1", Importance.HIGH, "issue", "鼻分身"),     # 5 chars
            mark("MED1", Importance.MEDIUM, "file", "眼分身"),     # 4 chars
            mark("HIGH2", Importance.HIGH, "decision", "意分身"),  # 5 chars
        ]

        # 最大 15 字符，应该优先保留 HIGH (两个 HIGH = 10 chars)
        compressed = compress_by_importance(items, max_chars=15)

        # 应该包含两个 HIGH 级别的内容，可能还有一个 MEDIUM (14 chars)
        self.assertGreater(len(compressed), 0)
        # 检查 HIGH 优先
        high_count = sum(1 for item in compressed if item.importance == Importance.HIGH)
        self.assertEqual(high_count, 2)  # 两个 HIGH 都应该在

    def test_compress_exact_fit(self):
        """测试恰好符合大小限制"""
        items = [
            mark("12345", Importance.HIGH, "test", "test"),  # 5 chars
            mark("67890", Importance.MEDIUM, "test", "test"),  # 5 chars
        ]

        compressed = compress_by_importance(items, max_chars=10)
        self.assertEqual(len(compressed), 2)

    def test_format_marked_output(self):
        """测试格式化输出"""
        items = [
            mark("高优先级问题", Importance.HIGH, "issue", "鼻分身"),
            mark("相关文件", Importance.MEDIUM, "file", "眼分身"),
            mark("辅助信息", Importance.LOW, "info", "舌分身"),
        ]

        output = format_marked_output(items)

        self.assertIn("高优先级 (HIGH)", output)
        self.assertIn("中优先级 (MEDIUM)", output)
        self.assertIn("低优先级 (LOW)", output)
        self.assertIn("高优先级问题", output)
        self.assertIn("相关文件", output)
        self.assertIn("辅助信息", output)

    def test_format_empty(self):
        """测试格式化空列表"""
        output = format_marked_output([])
        self.assertEqual(output, "")


class TestAggregator(unittest.TestCase):
    """测试结果聚合器"""

    def test_add_result(self):
        """测试添加结果"""
        aggregator = ResultAggregator()

        result = TaskResult(
            task_id="task1",
            avatar="眼分身",
            status="completed",
            output="探索完成",
            marked_items=[
                mark("发现文件A", Importance.HIGH, "file", "眼分身")
            ]
        )

        aggregator.add_result(result)
        self.assertEqual(len(aggregator.results), 1)

    def test_aggregate(self):
        """测试聚合为常形态"""
        aggregator = ResultAggregator()

        aggregator.add_result(TaskResult(
            task_id="task1",
            avatar="眼分身",
            status="completed",
            output="探索完成",
            marked_items=[
                mark("发现文件A", Importance.HIGH, "file", "眼分身"),
                mark("发现文件B", Importance.MEDIUM, "file", "眼分身"),
            ]
        ))

        aggregator.add_result(TaskResult(
            task_id="task2",
            avatar="鼻分身",
            status="completed",
            output="审查完成",
            marked_items=[
                mark("发现安全问题", Importance.HIGH, "issue", "鼻分身"),
            ]
        ))

        summary = aggregator.aggregate(max_chars=2000)

        self.assertIn("2 个任务", summary)
        self.assertIn("2 完成", summary)
        self.assertIn("发现文件A", summary)
        self.assertIn("发现安全问题", summary)

    def test_get_compact_summary(self):
        """测试聚合为缩形态"""
        aggregator = ResultAggregator()

        aggregator.add_result(TaskResult(
            task_id="task1",
            avatar="眼分身",
            status="completed",
            output="探索完成",
            marked_items=[
                mark("发现文件A", Importance.HIGH, "file", "眼分身"),
                mark("发现文件B", Importance.LOW, "file", "眼分身"),  # 应该被过滤
            ]
        ))

        summary = aggregator.get_compact_summary(max_chars=500)

        self.assertIn("1个任务", summary)
        self.assertIn("发现文件A", summary)
        self.assertNotIn("发现文件B", summary)  # LOW 应该被过滤

    def test_get_high_importance_only(self):
        """测试只获取高重要性内容"""
        aggregator = ResultAggregator()

        aggregator.add_result(TaskResult(
            task_id="task1",
            avatar="眼分身",
            status="completed",
            output="测试",
            marked_items=[
                mark("高1", Importance.HIGH, "test", "test"),
                mark("中1", Importance.MEDIUM, "test", "test"),
                mark("高2", Importance.HIGH, "test", "test"),
                mark("低1", Importance.LOW, "test", "test"),
            ]
        ))

        high_only = aggregator.get_high_importance_only()

        self.assertEqual(len(high_only), 2)
        self.assertTrue(all(item.importance == Importance.HIGH for item in high_only))

    def test_clear(self):
        """测试清空结果"""
        aggregator = ResultAggregator()

        aggregator.add_result(TaskResult(
            task_id="task1",
            avatar="眼分身",
            status="completed",
            output="测试",
            marked_items=[]
        ))

        self.assertEqual(len(aggregator.results), 1)

        aggregator.clear()
        self.assertEqual(len(aggregator.results), 0)

    def test_empty_aggregator(self):
        """测试空聚合器"""
        aggregator = ResultAggregator()

        self.assertEqual(aggregator.aggregate(), "无任务结果")
        self.assertEqual(aggregator.get_compact_summary(), "无任务结果")


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建快照
        snapshot = create_snapshot(
            session_id="session123",
            compact_context="正在重构认证模块",
            anchors=[
                {"type": "D", "content": "使用 OAuth2"},
                {"type": "C", "content": "保持向后兼容"}
            ]
        )

        # 2. 模拟多个并行任务
        task_ids = ["task1", "task2", "task3"]
        for task_id in task_ids:
            prompt = get_snapshot_for_task(snapshot, task_id)
            self.assertIn(snapshot.session_id, prompt)
            self.assertIn(task_id, prompt)

        # 3. 收集结果
        aggregator = ResultAggregator()

        aggregator.add_result(TaskResult(
            task_id="task1",
            avatar="眼分身",
            status="completed",
            output="探索完成",
            marked_items=[
                mark("src/auth/oauth.py", Importance.HIGH, "file", "眼分身"),
                mark("src/auth/legacy.py", Importance.MEDIUM, "file", "眼分身"),
            ]
        ))

        aggregator.add_result(TaskResult(
            task_id="task2",
            avatar="鼻分身",
            status="completed",
            output="审查完成",
            marked_items=[
                mark("发现过期依赖", Importance.HIGH, "issue", "鼻分身"),
            ]
        ))

        # 4. 聚合结果
        summary = aggregator.aggregate(max_chars=2000)
        compact = aggregator.get_compact_summary(max_chars=500)

        self.assertIn("2 个任务", summary)
        self.assertIn("src/auth/oauth.py", summary)
        self.assertIn("发现过期依赖", compact)


if __name__ == '__main__':
    unittest.main()
