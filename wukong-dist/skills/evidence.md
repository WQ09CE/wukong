# Evidence Skill (证据验证技能)

> **定**：心止一处，不动不乱。验证证据的等级与可复现性。

## 职责

Evidence Skill 负责验证分身输出的证据等级：
- 评估证据等级 (L0-L3)
- 执行验证命令
- 记录证据审计轨迹
- 判定通过/拒绝

## 证据等级定义

| Level | 名称 | 说明 | 可信度 | 要求 |
|-------|------|------|--------|------|
| **L0** | 推测 | 基于经验的猜测 | 不可信 | 必须拒绝 |
| **L1** | 引用 | 引用但未验证 | 条件可信 | 仅 Direct Track 可接受 |
| **L2** | 本地验证 | 本地命令验证 | 默认可信 | 标准门槛 |
| **L3** | 集成验证 | 端到端验证 | 完全可信 | 最高门槛 |

## L0 危险信号

以下表述必须触发拒绝：

```
"应该可以..." / "大概能..." → 推测
"我觉得..." / "我认为..." → 主观判断
"一般来说..." / "通常..." → 泛化假设
"显然..." / "当然..." → 隐藏假设
"没有问题" / "应该没事" → 乐观偏见
```

## 健康信号

以下表述表明存在证据：

```
"根据 {path}:{line}，..." → 有证据引用
"执行 {command} 输出 {result}" → 有验证
"测试 {test_name} 通过" → 有测试
"文件 {path} 已创建，内容包含..." → 有确认
```

## 验证流程

```
┌─────────────────────────────────────────┐
│  1. 接收分身输出                         │
│                                         │
│  2. 扫描危险信号                         │
│     → 发现 L0 信号 → 拒绝               │
│                                         │
│  3. 评估证据等级                         │
│     → 无验证命令输出 → L1               │
│     → 有验证命令输出 → L2               │
│     → 有端到端测试 → L3                 │
│                                         │
│  4. 检查轨道门槛                         │
│     → 证据等级 < 门槛 → 补充验证         │
│                                         │
│  5. 记录证据                             │
│                                         │
│  6. 返回判定结果                         │
└─────────────────────────────────────────┘
```

## 轨道门槛

| 轨道 | 最低等级 | 额外要求 |
|------|----------|----------|
| **Fix** | L2 | + 复现用例 + 回归测试 |
| **Feature** | L2 | + AC 测试覆盖 |
| **Refactor** | L2 | + 行为不变证明 |
| **Direct** | L1 | 简单任务可降级 |

## 验证命令参考

### Python 项目

```bash
# 语法检查
python -m py_compile <file>

# 类型检查
mypy src/

# Lint
ruff check .

# 测试
pytest -v --tb=short

# 覆盖率
pytest --cov=src --cov-report=term-missing
```

### C++ 项目

```bash
# 配置
cmake -B build -DCMAKE_BUILD_TYPE=Debug

# 构建
cmake --build build -j$(nproc)

# 测试
ctest --test-dir build --output-on-failure
```

### JavaScript/TypeScript 项目

```bash
# 类型检查
tsc --noEmit

# Lint
eslint src/

# 测试
npm test
```

## 输入格式

Evidence Skill 接收结构化的验证请求：

```json
{
  "node_id": "eye_explore",
  "graph_id": "tg_abc123",
  "track": "fix",
  "output": {
    "summary": "分身输出摘要",
    "claims": [
      "发现了 3 个相关文件",
      "bug 位于 auth.py:42"
    ],
    "commands_executed": [
      {"cmd": "grep -r 'error' src/", "output": "..."},
      {"cmd": "pytest tests/", "output": "5 passed"}
    ]
  }
}
```

## 输出格式

```markdown
## Evidence Verification Report

**Node**: {node_id}
**Graph**: {graph_id}
**Track**: {track}
**Timestamp**: {ISO8601}

### Summary

{分身输出摘要}

### Evidence Level

**Level**: L{0-3} - {等级名称}
**Status**: PASS / FAIL / NEEDS_VERIFICATION

### Verification Steps

| Step | Command | Result | Evidence |
|------|---------|--------|----------|
| 1 | `{command}` | {result} | L{level} |
| 2 | `{command}` | {result} | L{level} |

### Evidence Records

```json
{
  "claims": [...],
  "verifications": [...],
  "level": "L2",
  "passed": true
}
```

### Issues (if any)

| Issue | Severity | Action Required |
|-------|----------|-----------------|
| {issue} | {severity} | {action} |

### Verdict

**Result**: ACCEPTED / REJECTED
**Reason**: {判定理由}
**Next Steps**: {如有需要的后续步骤}
```

## 证据记录 Schema

```json
{
  "evidence_id": "evd_xxx",
  "node_id": "eye_explore",
  "graph_id": "tg_abc123",
  "level": "L2",
  "verified_at": "ISO8601",
  "claims": [
    {
      "claim": "文件已创建",
      "evidence_type": "file_exists",
      "verification": {"command": "ls -la", "output": "..."},
      "level": "L2"
    }
  ],
  "verdict": {
    "passed": true,
    "reason": "所有声明均有 L2 级验证"
  }
}
```

## 集成点

### 与戒模块

戒模块在规则检查后调用 Evidence Skill：

```
分身输出 → 戒 (规则) → Evidence (证据) → 慧 → 识
```

### 与 on_subagent_stop Hook

SubagentStop 事件触发证据验证：

```python
# on_subagent_stop.py
evidence_result = verify_evidence(node_output, track)
if not evidence_result["passed"]:
    # 触发补充验证或拒绝
    pass
```

### 与锚点系统

高等级证据 (L2+) 可能产生锚点候选：

```python
if evidence_result["level"] >= "L2" and is_significant(claim):
    add_anchor_candidate(claim, evidence_result)
```

## 使用示例

### 验证文件创建

```python
claim = "创建了 config.py 文件"
verification = {
    "command": "ls -la config.py",
    "output": "-rw-r--r-- 1 user user 1234 config.py"
}
# → L2: 本地命令验证
```

### 验证测试通过

```python
claim = "所有测试通过"
verification = {
    "command": "pytest -v tests/",
    "output": "15 passed, 0 failed"
}
# → L2: 本地测试验证
```

### 验证端到端

```python
claim = "API 端点正常工作"
verification = {
    "command": "curl -X POST http://localhost:8000/api/login",
    "output": '{"status": "success", "token": "..."}'
}
# → L3: 集成验证
```

## 失败处理

```
验证失败流程:
├── 第1次失败 → 记录问题，请求补充验证
├── 第2次失败 → 分析根本原因
├── 第3次失败 → 停止并升级给用户
│
└── 升级步骤:
    1. 记录所有尝试
    2. 捕获错误信息
    3. 识别可能原因
    4. 向用户请求指导
```

## 配置

Evidence Skill 可通过配置调整行为：

```json
{
  "evidence": {
    "strict_mode": false,
    "default_track": "direct",
    "timeout_seconds": 30,
    "max_retries": 3,
    "l0_patterns": [
      "应该可以",
      "大概能",
      "我觉得",
      "一般来说"
    ]
  }
}
```

## 与其他 Skill 关系

```
Evidence Skill
├── 被调用者: 戒模块, on_subagent_stop Hook
├── 调用者: 各分身完成时
└── 输出消费者: 慧模块, 锚点管理器
```
