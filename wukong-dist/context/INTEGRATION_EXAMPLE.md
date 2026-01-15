# Wukong 调度器集成示例

本文档展示如何将上下文优化模块集成到 Wukong 调度器中。

## 集成点 1: 本体召唤并行分身

在本体召唤多个分身时，使用快照机制传递一致的上下文。

```python
# 在 wukong 本体中
from context import create_snapshot, get_snapshot_for_task

def summon_parallel_avatars(task_descriptions, compact_context, anchors):
    """
    并行召唤多个分身

    Args:
        task_descriptions: List[Dict] - 任务描述列表
        compact_context: str - 缩形态上下文 (<500字)
        anchors: List[Dict] - 锚点列表
    """
    # 1. 创建快照
    snapshot = create_snapshot(
        session_id=get_current_session_id(),
        compact_context=compact_context,
        anchors=anchors
    )

    # 2. 并行召唤分身
    tasks = []
    for task_desc in task_descriptions:
        # 为每个任务获取相同的快照
        snapshot_prompt = get_snapshot_for_task(snapshot, task_desc['id'])

        # 构建完整 prompt
        full_prompt = f"""
{snapshot_prompt}

## 你的任务
{task_desc['description']}

## 预期输出
{task_desc['expected']}
"""

        # 召唤分身（后台）
        task = Task(
            prompt=full_prompt,
            model=task_desc['model'],
            run_in_background=True
        )
        tasks.append((task_desc['id'], task))

    return tasks
```

### 使用示例

```python
# 用户任务: "探索 src/auth/ 目录并审查代码"

# 1. 准备上下文
compact_context = "正在重构用户认证模块，需要支持 JWT 和 OAuth2"
anchors = [
    {"type": "D", "content": "使用 JWT 作为主要认证方式"},
    {"type": "C", "content": "必须保持向后兼容性"},
    {"type": "C", "content": "禁止硬编码密钥"}
]

# 2. 定义并行任务
task_descriptions = [
    {
        'id': 'eye-1',
        'description': '探索 src/auth/ 目录，列出所有文件',
        'expected': '文件列表，按重要性标注',
        'model': 'haiku'
    },
    {
        'id': 'nose-1',
        'description': '审查 src/auth/ 代码，发现安全问题',
        'expected': '安全问题列表，按严重性标注',
        'model': 'haiku'
    }
]

# 3. 召唤并行分身
tasks = summon_parallel_avatars(task_descriptions, compact_context, anchors)
```

---

## 集成点 2: 分身输出时标注重要性

分身在输出时，自动标注内容的重要性级别。

```python
# 在分身的 skill 文件中添加指导
"""
## OUTPUT CONTRACT

你的输出必须使用 MarkedContent 格式:

```python
from context import mark, Importance

# 标注高重要性内容（核心文件、严重问题、关键决策）
mark("src/auth/login.py", Importance.HIGH, "file", "眼分身")

# 标注中等重要性内容（相关文件、一般问题、辅助信息）
mark("src/auth/utils.py", Importance.MEDIUM, "file", "眼分身")

# 标注低重要性内容（辅助文件、细节信息、冗余内容）
mark("src/auth/legacy.py", Importance.LOW, "file", "眼分身")
```

**重要性判断标准**:

- HIGH: 核心功能、严重问题、关键决策、主要文件
- MEDIUM: 辅助功能、一般问题、相关文件
- LOW: 冗余信息、细节、辅助文件
"""
```

### 眼分身示例

```python
# 在眼分身的 output 中
from context import mark, Importance, format_marked_output

# 探索结果
items = [
    mark("src/auth/login.py - 主要登录逻辑", Importance.HIGH, "file", "眼分身"),
    mark("src/auth/oauth.py - OAuth2 实现", Importance.HIGH, "file", "眼分身"),
    mark("src/auth/jwt_util.py - JWT 工具", Importance.MEDIUM, "file", "眼分身"),
    mark("src/auth/legacy.py - 旧版代码", Importance.LOW, "file", "眼分身"),
    mark("src/auth/__init__.py - 模块初始化", Importance.LOW, "file", "眼分身"),
]

# 格式化输出
output = format_marked_output(items)
```

### 鼻分身示例

```python
# 在鼻分身的 output 中
from context import mark, Importance

# 审查结果
issues = [
    mark("发现 SQL 注入风险在 login.py:42", Importance.HIGH, "issue", "鼻分身"),
    mark("发现硬编码密钥在 oauth.py:15", Importance.HIGH, "issue", "鼻分身"),
    mark("建议添加日志记录", Importance.MEDIUM, "suggestion", "鼻分身"),
    mark("代码格式不一致", Importance.LOW, "info", "鼻分身"),
]
```

---

## 集成点 3: 本体聚合后台分身结果

本体等待后台分身完成后，自动聚合结果。

```python
# 在 wukong 本体中
from context import ResultAggregator, TaskResult
import json

def aggregate_avatar_results(tasks):
    """
    聚合后台分身结果

    Args:
        tasks: List[Tuple[str, Task]] - (task_id, task) 列表

    Returns:
        summary: str - 聚合结果（常形态或缩形态）
    """
    aggregator = ResultAggregator()

    # 等待所有任务完成并收集结果
    for task_id, task in tasks:
        # 获取任务输出
        output = TaskOutput(task.id)

        # 解析 marked_items（假设分身返回 JSON）
        try:
            result_data = json.loads(output.content)
            marked_items = result_data.get('marked_items', [])
            status = result_data.get('status', 'completed')
            avatar = result_data.get('avatar', 'unknown')
        except:
            # 如果分身没有返回结构化数据，使用原始输出
            marked_items = []
            status = 'completed'
            avatar = 'unknown'

        # 添加到聚合器
        aggregator.add_result(TaskResult(
            task_id=task_id,
            avatar=avatar,
            status=status,
            output=output.content,
            marked_items=marked_items
        ))

    # 根据上下文长度决定使用常形态还是缩形态
    current_context_length = get_current_context_length()

    if current_context_length > 50000:  # 上下文已经很长
        return aggregator.get_compact_summary(max_chars=500)  # 缩形态
    else:
        return aggregator.aggregate(max_chars=2000)  # 常形态
```

### 使用示例

```python
# 接上面的并行召唤示例

# 等待并聚合结果
summary = aggregate_avatar_results(tasks)

# 输出给用户
print(summary)

# 可选: 只看高优先级
high_only = aggregator.get_high_importance_only()
for item in high_only:
    print(f"[{item.source}] {item.content}")
```

---

## 完整工作流示例

```python
# 1. 用户请求
user_request = "探索并审查 src/auth/ 目录，找出安全问题"

# 2. 本体准备上下文
compact_context = compress_current_context(max_chars=500)  # 压缩为缩形态
anchors = load_relevant_anchors(['auth', 'security'])  # 从识模块加载锚点

# 3. 本体召唤并行分身
tasks = summon_parallel_avatars(
    task_descriptions=[
        {'id': 'eye-1', 'description': '探索 src/auth/', 'model': 'haiku'},
        {'id': 'nose-1', 'description': '审查代码安全', 'model': 'haiku'},
    ],
    compact_context=compact_context,
    anchors=anchors
)

# 4. 等待并聚合结果
summary = aggregate_avatar_results(tasks)

# 5. 展示给用户
print("## 探索与审查结果")
print(summary)

# 6. 提取高优先级问题
high_priority = aggregator.get_high_importance_only()

if high_priority:
    print("\n## 需要立即处理的问题:")
    for item in high_priority:
        if item.category == 'issue':
            print(f"- {item.content}")
```

---

## 与识模块集成

将高重要性内容自动写入锚点。

```python
from context import Importance

def save_high_importance_to_anchors(aggregator, anchor_type='I'):
    """
    将高重要性内容保存为锚点

    Args:
        aggregator: ResultAggregator
        anchor_type: str - 锚点类型 (I=Interface, D=Decision, C=Constraint, etc.)
    """
    high_items = aggregator.get_high_importance_only()

    for item in high_items:
        # 写入锚点文件
        add_anchor(
            anchor_type=anchor_type,
            content=f"[{item.source}] {item.content}",
            metadata={
                'category': item.category,
                'source': item.source,
                'timestamp': datetime.now().isoformat()
            }
        )
```

---

## 性能优化建议

1. **并行度控制**
   - CHEAP 分身 (眼/耳/鼻): 10+ 并发
   - MEDIUM 分身 (舌): 2-3 并发
   - EXPENSIVE 分身 (身/意): 1 个阻塞

2. **上下文压缩**
   - 使用 compress_by_importance() 压缩分身输出
   - 优先保留 HIGH 重要性内容
   - 自动丢弃 LOW 重要性内容

3. **快照复用**
   - 同一批并行分身共享一个快照
   - 避免重复传递大段上下文

4. **增量聚合**
   - 分身完成时立即添加到聚合器
   - 不需要等待所有分身完成再聚合

---

## 错误处理

```python
from context import ResultAggregator, TaskResult, mark, Importance

def safe_aggregate_results(tasks):
    """安全的聚合，处理分身失败情况"""
    aggregator = ResultAggregator()

    for task_id, task in tasks:
        try:
            output = TaskOutput(task.id)

            # 检查任务是否成功
            if task.status == 'failed':
                aggregator.add_result(TaskResult(
                    task_id=task_id,
                    avatar='unknown',
                    status='failed',
                    output=output.error_message,
                    marked_items=[
                        mark(f"任务失败: {output.error_message}",
                             Importance.HIGH, "error", "system")
                    ]
                ))
            else:
                # 正常处理
                aggregator.add_result(TaskResult(
                    task_id=task_id,
                    avatar=task.avatar,
                    status='completed',
                    output=output.content,
                    marked_items=parse_marked_items(output.content)
                ))
        except Exception as e:
            # 任务获取失败
            aggregator.add_result(TaskResult(
                task_id=task_id,
                avatar='unknown',
                status='failed',
                output=str(e),
                marked_items=[
                    mark(f"任务异常: {str(e)}",
                         Importance.HIGH, "error", "system")
                ]
            ))

    return aggregator.aggregate(max_chars=2000)
```

---

## 总结

集成上下文优化模块后，Wukong 将获得：

1. **一致的上下文传递** - 并行分身获得相同的快照
2. **智能压缩** - 自动优先保留重要信息
3. **自动聚合** - 后台分身结果自动汇总
4. **上下文效率** - 减少冗余传递，节省 token

建议逐步集成：

- 第一阶段: 在并行召唤时使用快照
- 第二阶段: 要求分身标注重要性
- 第三阶段: 自动聚合后台结果
- 第四阶段: 与识模块深度集成
