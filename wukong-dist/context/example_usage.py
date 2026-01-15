#!/usr/bin/env python3
"""
示例：如何使用 Wukong 上下文优化模块

运行:
  cd /path/to/wukong
  python3 -m wukong-dist.context.example_usage

或:
  cd /path/to/wukong/wukong-dist
  python3 -m context.example_usage
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import snapshot
import importance
import aggregator

# Aliases for convenience
create_snapshot = snapshot.create_snapshot
get_snapshot_for_task = snapshot.get_snapshot_for_task
Importance = importance.Importance
mark = importance.mark
compress_by_importance = importance.compress_by_importance
format_marked_output = importance.format_marked_output
TaskResult = aggregator.TaskResult
ResultAggregator = aggregator.ResultAggregator


def example_1_parallel_snapshot():
    """示例 1: 并行召唤时创建快照"""
    print("=" * 60)
    print("示例 1: 并行快照机制")
    print("=" * 60)

    # 创建快照
    snapshot = create_snapshot(
        session_id="session-abc123",
        compact_context="当前正在实现用户认证模块，需要支持 JWT 和 OAuth2 两种方式",
        anchors=[
            {"type": "D", "content": "使用 JWT 作为主要认证方式"},
            {"type": "C", "content": "必须支持 HTTPS"},
            {"type": "C", "content": "密码必须 bcrypt 加密存储"}
        ]
    )

    # 模拟并行任务
    task_ids = ["eye-task-1", "nose-task-1", "impl-task-1"]

    print(f"\n创建了快照: {snapshot.session_id}")
    print(f"时间戳: {snapshot.timestamp}")
    print(f"锚点数量: {len(snapshot.anchors)}\n")

    for task_id in task_ids:
        prompt = get_snapshot_for_task(snapshot, task_id)
        print(f"\n--- Task {task_id} 的 Prompt ---")
        print(prompt)
        print("-" * 60)


def example_2_importance_marking():
    """示例 2: 重要性标注和压缩"""
    print("\n" + "=" * 60)
    print("示例 2: 重要性标注系统")
    print("=" * 60)

    # 标注不同重要性的内容
    items = [
        mark("src/auth/login.py - 核心认证逻辑", Importance.HIGH, "file", "眼分身"),
        mark("src/utils/helper.py - 辅助函数", Importance.LOW, "file", "眼分身"),
        mark("发现 SQL 注入风险在 login 接口", Importance.HIGH, "issue", "鼻分身"),
        mark("建议添加日志记录", Importance.MEDIUM, "suggestion", "舌分身"),
        mark("发现过期依赖 jwt==1.0.0", Importance.HIGH, "issue", "鼻分身"),
        mark("代码格式可以优化", Importance.LOW, "info", "鼻分身"),
    ]

    print("\n原始内容:")
    for item in items:
        print(f"  [{item.importance.value}] {item.content}")

    # 压缩到 200 字符
    compressed = compress_by_importance(items, max_chars=200)

    print(f"\n压缩后 (max_chars=200):")
    for item in compressed:
        print(f"  [{item.importance.value}] {item.content}")

    # 格式化输出
    print("\n格式化输出:")
    print(format_marked_output(compressed))


def example_3_result_aggregation():
    """示例 3: 聚合多个后台分身结果"""
    print("\n" + "=" * 60)
    print("示例 3: 结果自动聚合")
    print("=" * 60)

    aggregator = ResultAggregator()

    # 添加眼分身的探索结果
    aggregator.add_result(TaskResult(
        task_id="eye-1",
        avatar="眼分身",
        status="completed",
        output="探索 src/auth/ 目录完成",
        marked_items=[
            mark("src/auth/login.py", Importance.HIGH, "file", "眼分身"),
            mark("src/auth/oauth.py", Importance.HIGH, "file", "眼分身"),
            mark("src/auth/jwt_util.py", Importance.MEDIUM, "file", "眼分身"),
            mark("src/auth/legacy.py", Importance.LOW, "file", "眼分身"),
        ]
    ))

    # 添加鼻分身的审查结果
    aggregator.add_result(TaskResult(
        task_id="nose-1",
        avatar="鼻分身",
        status="completed",
        output="代码审查完成",
        marked_items=[
            mark("发现 SQL 注入风险", Importance.HIGH, "issue", "鼻分身"),
            mark("发现硬编码密钥", Importance.HIGH, "issue", "鼻分身"),
            mark("建议添加单元测试", Importance.MEDIUM, "suggestion", "鼻分身"),
        ]
    ))

    # 添加舌分身的测试结果
    aggregator.add_result(TaskResult(
        task_id="tongue-1",
        avatar="舌分身",
        status="completed",
        output="测试完成",
        marked_items=[
            mark("3 个测试失败", Importance.HIGH, "issue", "舌分身"),
            mark("测试覆盖率 65%", Importance.MEDIUM, "info", "舌分身"),
        ]
    ))

    print("\n=== 常形态聚合 (max_chars=2000) ===")
    print(aggregator.aggregate(max_chars=2000))

    print("\n=== 缩形态聚合 (max_chars=500) ===")
    print(aggregator.get_compact_summary(max_chars=500))

    print("\n=== 只看高优先级 ===")
    high_only = aggregator.get_high_importance_only()
    for item in high_only:
        print(f"  [{item.source}] {item.content}")


def main():
    """运行所有示例"""
    print("\nWukong 上下文优化模块使用示例\n")

    example_1_parallel_snapshot()
    example_2_importance_marking()
    example_3_result_aggregation()

    print("\n" + "=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
