# Schedule Command (调度命令)

> **智能调度** - 分析任务，规划最优执行路径

## Usage (使用方式)

```
/schedule <任务描述>
/schedule --dry-run <任务描述>    # 只分析不执行
/schedule --plan <任务描述>       # 生成完整执行计划
```

## What This Command Does

1. **分析任务** - 检测任务类型和复杂度
2. **选择轨道** - Feature / Fix / Refactor / Direct
3. **规划分身** - 确定需要哪些分身、执行顺序、并行策略
4. **检测冲突** - 文件领地冲突检测
5. **生成计划** - 输出可执行的调度计划

## Execution Flow

```python
# 1. 导入调度器 (跨平台路径发现，用户级优先)
import sys
import os

# 发现链：用户级 → 项目级
runtime_paths = [
    os.path.expanduser("~/.wukong/runtime"),  # 用户级 (优先)
    ".wukong/runtime",                         # 项目级 (fallback)
]
for path in runtime_paths:
    if os.path.isdir(path):
        sys.path.insert(0, path)
        break

from scheduler import WukongScheduler, AvatarType, TrackType, AVATAR_CONFIG, TRACK_DAG

# 2. 创建调度器实例
scheduler = WukongScheduler()

# 3. 分析任务
task_description = "{user_input}"
track = scheduler.detect_track(task_description)

# 4. 规划执行
phases = scheduler.plan_track(track, task_description)

# 5. 输出计划
```

## Output Format

当用户运行 `/schedule <任务>` 时，输出以下格式：

```markdown
## 调度分析结果

### 任务信息
- **描述**: {task_description}
- **检测轨道**: {track} (Feature/Fix/Refactor/Direct)

### 执行计划

| Phase | 分身 | 模型 | 后台 | 依赖 |
|-------|------|------|------|------|
| 1 | 👁️ 眼 + 👂 耳 | haiku | 是 | - |
| 2 | 🧠 意 | opus | 否 | Phase 1 |
| 3 | ⚔️ 身 | sonnet | 否 | Phase 2 |
| 4 | 👅 舌 + 👃 鼻 | sonnet/haiku | 是 | Phase 3 |

### 并行策略
- **Phase 1**: 可并行 (CHEAP 分身，10+ 并发)
- **Phase 2-3**: 串行 (EXPENSIVE 分身，1 并发)
- **Phase 4**: 可并行 (MEDIUM + CHEAP)

### 预估
- **总阶段**: 4
- **可并行阶段**: 2
- **EXPENSIVE 调用**: 2 (意 + 身)

### 建议操作
{根据分析给出建议}
```

## Integration with Wukong

此命令与 Wukong 工作流无缝集成：

1. **独立使用**: `/schedule 添加用户认证` - 只分析，不执行
2. **配合 Wukong**: 先 `/schedule` 分析，再 `/wukong` 执行
3. **Dry-run 模式**: `/schedule --dry-run` 验证计划是否合理

## Scheduler Configuration Reference

### 分身成本配置

| 分身 | 成本 | 模型 | 最大并发 | 后台 |
|------|------|------|---------|------|
| 👁️ 眼 | CHEAP | haiku | 10+ | 必须 |
| 👂 耳 | CHEAP | haiku | 10+ | 可选 |
| 👃 鼻 | CHEAP | haiku | 5+ | 必须 |
| 👅 舌 | MEDIUM | sonnet | 3 | 可选 |
| ⚔️ 身 | EXPENSIVE | sonnet | 1 | 禁止 |
| 🧠 意 | EXPENSIVE | opus | 1 | 禁止 |

### 轨道 DAG

**Feature**: 耳+眼 → 意 → 身 → 舌+鼻
**Fix**: 眼+鼻 → 身 → 舌
**Refactor**: 眼 → 意 → 身 → 鼻+舌
**Direct**: 直接执行

## Now Execute

读取用户输入的任务描述，执行以下步骤：

1. **解析参数**
   ```
   --dry-run: 只输出分析，不建议执行
   --plan: 输出详细执行计划 + TodoWrite 格式
   无参数: 输出分析 + 建议下一步
   ```

2. **运行调度分析**
   ```python
   # 使用上面的路径发现机制导入 runtime scheduler
   from scheduler import WukongScheduler, TrackType

   scheduler = WukongScheduler()
   track = scheduler.detect_track(user_task)
   phases = scheduler.plan_track(track, user_task)
   ```

3. **格式化输出**
   - 使用上面定义的 Markdown 格式
   - 包含执行建议

4. **可选：生成 TodoWrite**
   如果用户使用 `--plan`，额外生成：
   ```python
   from todo_integration import TodoWriteIntegration
   integration = TodoWriteIntegration(scheduler)
   todo_call = integration.generate_todo_call()
   # 输出可直接用于 TodoWrite 的 JSON
   ```

## Error Handling

- 如果调度器模块不存在，提示用户检查 `~/.wukong/runtime/` 或 `.wukong/runtime/` 目录
- 如果任务描述为空，提示用户提供任务
- 如果检测到复杂冲突，建议拆分任务

---

**就绪**！请提供任务描述，我将分析并生成最优调度计划。
