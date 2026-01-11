# Task Orchestration Protocol (任务编排协议)

## Pre-Delegation Declaration (召唤分身前声明)

**BEFORE EVERY Avatar summoning, declare:**

```
我将召唤分身:
- **Avatar**: [需求悟空/架构悟空/斗战胜佛/测试悟空/审查悟空/探索悟空]
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

7. 是用户对话/问答/简单任务?
   ✓ YES → 本体直接处理
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

## Parallel Execution Strategy (并行执行策略)

### High-Throughput Patterns

**1. The "Scout & Infantry" Pattern (Explore + Implement)**
*Use when:* You are implementing a feature but need to look up references constantly.
```typescript
Task(agent="implementer", prompt="Implement class A...")
Task(agent="explorer", prompt="Find usage examples of API X...", background=true)
```

**2. The "TDD Pincer" Pattern (Test + Implement)**
*Use when:* The interface/signature is already defined (e.g., in a design doc or header file).
```typescript
// Parallel Attack
Task(agent="tester", prompt="Write tests for Interface I...", background=true)
Task(agent="implementer", prompt="Implement Interface I...", background=true)
// Merge: Wait for both, then run tests.
```

**3. The "Swarm" Pattern (Mass Refactoring)**
*Use when:* Renaming or migrating multiple independent files.
```typescript
Task(agent="implementer", prompt="Migrate File A...", background=true)
Task(agent="implementer", prompt="Migrate File B...", background=true)
Task(agent="implementer", prompt="Migrate File C...", background=true)
```

### When to Parallelize

```
✓ PARALLEL (可以并行):
  - 不同模块的探索
  - 不同文件的审查
  - 独立的测试用例
  - 斗战胜佛 + 探索悟空 (实现时并行探索)

✗ SEQUENTIAL (必须串行):
  - 需求悟空 → 架构悟空 → 斗战胜佛 → 测试悟空 → 审查悟空
  - 编辑同一文件
  - 测试依赖前置改动
```

### Parallel Execution Pattern

```typescript
// Launch multiple independent avatars in ONE message
Task(subagent_type="Explore", prompt="探索模块A", run_in_background=true)
Task(subagent_type="Explore", prompt="探索模块B", run_in_background=true)
Task(subagent_type="general-purpose", prompt="研究外部API", run_in_background=true)

// Continue with other work while avatars run
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
