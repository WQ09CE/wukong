# Wukong Context Optimization Modules

三个核心模块用于优化 Wukong 多分身并行上下文管理。

## 模块概览

### 1. snapshot.py - 并行快照机制

提供不可变的上下文快照，用于并行分身召唤时传递一致的上下文。

**核心类**:
- `ContextSnapshot`: 不可变的上下文快照（使用 `@dataclass(frozen=True)`）
- `Anchor`: 锚点数据（P/C/M/D/I）

**核心函数**:
- `create_snapshot()`: 创建上下文快照
- `get_snapshot_for_task()`: 格式化快照为 prompt 片段

**使用场景**: 本体召唤多个并行分身时，每个分身获得相同的上下文快照。

### 2. importance.py - 重要性标注系统

为分身输出内容标注重要性级别，用于智能压缩和优先级排序。

**重要性级别**:
- `HIGH`: 必须保留（关键文件、严重问题、核心决策）
- `MEDIUM`: 优先保留（相关文件、一般问题、辅助信息）
- `LOW`: 可丢弃（辅助文件、细节信息、冗余内容）

**核心类**:
- `Importance`: 重要性枚举
- `MarkedContent`: 带重要性标记的内容

**核心函数**:
- `mark()`: 标注内容的重要性
- `compress_by_importance()`: 按重要性压缩内容（优先保留 HIGH）
- `format_marked_output()`: 格式化输出（按重要性分组）

**使用场景**: 分身输出时标注重要性，本体聚合时智能压缩。

### 3. aggregator.py - 结果自动聚合

聚合多个后台分身的输出结果，自动压缩为常形态或缩形态。

**核心类**:
- `TaskResult`: 后台任务结果
- `ResultAggregator`: 结果聚合器

**核心方法**:
- `add_result()`: 添加任务结果
- `aggregate()`: 聚合为常形态（默认 2000 字符）
- `get_compact_summary()`: 聚合为缩形态（默认 500 字符）
- `get_high_importance_only()`: 只获取高重要性内容

**使用场景**: 本体等待多个后台分身完成后，聚合结果并压缩。

## 安装

无需安装外部依赖，只使用 Python 标准库。

**兼容性**: Python 3.9+

## 使用示例

### 示例 1: 并行快照

```python
from context import create_snapshot, get_snapshot_for_task

# 创建快照
snapshot = create_snapshot(
    session_id="session-abc123",
    compact_context="当前正在实现用户认证模块",
    anchors=[
        {"type": "D", "content": "使用 JWT 认证"},
        {"type": "C", "content": "必须支持 HTTPS"}
    ]
)

# 每个并行分身获得相同的快照
for task_id in ["task1", "task2", "task3"]:
    prompt = get_snapshot_for_task(snapshot, task_id)
    # 传递给分身...
```

### 示例 2: 重要性标注

```python
from context import mark, Importance, compress_by_importance

# 标注内容
items = [
    mark("src/auth/login.py", Importance.HIGH, "file", "眼分身"),
    mark("src/utils/helper.py", Importance.LOW, "file", "眼分身"),
    mark("发现 SQL 注入风险", Importance.HIGH, "issue", "鼻分身"),
]

# 压缩到 500 字符（优先保留 HIGH）
compressed = compress_by_importance(items, max_chars=500)
```

### 示例 3: 结果聚合

```python
from context import ResultAggregator, TaskResult, mark, Importance

aggregator = ResultAggregator()

# 添加眼分身结果
aggregator.add_result(TaskResult(
    task_id="eye-1",
    avatar="眼分身",
    status="completed",
    output="探索完成",
    marked_items=[
        mark("src/auth/login.py", Importance.HIGH, "file", "眼分身")
    ]
))

# 添加鼻分身结果
aggregator.add_result(TaskResult(
    task_id="nose-1",
    avatar="鼻分身",
    status="completed",
    output="审查完成",
    marked_items=[
        mark("发现安全问题", Importance.HIGH, "issue", "鼻分身")
    ]
))

# 聚合结果
summary = aggregator.aggregate(max_chars=2000)  # 常形态
compact = aggregator.get_compact_summary(max_chars=500)  # 缩形态
high_only = aggregator.get_high_importance_only()  # 只看 HIGH
```

## 运行示例

```bash
# 完整示例
cd /path/to/wukong/wukong-dist
python3 -m context.example_usage

# 或者
cd /path/to/wukong/wukong-dist/context
python3 example_usage.py
```

## 运行测试

```bash
# 运行所有测试
python3 -m unittest wukong-dist.context.test_context -v

# 或者
cd wukong-dist/context
python3 -m unittest test_context -v
```

## 架构决策

### 为什么使用不可变快照？

- 保证并行分身获得一致的上下文
- 避免并发修改导致的竞态条件
- 使用 `@dataclass(frozen=True)` 强制不可变性

### 为什么三级重要性？

- `HIGH`: 核心信息，必须保留
- `MEDIUM`: 辅助信息，优先保留
- `LOW`: 冗余信息，可丢弃

三级平衡了灵活性和简洁性。

### 为什么常形态 2000 字符，缩形态 500 字符？

- **常形态 (2000)**: 保留足够细节，用于本体理解完整上下文
- **缩形态 (500)**: 极简摘要，用于 PreCompact Hook 或快速回顾

### 为什么压缩算法是贪婪选择？

- 简单高效（O(n log n) 排序 + O(n) 选择）
- 保证 HIGH 优先（即使截断也尽量保留）
- 避免复杂的动态规划算法

## 文件结构

```
wukong-dist/context/
├── __init__.py           # 模块导出
├── snapshot.py           # 并行快照机制
├── importance.py         # 重要性标注系统
├── aggregator.py         # 结果自动聚合
├── test_context.py       # 单元测试
├── example_usage.py      # 使用示例
└── README.md             # 本文档
```

## 技术细节

### 兼容性

- **Python 版本**: 3.9+
- **不使用 3.10+ 语法**:
  - 不使用 `match` 语句
  - 不使用 `|` 类型联合（使用 `Union` 或 `Optional`）
- **依赖**: 仅标准库

### 类型注解

所有公共 API 都有完整的类型注解，支持类型检查工具（mypy, pyright）。

### 测试覆盖

- 16 个测试用例
- 覆盖所有核心功能
- 包括边界条件和集成测试

## 未来扩展

可能的扩展方向：

1. **持久化快照**: 将快照保存到磁盘，支持跨会话恢复
2. **更多压缩策略**: LCS、语义相似度、关键词提取
3. **自动重要性推断**: 使用 ML 模型自动标注重要性
4. **流式聚合**: 支持分身结果流式到达时的增量聚合

## 许可证

MIT License
