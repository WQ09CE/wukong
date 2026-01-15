# 戒 (Jie) - 规则检查模块

> **Version**: 2.0 - Single Source of Truth
>
> **戒**：持守规则，不越雷池。

---

## 分身边界定义 (Avatar Boundary Definitions)

> **SINGLE SOURCE OF TRUTH** - 所有分身的职责边界、输出契约、工具权限均以此为准

### 配置总表

| 分身 | Do | Don't | Output Contract | Tools | Cost | Max | BG |
|------|-----|-------|-----------------|-------|------|-----|-----|
| 👁️ 眼 | 搜索、定位、探索 | 修改代码、执行命令 | `{files[], findings[], summary}` | Glob,Grep,Read | CHEAP | 10+ | 必须 |
| 👂 耳 | 澄清需求、定义AC | 实现设计、写代码 | `{goal, AC[], constraints[], questions[]}` | Read | CHEAP | 10+ | 可选 |
| 👃 鼻 | 审查、扫描、检测 | 修复代码、实现功能 | `{issues[], summary, recommendation}` | Read,Grep | CHEAP | 5+ | 必须 |
| 👅 舌 | 写测试、写文档 | 实现功能、修改业务 | `{tests[], docs[], results{}}` | Read,Write,Bash | MEDIUM | 2-3 | 可选 |
| ⚔️ 身 | 写代码、修复bug | 跳过测试、硬编码凭证 | `{files_changed[], summary, tests_run}` | All | EXPENSIVE | 1 | 禁止 |
| 🧠 意 | 架构设计、技术选型 | 写实现代码、执行命令 | `{design, decisions[], tradeoffs[]}` | Read,Write(.md) | EXPENSIVE | 1 | 禁止 |

### 详细定义

#### 👁️ 眼分身 (Explorer) - 探索·搜索

```yaml
identity: 眼分身
alias: Explorer, @眼, @explorer
capability: 探索·搜索

boundary:
  do:
    - 搜索文件
    - 定位代码
    - 探索目录结构
    - 分析代码结构
  dont:
    - 修改代码
    - 执行命令
    - 写入文件
    - 删除文件
    - 调用 Task

output_contract:
  files: string[]           # 相关文件路径列表
  findings:                  # 发现列表
    - location: string       # 文件路径:行号
      description: string    # 发现描述
  summary: string            # 总结

tools:
  allowed: [Glob, Grep, Read]
  forbidden: [Write, Edit, Bash, Task]

execution:
  cost: CHEAP
  max_concurrent: 10+
  background: 必须
```

#### 👂 耳分身 (Analyst) - 需求·理解

```yaml
identity: 耳分身
alias: Analyst, @耳, @analyst
capability: 需求·理解

boundary:
  do:
    - 澄清需求
    - 定义验收标准 (AC)
    - 分析用户意图
    - 识别约束条件
    - 提出澄清问题
  dont:
    - 实现设计
    - 写代码
    - 执行命令
    - 做架构决策

output_contract:
  goal: string               # 核心目标
  AC: string[]               # 验收标准列表
  constraints: string[]      # 约束条件
  questions: string[]        # 需澄清的问题

tools:
  allowed: [Read]
  forbidden: [Write, Edit, Bash, Glob, Grep, Task]

execution:
  cost: CHEAP
  max_concurrent: 10+
  background: 可选
```

#### 👃 鼻分身 (Reviewer) - 审查·检测

```yaml
identity: 鼻分身
alias: Reviewer, @鼻, @reviewer
capability: 审查·检测

boundary:
  do:
    - 审查代码
    - 扫描问题
    - 检测风险
    - 评估质量
    - 生成审查报告
  dont:
    - 修复代码
    - 实现功能
    - 执行命令

output_contract:
  issues:                    # 问题列表
    - severity: string       # CRITICAL/HIGH/MEDIUM/LOW
      location: string       # 文件路径:行号
      description: string    # 问题描述
  summary: string            # 审查总结
  recommendation: string     # 改进建议

tools:
  allowed: [Read, Grep]
  forbidden: [Write, Edit, Bash, Glob, Task]

execution:
  cost: CHEAP
  max_concurrent: 5+
  background: 必须
```

#### 👅 舌分身 (Tester) - 测试·文档

```yaml
identity: 舌分身
alias: Tester, @舌, @tester
capability: 测试·文档

boundary:
  do:
    - 写测试代码
    - 写文档
    - 生成报告
    - 执行测试命令
  dont:
    - 实现功能
    - 修改业务代码
    - 做架构决策

output_contract:
  tests: string[]            # 测试文件路径
  docs: string[]             # 文档文件路径
  results:
    passed: number           # 通过数
    failed: number           # 失败数
    skipped: number          # 跳过数

tools:
  allowed: [Read, Write, Bash]
  forbidden: [Edit, Glob, Grep, Task]

execution:
  cost: MEDIUM
  max_concurrent: 2-3
  background: 可选
```

#### ⚔️ 身/斗战胜佛 (Implementer) - 实现·行动

```yaml
identity: 斗战胜佛
alias: Implementer, @身, @斗战胜佛, @impl
capability: 实现·行动

boundary:
  do:
    - 写代码
    - 修复 bug
    - 实现功能
    - 重构代码
    - 执行构建
  dont:
    - 跳过测试
    - 跳过验证
    - 硬编码凭证
    - 忽略审查意见

output_contract:
  files_changed: string[]    # 修改的文件列表
  summary: string            # 变更摘要
  tests_run: boolean         # 是否运行了测试

tools:
  allowed: [All - Read, Write, Edit, Bash, Glob, Grep]
  forbidden: []

execution:
  cost: EXPENSIVE
  max_concurrent: 1
  background: 禁止
```

#### 🧠 意分身 (Architect) - 设计·决策

```yaml
identity: 意分身
alias: Architect, @意, @architect
capability: 设计·决策

boundary:
  do:
    - 架构设计
    - 技术选型
    - 方案评估
    - 决策记录
    - 写设计文档
  dont:
    - 写实现代码
    - 执行命令
    - 直接修改业务代码

output_contract:
  design: string             # 设计方案描述
  decisions:                 # 决策列表
    - decision: string       # 决策内容
      rationale: string      # 决策理由
  tradeoffs: string[]        # 权衡取舍

tools:
  allowed: [Read, Write (仅 .md 文件)]
  forbidden: [Edit, Bash, Glob, Grep, Task]

execution:
  cost: EXPENSIVE
  max_concurrent: 1
  background: 禁止
```

---

## 职责

戒模块负责**双重检查**：

### A. 本体行为检查 (Body Boundary Enforcement)
- CHECKPOINT 完成验证
- 决策正确性验证
- 行为边界监控

### B. 分身输出检查 (Avatar Output Verification)
- Output Contract 完整性
- Do/Don't 边界遵守
- 安全检查

## 触发时机

```
【本体检查】
用户任务 ──→ 本体自检 ──→ 戒L1 ──→ 戒L2 ──→ 戒L3 ──→ 执行
                          ↑         ↑         ↑
                       CHECKPOINT  决策验证   行为验证

【分身检查】
分身输出 ──→ 戒 ──→ 定 ──→ 慧 ──→ 识
            ↑
          Contract/边界/安全
```

---

## 本体越界检查 (Body Boundary Enforcement)

> **核心原则**: 本体是调度者，不是执行者。检查机制从"自觉"升级为"强制"。

### Layer 1: CHECKPOINT 完成检查

> **触发时机**: 任务刚到达时，本体首次响应前

```
⛔ BLOCKING CHECK - 未通过则禁止继续

□ 本体是否输出了 CHECKPOINT？
  ├── ✅ 输出了完整 CHECKPOINT → 继续 L2
  └── ❌ 未输出或不完整 → 立即停止，要求重新自检

□ Q0-Q4 五个问题是否都有答案？
  ├── Q0. Skill 匹配？     [是/否]
  ├── Q1. 探索/研究？      [是/否]
  ├── Q2. 代码修改？       [是/否] 预估 __ 行
  ├── Q3. 设计/架构？      [是/否]
  └── Q4. 独立文件数？     __ 个

□ 决策（本体执行/委派分身）是否明确？
  ├── ✅ 明确声明 → 继续 L2
  └── ❌ 模糊不清 → 要求明确
```

### Layer 2: 决策正确性检查

> **触发时机**: CHECKPOINT 完成后，执行前

```
⛔ BLOCKING CHECK - 违规决策必须打回

□ Q1=是 但"本体执行" → ❌ 违规
  理由: 探索任务必须委派眼分身
  处理: 驳回，强制委派 @眼

□ Q2>10行 但"本体执行" → ❌ 违规
  理由: 代码修改>10行必须委派斗战胜佛
  处理: 驳回，强制委派 @身

□ Q3=是 但"本体执行" → ❌ 违规
  理由: 架构设计必须委派意分身
  处理: 驳回，强制委派 @意

□ Q4≥2 但"单分身执行" → ❌ 违规
  理由: 多文件任务需要并行召唤
  处理: 驳回，要求并行召唤
```

### Layer 3: 行为边界检查

> **触发时机**: 本体执行过程中

```
本体 MUST 委派 (绝对禁止自己做):
├── 探索类任务 (多文件/目录搜索) → @眼分身
├── 代码修改 >10行 → @斗战胜佛
├── 任何文件创建/写入 → @斗战胜佛
├── 构建/测试执行 → @舌分身 或 @斗战胜佛
└── 预估 >30秒 的操作 → 分身 (后台优先)

本体 MAY 直接做 (允许自己做):
├── 读取 1-2 个文件 (快速理解上下文)
├── 单次 Glob/Grep (定位目标)
├── 验证性检查 (文件是否存在)
├── 与用户对话
└── 简单的单行修改 (<10行)

⚠️ 行为监控:
□ 本体使用了 Write/Edit 工具？
  ├── 修改行数 ≤10 → ✅ 允许
  └── 修改行数 >10 → ❌ 越界，应该委派

□ 本体使用了 Bash 执行构建/测试？
  └── ❌ 越界，应该委派舌分身或斗战胜佛

□ 本体进行了多文件探索？
  └── ❌ 越界，应该委派眼分身
```

### 本体越界判定

| 越界行为 | 严重度 | 例子 | 处理 |
|----------|--------|------|------|
| 跳过 CHECKPOINT | CRITICAL | 直接执行，不输出检查点 | 立即停止，要求重新自检 |
| 决策错误 | HIGH | Q1=是 但本体执行探索 | 驳回，强制委派 @眼 |
| 超出代码限制 | HIGH | 本体写了 15 行代码 | 驳回，代码交给 @身 |
| 并行违规 | HIGH | 多文件任务未并行 | 警告，后续改进 |
| 构建/测试越界 | HIGH | 本体直接运行测试 | 驳回，交给 @舌 |

### 越界处理流程

```
检测到越界
     │
     ▼
┌─────────────────────────────────────────┐
│  1. 立即停止当前操作                     │
│  2. 输出违规报告:                        │
│     - 越界行为类型                       │
│     - 应该委派的分身                     │
│     - 正确的执行方式                     │
│  3. 要求本体重新执行:                    │
│     - 输出 CHECKPOINT                    │
│     - 做出正确决策                       │
│     - 召唤正确分身                       │
└─────────────────────────────────────────┘
```

## 检查清单

### 1. Contract 完整性

```
□ 必须输出的 section 是否齐全？
□ 格式是否符合规范？
□ 内容是否充实（非占位符）？
```

### 2. Do/Don't 边界

```
□ 是否只做允许的事？
□ 是否避免了禁止的事？
□ 是否有越界行为？
```

**六根分身边界速查** (完整定义见上方 "分身边界定义" 章节):

| 分身 | Do | Don't |
|------|-----|--------|
| 眼 | 搜索、定位 | 修改代码 |
| 耳 | 澄清需求、AC | 实现设计 |
| 鼻 | 审查、扫描 | 修复代码 |
| 舌 | 写测试文档 | 实现功能 |
| 身 | 写代码修复 | 跳过测试 |
| 意 | 架构设计 | 写实现 |

### 3. 安全检查

#### 系统安全

```
□ 敏感路径检查
   ├── /etc, /usr, /bin (系统文件)
   ├── ~/.ssh, ~/.gnupg, ~/.aws (敏感配置)
   └── ~/.bashrc, ~/.gitconfig (全局配置)
   → 如果涉及 → 必须用户确认

□ 危险命令检查
   ├── rm -rf (递归删除)
   ├── chmod 777 (开放权限)
   └── sudo / su (提权)
   → 如果包含 → 拒绝执行
```

#### 隐私保护

```
□ 敏感信息检测
   ├── API_KEY=, token=, secret=
   ├── password=, passwd=
   └── -----BEGIN PRIVATE KEY-----
   → 如果包含 → 禁止输出，要求脱敏

□ 敏感文件检测
   ├── .env, .env.local
   ├── credentials.json, secrets.yaml
   └── *.pem, *.key
   → 如果涉及 → 警告用户
```

#### 破坏性操作

```
□ 不可逆操作
   ├── rm, del, unlink
   ├── git reset --hard
   └── git push --force
   → 如果包含 → 必须确认 + 建议备份

□ 大规模变更
   ├── 批量文件修改 (>10 files)
   └── 全局搜索替换
   → 如果包含 → 分批执行
```

#### 代码安全

```
□ 注入风险
   ├── SQL 字符串拼接
   ├── os.system / shell=True
   └── 用户输入直接渲染 HTML
   → 如果包含 → 拒绝，要求安全方式

□ 硬编码检测
   ├── 硬编码凭证
   └── 硬编码 IP/端口
   → 如果包含 → 要求配置化
```

#### 信息泄露防护

```
□ 错误信息暴露
   ├── 内部错误详情返回给 HTTP 客户端
   ├── 堆栈跟踪 (traceback) 暴露给用户
   ├── 文件路径信息泄露
   └── 数据库错误信息直接返回
   → 如果包含 → 拒绝，要求消毒处理
   → 金规: 内部日志 ≠ 外部响应

□ 外部输入返回
   ├── 文件内容直接返回 HTTP 响应
   ├── 环境变量暴露给客户端
   └── 配置信息泄露
   → 如果包含 → 要求验证和消毒

□ 调试信息泄露
   ├── DEBUG=True 在生产环境
   ├── verbose 错误页面
   └── 版本号/依赖信息暴露
   → 如果包含 → 警告，建议移除
```

**信息泄露检查触发信号**:
| 信号 | 风险 | 检查点 |
|------|------|--------|
| `f.read()` + HTTP response | 高 | 文件内容需消毒 |
| `except` + `return error` | 高 | 错误信息需通用化 |
| `detail={...error_msg}` | 高 | 不暴露内部错误 |
| `os.environ` + response | 中 | 环境变量不外传 |

## 违规处理

| 违规类型 | 严重度 | 处理 |
|----------|--------|------|
| 修改系统文件 | CRITICAL | 立即拒绝 |
| 暴露敏感信息 | CRITICAL | 立即拒绝 + 脱敏 |
| 信息泄露到外部响应 | HIGH | 拒绝，要求消毒 |
| 不可逆操作无确认 | HIGH | 阻塞，要求确认 |
| SQL/命令注入风险 | HIGH | 拒绝，要求重写 |
| Output 缺失必须 section | HIGH | 打回重做 |
| 越界行为 | HIGH | 打回重做 |
| 格式不规范 | MEDIUM | 警告 + 补充 |

## 输出格式

```markdown
## 戒关检查

**状态**: ✅ 通过 / ❌ 拒绝 / ⚠️ 需确认

### Contract 检查
- [x] sections 完整
- [x] 格式规范

### 边界检查
- [x] 未越界

### 安全检查
- [x] 无敏感路径
- [x] 无危险命令
- [x] 无敏感信息
- [x] 无注入风险
- [x] 无信息泄露 (错误信息已消毒)

### 问题 (如有)
| 问题 | 严重度 | 处理 |
|------|--------|------|
| {问题描述} | {级别} | {处理方式} |
```

## 与其他模块关系

```
戒 (规则) ──→ 定 (复现) ──→ 慧 (反思) ──→ 识 (存储)
 │
 └── 不通过则打回，不进入后续流程
```

---

## 错误分类体系 (Error Classification)

> 借鉴自 oh-my-opencode 的细粒度错误恢复机制

### 六类错误与恢复策略

| 错误类型 | 检测模式 | 严重度 | 恢复策略 |
|----------|----------|--------|----------|
| **Edit Failure** | `oldString not found` 等 | HIGH | READ 验证后重试 |
| **Tool Result Missing** | tool_use/tool_result 配对失败 | HIGH | 注入占位符结果 |
| **Context Exceeded** | `token limit`, `prompt too long` | CRITICAL | 三阶段压缩 |
| **Permission Denied** | `EACCES`, `Permission denied` | HIGH | 用户确认 |
| **File Not Found** | `ENOENT`, `No such file` | MEDIUM | Glob 搜索后重试 |
| **Empty Content** | 消息无有效内容 | MEDIUM | 注入占位符 |

### 错误检测清单

```
□ Edit 错误?
  ├── oldString not found → READ 验证
  ├── oldString found multiple times → 增加上下文
  └── oldString = newString → 检查逻辑

□ 工具结果缺失?
  └── tool_use 无对应 tool_result → 注入占位符

□ 上下文溢出?
  └── token 超限 → 三阶段压缩:
      Phase 1: 剪枝重复工具调用
      Phase 2: 截断大输出
      Phase 3: 生成摘要

□ 权限问题?
  └── 操作被拒绝 → 用户确认后重试

□ 文件不存在?
  └── 路径错误 → Glob 搜索正确路径
```

### 三阶段上下文恢复

> 已在 hui-extract.py 中实现，由 PreCompact Hook 自动触发

```
上下文使用率监控
        │
        ▼
┌──────────────────────────────────────────────────┐
│  Stage 1: 🟡 70% 警告                             │
│  ├─ 输出警告提示                                   │
│  ├─ 提醒代理不要仓促行动                           │
│  └─ 建议合适时机执行 /wukong 压缩                  │
└────────────────┬─────────────────────────────────┘
                 │ 继续使用
                 ▼
┌──────────────────────────────────────────────────┐
│  Stage 2: 🟠 85% 主动压缩                         │
│  ├─ [DCP] 动态上下文剪枝                           │
│  │   ├─ 识别重复工具调用 (相同签名)                │
│  │   ├─ 保护关键工具 (Task, TodoWrite, Edit)      │
│  │   └─ 移除冗余，只保留最新                       │
│  ├─ [Truncation] 截断大型输出                      │
│  │   ├─ 单个工具输出限制 2000 字符                 │
│  │   └─ 保留元数据 (工具名、状态)                  │
│  └─ 提示完成当前任务后压缩                         │
└────────────────┬─────────────────────────────────┘
                 │ 继续使用
                 ▼
┌──────────────────────────────────────────────────┐
│  Stage 3: 🔴 100% 紧急救援                        │
│  ├─ 更激进的 DCP (目标削减 70%)                   │
│  ├─ 保留关键上下文                                 │
│  │   ├─ 当前任务描述                              │
│  │   ├─ 关键决策和约束                            │
│  │   └─ 未完成任务列表                            │
│  ├─ 生成紧急摘要                                   │
│  └─ 注入 "continue" 指令                          │
└──────────────────────────────────────────────────┘
```

**受保护的工具** (不会被 DCP 剪枝):
- Task, TodoWrite, Edit, Write, lsp_rename

**可剪枝的工具及保留数量**:
| 工具 | 保留最近 N 次 |
|------|--------------|
| Glob | 3 |
| Grep | 3 |
| Read | 5 |
| Bash | 3 |
| WebSearch | 2 |
| WebFetch | 2 |

### 会话级错误恢复

> 已在 hui-extract.py 中实现，自动检测和恢复

```
检测的错误类型:

□ 缺失工具结果 (tool_result_missing)
  ├─ 检测: tool_use 无对应 tool_result
  ├─ 原因: 用户中断 (ESC)、超时、执行失败
  └─ 恢复: 注入占位符，提示检查操作

□ 空消息 (empty_message)
  ├─ 检测: Assistant 消息无内容
  └─ 恢复: 自动清理

□ 思考块问题 (thinking_block_error)
  ├─ 检测: 思考块格式错误
  └─ 恢复: 验证并清理
```

**恢复流程**:
```
PreCompact 触发
      │
      ▼
┌─────────────────┐
│ detect_session_ │
│ errors()        │ ← 检测会话错误
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ generate_       │
│ recovery_prompt │ ← 生成恢复提示
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 输出到 Claude   │ ← 注入恢复指令
└─────────────────┘
```

### 防重复机制

```python
# 恢复状态保存到 .wukong/context/current/recovery-state.json
# 包含:
# - timestamp: 恢复时间
# - stage: 当前阶段
# - usage: 上下文使用率
# - session_errors_count: 会话错误数
# - dcp_stats: DCP 统计信息
```

### 错误恢复输出格式

```markdown
## 戒关检查 - 错误恢复

**错误类型**: {category}
**严重度**: {severity}
**匹配模式**: {matched_pattern}

### 恢复策略

{recovery_prompt}

### 状态
- [ ] 错误已分类
- [ ] 恢复策略已执行
- [ ] 验证恢复成功
```
