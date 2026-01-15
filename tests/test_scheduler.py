#!/usr/bin/env python3
"""
Wukong Scheduler Tests

测试调度器的核心功能:
- 任务创建和状态管理
- 并发控制
- 领地冲突检测
- 依赖关系处理
- 轨道检测和规划
- TodoWrite 集成
"""

import unittest
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加 scheduler 目录到路径 (测试文件现在在 tests/ 目录)
tests_dir = Path(__file__).parent
project_root = tests_dir.parent
scheduler_dir = project_root / 'wukong-dist' / 'scheduler'
sys.path.insert(0, str(scheduler_dir))

from scheduler import (
    WukongScheduler,
    AvatarType,
    CostTier,
    TaskStatus,
    TrackType,
    Territory,
    ScheduledTask,
    AVATAR_CONFIG,
    parse_territory_declaration,
    generate_task_prompt,
)
from todo_integration import (
    TodoWriteIntegration,
    generate_summoning_declaration,
    generate_task_invocation,
)


class TestBasicScheduling(unittest.TestCase):
    """测试基本调度功能"""

    def test_create_task(self):
        scheduler = WukongScheduler()
        task = scheduler.add_task(
            avatar=AvatarType.EYE,
            description="探索代码库",
            prompt="## TASK\n探索并分析代码结构"
        )
        self.assertEqual(task.task_id, "眼_001")
        self.assertEqual(task.avatar, AvatarType.EYE)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(len(scheduler.tasks), 1)

    def test_task_id_increment(self):
        scheduler = WukongScheduler()
        task1 = scheduler.add_task(AvatarType.EYE, "Task 1", "Prompt 1")
        task2 = scheduler.add_task(AvatarType.BODY, "Task 2", "Prompt 2")
        task3 = scheduler.add_task(AvatarType.EYE, "Task 3", "Prompt 3")

        self.assertEqual(task1.task_id, "眼_001")
        self.assertEqual(task2.task_id, "身_002")
        self.assertEqual(task3.task_id, "眼_003")

    def test_start_task(self):
        scheduler = WukongScheduler()
        task = scheduler.add_task(AvatarType.EYE, "Task", "Prompt")

        success = scheduler.start_task(task.task_id)
        self.assertTrue(success)
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(task.started_at)
        self.assertEqual(len(scheduler.active_by_tier[CostTier.CHEAP]), 1)

    def test_complete_task(self):
        scheduler = WukongScheduler()
        task = scheduler.add_task(AvatarType.EYE, "Task", "Prompt")
        scheduler.start_task(task.task_id)

        scheduler.complete_task(task.task_id, result="Done", success=True)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.result, "Done")
        self.assertEqual(len(scheduler.active_by_tier[CostTier.CHEAP]), 0)


class TestConcurrencyControl(unittest.TestCase):
    """测试并发控制"""

    def test_cheap_concurrent_limit(self):
        scheduler = WukongScheduler()
        tasks = []

        # 创建 12 个 CHEAP 任务（眼分身 max=10）
        for i in range(12):
            task = scheduler.add_task(AvatarType.EYE, f"Task {i}", f"Prompt {i}")
            tasks.append(task)

        # 启动前 10 个应该成功
        for i in range(10):
            self.assertTrue(scheduler.start_task(tasks[i].task_id))

        # 第 11 个应该被阻塞
        self.assertFalse(scheduler.start_task(tasks[10].task_id))
        self.assertEqual(tasks[10].status, TaskStatus.BLOCKED)

        # 完成一个任务后，第 11 个应该可以启动
        scheduler.complete_task(tasks[0].task_id)
        self.assertTrue(scheduler.start_task(tasks[10].task_id))

    def test_expensive_concurrent_limit(self):
        scheduler = WukongScheduler()

        task1 = scheduler.add_task(AvatarType.BODY, "Task 1", "Prompt 1")
        task2 = scheduler.add_task(AvatarType.BODY, "Task 2", "Prompt 2")

        # 第一个应该成功
        self.assertTrue(scheduler.start_task(task1.task_id))

        # 第二个应该被阻塞（EXPENSIVE max=1）
        self.assertFalse(scheduler.start_task(task2.task_id))
        self.assertEqual(task2.status, TaskStatus.BLOCKED)

        # 完成第一个后，第二个可以启动
        scheduler.complete_task(task1.task_id)
        self.assertTrue(scheduler.start_task(task2.task_id))

    def test_mixed_tier_concurrency(self):
        scheduler = WukongScheduler()

        # 创建不同层级的任务
        cheap_task = scheduler.add_task(AvatarType.EYE, "Cheap", "Prompt")
        medium_task = scheduler.add_task(AvatarType.TONGUE, "Medium", "Prompt")
        expensive_task = scheduler.add_task(AvatarType.BODY, "Expensive", "Prompt")

        # 所有任务都应该能并发启动
        self.assertTrue(scheduler.start_task(cheap_task.task_id))
        self.assertTrue(scheduler.start_task(medium_task.task_id))
        self.assertTrue(scheduler.start_task(expensive_task.task_id))

        self.assertEqual(len(scheduler.active_by_tier[CostTier.CHEAP]), 1)
        self.assertEqual(len(scheduler.active_by_tier[CostTier.MEDIUM]), 1)
        self.assertEqual(len(scheduler.active_by_tier[CostTier.EXPENSIVE]), 1)


class TestTerritoryConflict(unittest.TestCase):
    """测试领地冲突检测"""

    def test_file_level_conflict(self):
        scheduler = WukongScheduler()

        territory1 = Territory(file_path="main.py", owner="眼_001", granularity="file")
        territory2 = Territory(file_path="main.py", owner="身_002", granularity="file")

        task1 = scheduler.add_task(AvatarType.EYE, "Task 1", "Prompt", territories=[territory1])
        task2 = scheduler.add_task(AvatarType.BODY, "Task 2", "Prompt", territories=[territory2])

        # 第一个任务启动成功
        self.assertTrue(scheduler.start_task(task1.task_id))

        # 第二个任务因为领地冲突被阻塞
        can_start, reason = scheduler.can_start(task2)
        self.assertFalse(can_start)
        self.assertIn("conflict", reason.lower())

    def test_function_level_no_conflict(self):
        scheduler = WukongScheduler()

        territory1 = Territory(
            file_path="utils.py", owner="眼_001",
            granularity="function", function_name="func1"
        )
        territory2 = Territory(
            file_path="utils.py", owner="身_002",
            granularity="function", function_name="func2"
        )

        task1 = scheduler.add_task(AvatarType.EYE, "Task 1", "Prompt", territories=[territory1])
        task2 = scheduler.add_task(AvatarType.BODY, "Task 2", "Prompt", territories=[territory2])

        # 两个任务都应该能启动（不同函数）
        self.assertTrue(scheduler.start_task(task1.task_id))
        can_start, _ = scheduler.can_start(task2)
        self.assertTrue(can_start)

    def test_function_level_conflict(self):
        scheduler = WukongScheduler()

        territory1 = Territory(
            file_path="utils.py", owner="眼_001",
            granularity="function", function_name="process"
        )
        territory2 = Territory(
            file_path="utils.py", owner="身_002",
            granularity="function", function_name="process"
        )

        task1 = scheduler.add_task(AvatarType.EYE, "Task 1", "Prompt", territories=[territory1])
        task2 = scheduler.add_task(AvatarType.BODY, "Task 2", "Prompt", territories=[territory2])

        self.assertTrue(scheduler.start_task(task1.task_id))
        can_start, reason = scheduler.can_start(task2)
        self.assertFalse(can_start)
        self.assertIn("conflict", reason.lower())

    def test_territory_release(self):
        scheduler = WukongScheduler()

        territory = Territory(file_path="main.py", owner="眼_001", granularity="file")
        task1 = scheduler.add_task(AvatarType.EYE, "Task 1", "Prompt", territories=[territory])
        task2 = scheduler.add_task(AvatarType.BODY, "Task 2", "Prompt",
                                  territories=[Territory(file_path="main.py", owner="身_002")])

        scheduler.start_task(task1.task_id)
        self.assertFalse(scheduler.can_start(task2)[0])

        # 完成任务后领地应该释放
        scheduler.complete_task(task1.task_id)
        self.assertTrue(scheduler.can_start(task2)[0])


class TestDependencies(unittest.TestCase):
    """测试依赖关系"""

    def test_basic_dependency(self):
        scheduler = WukongScheduler()

        task1 = scheduler.add_task(AvatarType.EYE, "Explore", "Prompt")
        task2 = scheduler.add_task(AvatarType.BODY, "Implement", "Prompt",
                                  depends_on=[task1.task_id])

        # task2 依赖 task1，不能直接启动
        can_start, reason = scheduler.can_start(task2)
        self.assertFalse(can_start)
        self.assertIn("dependency", reason.lower())

        # task1 完成后，task2 可以启动
        scheduler.start_task(task1.task_id)
        scheduler.complete_task(task1.task_id)

        can_start, _ = scheduler.can_start(task2)
        self.assertTrue(can_start)

    def test_multiple_dependencies(self):
        scheduler = WukongScheduler()

        task1 = scheduler.add_task(AvatarType.EYE, "Explore", "Prompt")
        task2 = scheduler.add_task(AvatarType.MIND, "Design", "Prompt")
        task3 = scheduler.add_task(AvatarType.BODY, "Implement", "Prompt",
                                  depends_on=[task1.task_id, task2.task_id])

        # 只完成一个依赖，不够
        scheduler.start_task(task1.task_id)
        scheduler.complete_task(task1.task_id)
        self.assertFalse(scheduler.can_start(task3)[0])

        # 完成所有依赖后才能启动
        scheduler.start_task(task2.task_id)
        scheduler.complete_task(task2.task_id)
        self.assertTrue(scheduler.can_start(task3)[0])


class TestTrackDetection(unittest.TestCase):
    """测试轨道检测"""

    def test_detect_feature_track(self):
        self.assertEqual(WukongScheduler.detect_track("Add user login feature"), TrackType.FEATURE)
        self.assertEqual(WukongScheduler.detect_track("Create new API endpoint"), TrackType.FEATURE)
        self.assertEqual(WukongScheduler.detect_track("实现新功能"), TrackType.FEATURE)

    def test_detect_fix_track(self):
        self.assertEqual(WukongScheduler.detect_track("Fix login bug"), TrackType.FIX)
        self.assertEqual(WukongScheduler.detect_track("Resolve crash issue"), TrackType.FIX)
        self.assertEqual(WukongScheduler.detect_track("修复错误"), TrackType.FIX)

    def test_detect_refactor_track(self):
        self.assertEqual(WukongScheduler.detect_track("Refactor database layer"), TrackType.REFACTOR)
        self.assertEqual(WukongScheduler.detect_track("Clean up code"), TrackType.REFACTOR)
        self.assertEqual(WukongScheduler.detect_track("重构模块"), TrackType.REFACTOR)

    def test_detect_direct_track(self):
        self.assertEqual(WukongScheduler.detect_track("Update documentation"), TrackType.DIRECT)
        self.assertEqual(WukongScheduler.detect_track("Run tests"), TrackType.DIRECT)


class TestTrackPlanning(unittest.TestCase):
    """测试轨道规划"""

    def test_feature_track_dag(self):
        scheduler = WukongScheduler()
        phases = scheduler.plan_track(TrackType.FEATURE, "Add login feature")

        # Feature track: 耳+眼 -> 意 -> 身 -> 舌+鼻
        self.assertEqual(len(phases), 4)
        self.assertEqual(len(phases[0]), 2)  # 耳+眼
        self.assertEqual(len(phases[1]), 1)  # 意
        self.assertEqual(len(phases[2]), 1)  # 身
        self.assertEqual(len(phases[3]), 2)  # 舌+鼻

        # 检查依赖关系
        phase2_task = phases[1][0]
        self.assertEqual(len(phase2_task.depends_on), 2)  # 依赖 phase 1 的两个任务

    def test_fix_track_dag(self):
        scheduler = WukongScheduler()
        phases = scheduler.plan_track(TrackType.FIX, "Fix authentication bug")

        # Fix track: 眼+鼻 -> 身 -> 舌
        self.assertEqual(len(phases), 3)
        self.assertEqual(len(phases[0]), 2)  # 眼+鼻
        self.assertEqual(len(phases[1]), 1)  # 身
        self.assertEqual(len(phases[2]), 1)  # 舌


class TestScheduleNextBatch(unittest.TestCase):
    """测试批量调度"""

    def test_schedule_next_batch_priority(self):
        scheduler = WukongScheduler()

        # 创建不同层级的任务
        cheap1 = scheduler.add_task(AvatarType.EYE, "Cheap 1", "Prompt")
        cheap2 = scheduler.add_task(AvatarType.EYE, "Cheap 2", "Prompt")
        medium = scheduler.add_task(AvatarType.TONGUE, "Medium", "Prompt")
        expensive = scheduler.add_task(AvatarType.BODY, "Expensive", "Prompt")

        batch = scheduler.schedule_next_batch()

        # 应该返回所有就绪的任务
        self.assertEqual(len(batch), 4)
        self.assertIn(cheap1, batch)
        self.assertIn(expensive, batch)


class TestTerritoryParsing(unittest.TestCase):
    """测试领地声明解析"""

    def test_parse_file_territory(self):
        declaration = """
- main.py
- utils.py (全文件)
"""
        territories = parse_territory_declaration(declaration)
        self.assertEqual(len(territories), 2)
        self.assertEqual(territories[0].file_path, "main.py")
        self.assertEqual(territories[0].granularity, "file")
        self.assertEqual(territories[1].file_path, "utils.py")

    def test_parse_function_territory(self):
        declaration = "- utils.py (函数: process_data)"
        territories = parse_territory_declaration(declaration)
        self.assertEqual(len(territories), 1)
        self.assertEqual(territories[0].granularity, "function")
        self.assertEqual(territories[0].function_name, "process_data")


class TestTodoIntegration(unittest.TestCase):
    """测试 TodoWrite 集成"""

    def test_generate_todo_call(self):
        scheduler = WukongScheduler()
        integration = TodoWriteIntegration(scheduler)

        task1 = scheduler.add_task(AvatarType.EYE, "探索代码", "Prompt")
        task2 = scheduler.add_task(AvatarType.BODY, "实现功能", "Prompt")
        scheduler.start_task(task1.task_id)

        todo_call = integration.generate_todo_call()
        todos = todo_call["todos"]

        self.assertEqual(len(todos), 2)
        self.assertEqual(todos[0]["status"], "in_progress")
        self.assertEqual(todos[1]["status"], "pending")
        self.assertIn("眼", todos[0]["content"])
        self.assertIn("身", todos[1]["content"])

    def test_generate_summoning_declaration(self):
        scheduler = WukongScheduler()
        task = scheduler.add_task(AvatarType.BODY, "实现功能", "Prompt")

        declaration = generate_summoning_declaration(task)
        self.assertIn("身", declaration)
        self.assertIn("opus", declaration)
        self.assertIn("expensive", declaration)

    def test_generate_task_invocation(self):
        scheduler = WukongScheduler()
        task = scheduler.add_task(AvatarType.EYE, "探索", "Test Prompt")

        invocation = generate_task_invocation(task)
        self.assertIn("Task(", invocation)
        self.assertIn("sonnet", invocation)  # EYE avatar now uses sonnet
        self.assertIn("run_in_background=True", invocation)  # 眼分身必须后台


class TestExecutionMode(unittest.TestCase):
    """测试执行模式配置"""

    def test_eye_avatar_background_required(self):
        scheduler = WukongScheduler()
        mode = scheduler.get_execution_mode(AvatarType.EYE)

        self.assertEqual(mode["model"], "sonnet")  # EYE avatar now uses sonnet
        self.assertTrue(mode["run_in_background"])
        self.assertTrue(mode["background_required"])
        self.assertFalse(mode["background_forbidden"])

    def test_body_avatar_background_forbidden(self):
        scheduler = WukongScheduler()
        mode = scheduler.get_execution_mode(AvatarType.BODY)

        self.assertEqual(mode["model"], "opus")
        self.assertTrue(mode["background_forbidden"])

    def test_mind_avatar_opus_model(self):
        scheduler = WukongScheduler()
        mode = scheduler.get_execution_mode(AvatarType.MIND)

        self.assertEqual(mode["model"], "opus")
        self.assertTrue(mode["background_forbidden"])


class TestTaskPromptGeneration(unittest.TestCase):
    """测试任务 Prompt 生成"""

    def test_generate_basic_prompt(self):
        prompt = generate_task_prompt(
            avatar=AvatarType.EYE,
            task="探索代码库",
            expected_outcome="找到所有相关文件",
            context="项目是 Python Web 应用",
            must_do=["扫描所有 .py 文件", "记录文件结构"],
            must_not=["修改任何文件"]
        )

        self.assertIn("## 1. TASK", prompt)
        self.assertIn("探索代码库", prompt)
        self.assertIn("## 5. MUST DO", prompt)
        self.assertIn("扫描所有 .py 文件", prompt)
        self.assertIn("model=sonnet", prompt)  # EYE avatar now uses sonnet

    def test_generate_mind_avatar_prompt(self):
        prompt = generate_task_prompt(
            avatar=AvatarType.MIND,
            task="设计架构",
            expected_outcome="完整的架构方案",
            context="微服务系统",
            must_do=["考虑扩展性"],
            must_not=["过度设计"]
        )

        self.assertIn("ultrathink", prompt)
        self.assertIn("model=opus", prompt)


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
