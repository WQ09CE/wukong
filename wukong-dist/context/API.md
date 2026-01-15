# Wukong Context API Reference

## Quick Import

```python
from context import (
    # Snapshot
    ContextSnapshot, create_snapshot, get_snapshot_for_task,
    # Importance
    Importance, MarkedContent, mark, compress_by_importance, format_marked_output,
    # Aggregator
    TaskResult, ResultAggregator
)
```

## snapshot.py

### ContextSnapshot

不可变的上下文快照（frozen dataclass）。

**字段**:
- `session_id: str` - 会话 ID
- `timestamp: datetime` - 创建时间戳
- `compact_context: str` - 缩形态上下文 (<500 字)
- `anchors: List[Anchor]` - 锚点列表
- `metadata: Dict[str, Any]` - 元数据（可选）

### create_snapshot()

创建上下文快照。

```python
def create_snapshot(
    session_id: str,
    compact_context: str,
    anchors: List[Dict[str, Any]],
    metadata: Dict[str, Any] = None
) -> ContextSnapshot
```

**参数**:
- `session_id` - 会话 ID
- `compact_context` - 缩形态上下文 (应 <500 字)
- `anchors` - 锚点列表，格式: `[{"type": "D", "content": "..."}, ...]`
- `metadata` - 可选元数据

**返回**: 不可变的 `ContextSnapshot` 对象

**示例**:
```python
snapshot = create_snapshot(
    session_id="abc123",
    compact_context="正在实现认证模块",
    anchors=[
        {"type": "D", "content": "使用 JWT"},
        {"type": "C", "content": "必须 HTTPS"}
    ]
)
```

### get_snapshot_for_task()

将快照格式化为 prompt 片段。

```python
def get_snapshot_for_task(
    snapshot: ContextSnapshot,
    task_id: str
) -> str
```

**参数**:
- `snapshot` - 上下文快照
- `task_id` - 任务 ID

**返回**: 格式化的 prompt 字符串

**示例**:
```python
prompt = get_snapshot_for_task(snapshot, "task-001")
# 包含: session_id, task_id, 缩形态上下文, 锚点列表
```

---

## importance.py

### Importance (Enum)

重要性级别枚举。

**值**:
- `Importance.HIGH` - 必须保留（关键信息）
- `Importance.MEDIUM` - 优先保留（辅助信息）
- `Importance.LOW` - 可丢弃（冗余信息）

### MarkedContent

带重要性标记的内容（dataclass）。

**字段**:
- `content: str` - 内容文本
- `importance: Importance` - 重要性级别
- `category: str` - 类别 (file, issue, decision, etc.)
- `source: str` - 来源分身名称

### mark()

标注内容的重要性。

```python
def mark(
    content: str,
    importance: Importance,
    category: str,
    source: str
) -> MarkedContent
```

**参数**:
- `content` - 内容文本
- `importance` - 重要性级别 (HIGH/MEDIUM/LOW)
- `category` - 内容类别
- `source` - 来源分身名称

**返回**: `MarkedContent` 对象

**示例**:
```python
item = mark(
    content="src/auth/login.py",
    importance=Importance.HIGH,
    category="file",
    source="眼分身"
)
```

### compress_by_importance()

按重要性压缩内容，优先保留 HIGH。

```python
def compress_by_importance(
    items: List[MarkedContent],
    max_chars: int
) -> List[MarkedContent]
```

**参数**:
- `items` - 标注内容列表
- `max_chars` - 最大字符数限制

**返回**: 压缩后的内容列表（按重要性排序）

**算法**: 按 HIGH -> MEDIUM -> LOW 排序，贪婪选择直到达到字符限制

**示例**:
```python
compressed = compress_by_importance(items, max_chars=500)
# 优先保留 HIGH，然后 MEDIUM，最后 LOW
```

### format_marked_output()

格式化带标记的输出。

```python
def format_marked_output(items: List[MarkedContent]) -> str
```

**参数**:
- `items` - 标注内容列表

**返回**: 格式化的字符串（按重要性分组）

**输出格式**:
```
### 高优先级 (HIGH)
- [category] (source) content
...

### 中优先级 (MEDIUM)
- [category] (source) content
...

### 低优先级 (LOW)
- [category] (source) content
...
```

---

## aggregator.py

### TaskResult

后台任务结果（dataclass）。

**字段**:
- `task_id: str` - 任务 ID
- `avatar: str` - 分身名称
- `status: str` - 状态 (completed, failed, pending)
- `output: str` - 输出内容
- `marked_items: List[MarkedContent]` - 标注内容列表（默认空）
- `metadata: Dict[str, Any]` - 元数据（默认空）

### ResultAggregator

结果聚合器。

#### add_result()

添加任务结果。

```python
def add_result(self, result: TaskResult) -> None
```

**参数**:
- `result` - `TaskResult` 对象

#### aggregate()

聚合为常形态（结构化输出）。

```python
def aggregate(self, max_chars: int = 2000) -> str
```

**参数**:
- `max_chars` - 最大字符数限制（默认 2000）

**返回**: 格式化的聚合结果

**输出包含**:
- 任务数量和状态概览
- 按重要性分组的标注内容

#### get_compact_summary()

聚合为缩形态（极简摘要）。

```python
def get_compact_summary(self, max_chars: int = 500) -> str
```

**参数**:
- `max_chars` - 最大字符数限制（默认 500）

**返回**: 极简摘要

**特点**: 只保留 HIGH 重要性内容，极简格式

#### get_high_importance_only()

只获取高重要性内容。

```python
def get_high_importance_only(self) -> List[MarkedContent]
```

**返回**: HIGH 重要性的标注内容列表

#### clear()

清空所有结果。

```python
def clear(self) -> None
```

---

## 完整工作流示例

```python
from context import (
    create_snapshot, get_snapshot_for_task,
    mark, Importance,
    TaskResult, ResultAggregator
)

# 1. 创建快照（本体）
snapshot = create_snapshot(
    session_id="session-001",
    compact_context="正在重构认证模块",
    anchors=[{"type": "D", "content": "使用 OAuth2"}]
)

# 2. 并行召唤分身（本体）
task_ids = ["eye-1", "nose-1"]
for task_id in task_ids:
    prompt = get_snapshot_for_task(snapshot, task_id)
    # Task(prompt=f"{prompt}\n\n## YOUR TASK\n{...}")

# 3. 分身输出时标注重要性（分身）
eye_output = [
    mark("src/auth/oauth.py", Importance.HIGH, "file", "眼分身"),
    mark("src/auth/legacy.py", Importance.LOW, "file", "眼分身"),
]

nose_output = [
    mark("发现安全问题", Importance.HIGH, "issue", "鼻分身"),
]

# 4. 聚合结果（本体）
aggregator = ResultAggregator()

aggregator.add_result(TaskResult(
    task_id="eye-1",
    avatar="眼分身",
    status="completed",
    output="探索完成",
    marked_items=eye_output
))

aggregator.add_result(TaskResult(
    task_id="nose-1",
    avatar="鼻分身",
    status="completed",
    output="审查完成",
    marked_items=nose_output
))

# 5. 获取聚合结果
summary = aggregator.aggregate(max_chars=2000)  # 常形态
compact = aggregator.get_compact_summary(max_chars=500)  # 缩形态
high_only = aggregator.get_high_importance_only()  # 只看 HIGH
```

---

## 类型签名速查

```python
# snapshot
create_snapshot(str, str, List[Dict], Dict?) -> ContextSnapshot
get_snapshot_for_task(ContextSnapshot, str) -> str

# importance
mark(str, Importance, str, str) -> MarkedContent
compress_by_importance(List[MarkedContent], int) -> List[MarkedContent]
format_marked_output(List[MarkedContent]) -> str

# aggregator
ResultAggregator.add_result(TaskResult) -> None
ResultAggregator.aggregate(int?) -> str
ResultAggregator.get_compact_summary(int?) -> str
ResultAggregator.get_high_importance_only() -> List[MarkedContent]
ResultAggregator.clear() -> None
```
