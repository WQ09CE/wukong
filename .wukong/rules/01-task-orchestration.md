# Task Orchestration Protocol (任务编排协议)

## Pre-Delegation Declaration (召唤分身前声明)

**BEFORE EVERY Avatar summoning, declare:**

```
我将召唤分身:
- **Avatar**: [需求悟空/架构悟空/斗战胜佛/测试悟空/审查悟空/探索悟空/内观悟空]
- **Reason**: [为什么需要这个分身]
- **Expected Outcome**: [期望的交付物]
- **Background**: [true/false - 是否后台运行]
```

**本体职责提醒**:
- 本体专注于用户交互，不直接写大量代码
- 代码实现交给斗战胜佛
- 本体负责监督、验证、汇报

## Avatar Selection Decision Tree

```
1. 是需求分析/澄清任务?
   ✓ YES → 需求悟空
   ✗ NO → Continue

2. 是架构/设计/技术选型任务?
   ✓ YES → 架构悟空
   ✗ NO → Continue

3. 是代码实现/编写/开发任务?
   ✓ YES → 斗战胜佛 ⚔️
   ✗ NO → Continue

4. 是代码探索/研究任务?
   ✓ YES → 探索悟空 (background=true)
   ✗ NO → Continue

5. 是测试编写/验证任务?
   ✓ YES → 测试悟空
   ✗ NO → Continue

6. 是代码审查任务?
   ✓ YES → 审查悟空 (background=true)
   ✗ NO → Continue

7. 是流程反思/改进分析任务?
   ✓ YES → 内观悟空
   ✗ NO → Continue

8. 是用户对话/问答/简单任务?
   ✓ YES → 本体直接处理
```

## Introspection Protocol (内观协议)

> 吾日三省吾身 - 复杂任务完成后，进行内观反思。

### 何时召唤内观悟空

| 触发条件 | 内观深度 | 说明 |
|----------|----------|------|
| 复杂任务完成 | 深度 | 多分身协作的任务 |
| 任务失败/重做 | 深度 | 分析失败原因 |
| 用户主动请求 | 按需 | "反思一下"、"总结经验" |
| 简单任务完成 | 跳过 | 不需要内观 |

### 内观深度

```
快速内观 (简要):
├── 主要问题识别
├── 1-2 条改进建议
└── 耗时: 1-2 分钟

深度内观 (完整):
├── 6 维度完整分析
├── 详细改进建议
├── 更新 notepads/learnings.md
└── 耗时: 5-10 分钟
```

### 内观不是批判

```
✅ 正确的内观:
   - 客观分析做得好的和需改进的
   - 提供具体可行的建议
   - 将学习沉淀为知识

❌ 错误的内观:
   - 只批评不肯定
   - 泛泛而谈无法执行
   - 为了反思而反思
```

## Task Prompt Template

```markdown
## 任务 (TASK)
[具体、可衡量的目标]

## 背景 (CONTEXT)
- 技术栈: [C++/Python/FastAPI/...]
- 相关文件: [file paths]
- 现有模式: [patterns to follow]

## 期望产出 (EXPECTED OUTCOME)
- [ ] [具体交付物 1]
- [ ] [具体交付物 2]
- [ ] [成功标准]

## 必须做 (MUST DO)
- [遵循的规范]
- [参考的文件/模块]
- [性能要求]

## 禁止做 (MUST NOT DO)
- [禁止的反模式]
- [避免的技术债]
```

## Parallel Execution Strategy (筋斗云并行策略)

> **筋斗云**: 一个筋斗十万八千里。分身术的精髓在于**同时出击**，而非排队等候。

### The Parallelization Decision Tree (并行决策树)

```
开始任务分析
     │
     ▼
┌─────────────────────────────────────────┐
│ Q1: 任务可以分解为多个独立子任务吗？        │
└─────────────────────────────────────────┘
     │
     ├── NO → 单分身串行执行
     │
     ▼ YES
┌─────────────────────────────────────────┐
│ Q2: 子任务之间有数据依赖吗？               │
│     (一个的输出是另一个的输入)              │
└─────────────────────────────────────────┘
     │
     ├── YES → 按依赖顺序串行
     │
     ▼ NO
┌─────────────────────────────────────────┐
│ Q3: 子任务会修改同一个文件吗？             │
└─────────────────────────────────────────┘
     │
     ├── YES → 串行执行（避免冲突）
     │
     ▼ NO
┌─────────────────────────────────────────┐
│ ✅ 可以并行！召唤多个分身同时执行          │
└─────────────────────────────────────────┘
```

### Parallelization Patterns (并行模式)

#### Pattern 1: **分身群攻** (Multi-Module Implementation)
**场景**: 实现多个独立模块（无相互依赖）
**加速比**: 理论 Nx（N = 模块数）

```
设计完成后:
     │
     ├──→ [斗战胜佛 A] 实现 module_a.py  ──┐
     ├──→ [斗战胜佛 B] 实现 module_b.py  ──┼──→ 合并验证
     └──→ [斗战胜佛 C] 实现 module_c.py  ──┘

# 召唤方式 (在同一条消息中发送多个 Task)
Task(subagent_type="general-purpose", prompt="实现 module_a", run_in_background=true)
Task(subagent_type="general-purpose", prompt="实现 module_b", run_in_background=true)
Task(subagent_type="general-purpose", prompt="实现 module_c", run_in_background=true)
```

#### Pattern 2: **侦察兵 + 主力军** (Scout & Infantry)
**场景**: 实现功能时需要不断查阅参考
**加速比**: 减少等待时间

```
开始实现:
     │
     ├──→ [探索悟空] 研究相关 API 和模式 (后台)
     │         │
     │         └──→ 持续提供参考信息
     │
     └──→ [斗战胜佛] 开始实现代码
               │
               └──→ 遇到不确定时，从探索悟空获取答案

# 召唤方式
Task(subagent_type="Explore", prompt="研究 X 库的用法和最佳实践", run_in_background=true)
Task(subagent_type="general-purpose", prompt="实现 Y 功能，参考探索悟空的发现")
```

#### Pattern 3: **TDD 钳形攻势** (Test + Implement Pincer)
**场景**: 接口已明确定义（设计文档/头文件）
**加速比**: ~2x

```
接口定义完成:
     │
     ├──→ [测试悟空] 根据接口编写测试 (后台)
     │
     └──→ [斗战胜佛] 实现接口 (后台)
               │
               ▼
          [合并] → 运行测试 → 验证

# 召唤方式
Task(subagent_type="general-purpose", prompt="根据接口定义编写测试", run_in_background=true)
Task(subagent_type="general-purpose", prompt="实现接口", run_in_background=true)
# 等待两者完成后运行测试
```

#### Pattern 4: **代码 + 配置并行** (Code + Config Parallel)
**场景**: 实现代码的同时准备部署配置
**加速比**: ~1.5x

```
设计完成后:
     │
     ├──→ [斗战胜佛] 实现核心代码
     │
     └──→ [架构悟空] 准备 Dockerfile / CI 配置 (后台)
               │
               └──→ 容器配置不依赖具体实现细节

# 召唤方式
Task(subagent_type="general-purpose", prompt="实现核心功能代码")
Task(subagent_type="general-purpose", prompt="准备 Dockerfile 和 docker-compose", run_in_background=true)
```

#### Pattern 5: **蜂群模式** (Swarm - Mass Operations)
**场景**: 批量重构/迁移多个独立文件
**加速比**: ~Nx

```
重构计划确定后:
     │
     ├──→ [斗战胜佛 A] 重构 file_1.py  ──┐
     ├──→ [斗战胜佛 B] 重构 file_2.py  ──┤
     ├──→ [斗战胜佛 C] 重构 file_3.py  ──┼──→ 合并
     └──→ [斗战胜佛 D] 重构 file_4.py  ──┘

# 召唤方式 (限制同时 3-4 个分身)
Task(subagent_type="general-purpose", prompt="重构 file_1", run_in_background=true)
Task(subagent_type="general-purpose", prompt="重构 file_2", run_in_background=true)
Task(subagent_type="general-purpose", prompt="重构 file_3", run_in_background=true)
```

### Parallelization Rules (并行规则)

#### ✅ 可以并行的场景

| 场景 | 模式 | 最大并行数 |
|------|------|-----------|
| 实现多个独立模块 | 分身群攻 | 3-4 |
| 实现 + 探索参考 | 侦察兵+主力军 | 2 |
| 实现 + 写测试 (接口已定) | TDD钳形攻势 | 2 |
| 代码 + 部署配置 | 代码+配置并行 | 2 |
| 批量文件修改 | 蜂群模式 | 3-4 |
| 多文件代码审查 | 审查分身群 | 3-4 |
| 多模块代码探索 | 探索分身群 | 3-4 |

#### ❌ 必须串行的场景

| 场景 | 原因 |
|------|------|
| 需求 → 架构 → 实现 | 依赖上游输出 |
| 修改同一文件的多个任务 | 会产生冲突 |
| 测试依赖未完成的代码 | 会失败 |
| 需要用户确认的决策点 | 阻塞等待 |

### Parallel Execution Syntax (并行召唤语法)

**关键**: 在**同一条消息**中发送多个 Task 调用

```python
# ✅ 正确: 同一消息中多个 Task (并行执行)
<message>
Task(subagent_type="general-purpose", prompt="任务A", run_in_background=true)
Task(subagent_type="general-purpose", prompt="任务B", run_in_background=true)
Task(subagent_type="general-purpose", prompt="任务C", run_in_background=true)
</message>

# ❌ 错误: 分开发送 (串行执行)
<message>Task(...任务A...)</message>
<message>Task(...任务B...)</message>
<message>Task(...任务C...)</message>
```

### Resource Management (资源管理)

```
并行分身限制:
├── 最大同时运行: 3-4 个分身
├── 后台探索: 不计入限制
└── 超过限制时: 批次执行

示例 (8个独立模块):
├── 第一批: 模块 1, 2, 3, 4 (并行)
├── 等待完成
└── 第二批: 模块 5, 6, 7, 8 (并行)
```

### Merge Protocol (合并协议)

并行任务完成后:

```
1. 收集所有分身的输出
2. 检查是否有冲突
3. 如有冲突 → 手动解决
4. 运行完整验证 (构建 + 测试)
5. 确认无误后继续
```

## Domain-Specific Patterns

### C++ Projects

```markdown
## Build & Test Commands
- Configure: cmake -B build -DCMAKE_BUILD_TYPE=Release
- Build: cmake --build build -j$(nproc)
- Test: ctest --test-dir build --output-on-failure
- Coverage: gcov/lcov

## Code Patterns
- RAII for resource management
- Smart pointers (unique_ptr, shared_ptr)
- Exception safety guarantees
- const correctness
```

### Python Projects

```markdown
## Build & Test Commands
- Install: pip install -e ".[dev]"
- Test: pytest -v --cov
- Lint: ruff check . && mypy .
- Format: ruff format .

## Code Patterns
- Type hints (Python 3.10+)
- Pydantic for data validation
- async/await for I/O
- Dependency injection
```

### FastAPI Projects

```markdown
## Structure
src/
├── api/           # Route handlers
├── core/          # Config, security
├── models/        # Pydantic models
├── services/      # Business logic
└── repositories/  # Data access

## Patterns
- Dependency injection via Depends
- Async database operations
- Response models for validation
- OpenAPI documentation
```

### Video Processing

```markdown
## Libraries
- FFmpeg: transcoding, muxing
- GStreamer: pipeline processing
- OpenCV: frame analysis
- VAAPI/NVENC: hardware acceleration

## Patterns
- Zero-copy frame passing
- Pipeline parallelism
- Memory pool management
- Frame rate control
```

### AI Inference

```markdown
## Runtimes
- ONNX Runtime: cross-platform
- TensorRT: NVIDIA optimization
- OpenVINO: Intel optimization

## Patterns
- Batching for throughput
- Async inference
- Model versioning
- Input validation
```

## Workflow Tracks (动态编排)

### Track A: Feature Development (The Waterfall)
**Trigger**: New features, massive changes.
**Flow**: `Req -> Arch -> Impl + Explore -> Test -> Review`

### Track B: Bug Fix (The Surgical Strike)
**Trigger**: "Fix this error", "It's crashing".
**Flow**:
1. **Locate**: Explore Wukong finds the bug.
2. **Fix**: Battle Wukong applies the fix. (No `design.md` needed, just fix it).
3. **Verify**: Test Wukong adds a regression case.

### Track C: Refactoring (The Renewal)
**Trigger**: "Cleanup", "Modernize", "Optimize".
**Flow**:
1. **Map**: Explore Wukong maps dependencies.
2. **Plan**: Arch Wukong creates a strategy (not full design).
3. **Execute**: Battle Wukong implements changes.
4. **Safety**: Test Wukong verifies behavior.

### Stage 1: 需求获取 (Requirement Gathering)

```
Input: 用户请求
Avatar: 需求悟空

Tasks:
1. 解析显式需求
2. 推导隐式需求
3. 识别边界条件
4. 确认技术约束

Output: requirements.md
```

### Stage 2: 方案设计 (Solution Design)

```
Input: requirements.md
Avatar: 架构悟空

Tasks:
1. 分析现有架构
2. 设计解决方案
3. 技术选型
4. 识别风险

Output: design.md
```

### Stage 3: 代码实现 (Implementation)

```
Input: design.md
Avatar: 斗战胜佛 ⚔️ + 探索悟空 (parallel)

Tasks:
1. 探索悟空: 研究相关代码 (background)
2. 斗战胜佛: 按设计实现代码
3. 本体: 监督进度，回答问题
4. 增量验证

Output: 代码变更
```

### Stage 4: 测试验证 (Testing)

```
Input: 代码变更
Avatar: 测试悟空

Tasks:
1. 编写单元测试
2. 编写集成测试
3. 验证边界条件
4. 检查覆盖率

Output: 测试通过
```

### Stage 5: 代码审查 (Code Review)

```
Input: 代码变更 + 测试
Avatar: 审查悟空

Tasks:
1. 检查代码质量
2. 验证设计一致性
3. 识别潜在问题
4. 提出改进建议

Output: review.md
```

## Resume Protocol (继续协议)

| Scenario | Action |
|----------|--------|
| 上次搜索未完成 | `resume: "<agent_id>"` |
| 需要补充之前的发现 | `resume: "<agent_id>"` |
| 完全不同的任务 | 重新开始 |
| 上下文过期 (>30 min) | 重新开始 |
