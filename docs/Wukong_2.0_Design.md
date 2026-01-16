# Wukong 2.0 详细设计文档

> **版本**: 2.0 (Draft v0.9)
> **作者**: Dennis Wang
> **状态**: 设计草案 / 可开始实现
> **目标读者**: 使用 Claude Code / 多智能体编排的工程师、维护者、贡献者

---

## 1. 背景与动机

Wukong 1.x 的核心价值是：以"六根分身 + 轨道流程 + 证据分级 + 记忆锚点"构建可复用的多智能体工作法。但在长期使用后，出现典型瓶颈：

- **流程主要"写在提示词/命令里"**：编排逻辑依赖主对话上下文，难以复用、难以恢复、难以观测。
- **线性轨道为主**：并行探索/分叉验证/回滚合并需要"人肉编排"，复杂任务收益递减。
- **记忆注入与抽取时机单点**：只在 compact/结束阶段抽取，注入常"过多或过少"，无法基于任务节点精准供给。
- **验证闭环不够"可执行"**：证据体系很强，但缺少"自动触发的验证子图"，容易停留在文字层。

**Wukong 2.0 的核心改变**：把 Wukong 从"提示词框架"提升为 **事件驱动的任务运行时（Runtime）**，并用 **TaskGraph（DAG）** 作为任务表达与编排的中心数据结构。

---

## 2. 目标与非目标

### 2.1 目标（Goals）

**G1. 任务中心化：TaskGraph（DAG）表达复杂任务**
- 轨道（Feature/Fix/Refactor）变为"模板"，底层统一用 DAG 表达。
- 原生支持并行、分叉、回滚、重试、验证子图。

**G2. 编排工程化：事件驱动 Runtime**
- 使用 hooks（或等价机制）覆盖关键生命周期：用户输入、子代理结束、compact 前、会话结束等。
- 形成"可恢复"的执行状态：中断后可续跑。

**G3. 原生多智能体：六根 Subagents Pack**
- 六根落地为可配置的 subagents：独立上下文、权限边界、工具白名单、模型选择。
- 既支持自动委派，也支持显式调用。

**G4. 质量闭环：证据分级 + 验证子图**
- 保留 L0–L3 证据等级，并将验证步骤变成可执行 DAG 节点。
- 默认带最小"实现 → 测试/复现 → 审计 → 汇总"闭环。

**G5. 可观测：日志、产物、决策可追溯**
- 统一事件日志、节点产物目录、成本/耗时指标。
- 任何关键结论应具备证据引用或可复现说明。

### 2.2 非目标（Non-goals）

- 不追求做一个完整 IDE 或完整 CI 系统；2.0 只提供"本地可用的编排运行时与规范"。
- 不强制绑定某个模型或供应商；2.0 提供抽象与默认配置。
- 不在 2.0 MVP 阶段实现复杂的全量向量检索；先做可解释的索引与规则召回。

---

## 3. 核心概念与术语

| 术语 | 定义 |
|------|------|
| **TaskGraph** | 任务图（DAG），由节点 Node 与边 Edge 组成，节点代表一个可执行单元 |
| **Node（节点）** | 具备输入、输出、状态、证据等级、执行者（subagent/skill/command）等属性 |
| **Runtime（运行时）** | 事件处理 + 状态机 + 调度器 + 产物管理 |
| **Event（事件）** | 来自 hooks 或工具回调的结构化记录，驱动状态变化 |
| **Anchor（锚点）** | 长期记忆条目（Decision/Pattern/Constraint/Metric 等），用于召回与注入 |
| **Evidence Level（证据等级）** | L0–L3（保留 1.x 的分级思想） |
| **Subagent Pack（六根）** | Eye/Ear/Nose/Tongue/Body/Mind 六类角色定义 |
| **Skill Pack** | 可复用能力包（含元数据、脚本、模板） |
| **Command** | 显式触发的快捷命令入口，用于启动某些模板或节点子图 |

---

## 4. 总体架构

### 4.1 分层架构

**A. 配置层（Project/User Scope）**
- `.claude/agents/`：六根 subagents 定义
- `.claude/skills/`：技能包（每个 skill 一个目录）
- `.claude/commands/`：显式命令入口
- `.claude/hooks/` 或 `settings.json`：hook 注册

**B. Runtime 层（Wukong Runtime）**
- 事件总线（EventBus）
- 状态机（StateMachine）
- 调度器（Scheduler）
- 产物/日志（Artifacts, Logs）
- 记忆管理（Anchors, Index）

**C. 数据层（Wukong Workspace）**
- `.wukong/taskgraph.json`：任务图定义
- `.wukong/state.json`：运行状态（可恢复）
- `.wukong/events.jsonl`：事件日志（追加写）
- `.wukong/artifacts/<session>/<node_id>/...`：节点产物
- `.wukong/anchors/*.md|json`：锚点库与索引

### 4.2 数据流概览

```
用户输入 → UserPromptSubmit 事件
    ↓
Runtime 做：意图分类 → 模板选择（轨道转 DAG）→ 召回 anchors → 写入 taskgraph/state
    ↓
调度器根据 DAG 决定执行顺序：并行节点派到各 subagent
    ↓
子代理完成 → SubagentStop 事件 → 归档产物 → 更新节点状态 → 触发下游节点
    ↓
会话结束/停止 → Stop 事件 → 汇总 → 生成 anchors 候选 → 写入库
    ↓
compact 前 → PreCompact 事件 → 抽取/去重/索引（可选）
```

---

## 5. 目录结构规范

```
repo/
  .claude/
    agents/
      eye.md
      ear.md
      nose.md
      tongue.md
      body.md
      mind.md
    skills/
      evidence/
        SKILL.md
        templates/
          evidence_report.md
      anchor_writer/
        SKILL.md
        rules/
          anchor_schema.md
      taskgraph_tools/
        SKILL.md
        scripts/
          validate_taskgraph.py
    commands/
      wukong.md
      wukong_fix.md
      wukong_feature.md
      wukong_refactor.md
      wukong_resume.md
    hooks/
      on_user_prompt_submit.py
      on_subagent_stop.py
      on_stop.py
      on_precompact.py

  .wukong/
    taskgraph.json
    state.json
    events.jsonl
    artifacts/
    anchors/
      anchors.md
      index.json
    runtime/
      README.md
      schema/
        taskgraph.schema.json
        event.schema.json
```

---

## 6. TaskGraph 设计

### 6.1 Node Schema（建议字段）

```json
{
  "id": "N-010",
  "title": "Implement fix for crash in decoder",
  "role": "body",
  "executor": {
    "type": "subagent",
    "name": "body"
  },
  "inputs": {
    "files": ["src/decoder.cc"],
    "context_refs": ["A-2026-0012"],
    "upstream_outputs": ["N-005.outputs.patch"]
  },
  "constraints": {
    "allowed_tools": ["bash", "edit", "read"],
    "time_budget_sec": 1200
  },
  "quality": {
    "evidence_level_required": "L2",
    "checklist": ["tests_added", "repro_steps", "risk_assessment"]
  },
  "status": "pending",
  "retries": 0,
  "outputs": {
    "artifacts_dir": ".wukong/artifacts/S-xxx/N-010/",
    "summary": "",
    "patch_files": [],
    "evidence": []
  },
  "metrics": {
    "cost_estimate": 0.2,
    "actual_cost": 0.0,
    "started_at": null,
    "finished_at": null
  }
}
```

### 6.2 Edge Schema

```json
{ "from": "N-010", "to": "N-020", "condition": "on_success" }
```

支持的 condition：
- `on_success` / `on_failure` / `always`
- 可扩展：`predicate:<expr>`（MVP 可不实现）

### 6.3 状态机

**节点状态**：
- `pending` → `running` → `done`
- `running` → `failed`（可重试）
- `blocked`（依赖未满足 / 需要人工输入）

**Graph 状态**：
- `created` / `running` / `paused` / `completed` / `aborted`

---

## 7. Runtime 设计

### 7.1 组件

**EventBus**
- 接收 hooks 发来的结构化事件（写 `events.jsonl`）
- 对外提供订阅/分发（MVP 可直接轮询 events 文件）

**StateMachine**
- 根据事件更新 `.wukong/state.json` 与 `.wukong/taskgraph.json`
- 维护 session、当前 graph、节点状态、重试次数等

**Scheduler**
- 读取 DAG，找出可运行节点（所有依赖 done）
- 根据节点 role/executor 把任务派给对应 subagent 或 skill/command
- 支持并行队列（MVP：并行="一次启动多个 subagent"，或"分批启动"）

**ArtifactManager**
- 为每个 session/node 创建产物目录
- 保存：subagent 输出、执行日志、patch、测试输出、证据报告

**MemoryManager**
- anchors 召回：关键词/标签/最近策略（MVP 先做可解释召回）
- anchors 抽取：Stop/PreCompact 时生成候选 → 人工或自动确认写入

### 7.2 事件模型（Event Schema）

```json
{
  "event_id": "E-000123",
  "type": "SubagentStop",
  "timestamp": "2026-01-16T21:35:22-08:00",
  "session_id": "S-20260116-001",
  "node_id": "N-010",
  "payload": {
    "agent": "body",
    "result": "success",
    "summary": "Fixed null deref by guarding ...",
    "artifacts": ["patch.diff", "test.log"],
    "evidence_level": "L2"
  }
}
```

**事件类型（MVP 必需）**：
- `UserPromptSubmit`
- `SubagentStop`
- `Stop`
- `PreCompact`（可选但建议保留）

---

## 8. 六根 Subagents Pack（2.0 规范）

每个 subagent 文件建议包含：
- `name` / `description` / `responsibilities`
- `allowed_tools`（白名单）
- `default_evidence_level`（输出目标）
- `output_format`（统一结构：Summary / Steps / Evidence / Risks / Next）

### 8.1 角色职责

| 角色 | 职责 | 工具权限 |
|------|------|----------|
| **Eye（眼）** | 观察/检索/阅读 | read、grep（禁写） |
| **Ear（耳）** | 需求澄清/对齐 | 只读/对话（禁修改） |
| **Nose（鼻）** | 审计/安全/规范 | read + 分析（禁写） |
| **Tongue（舌）** | 表达/文档/测试与复现 | 可写测试/文档；可跑测试 |
| **Body（身）** | 动手实现/修复/重构 | edit/bash/read（严格白名单） |
| **Mind（意）** | 架构/策略/全局权衡 | read + 写设计文档（不直接实现） |

---

## 9. Skills 2.0 设计（能力包）

### 9.1 Evidence Skill（证据报告标准化）

**目标**：把"证据等级"从口头描述升级为可复用的报告模板与规则。

**产出**：
- `evidence_report.md` 模板
- 证据等级判定规则（什么算 L1/L2/L3）
- 自动检查脚本（可选）

**建议输出结构**：
```markdown
## Summary
(1–3 行)

## Repro Steps
(可复制)

## Observations
(引用文件/行号/日志片段)

## Verification
(测试命令与结果)

## Risk & Rollback
(风险/回滚方式)

## Evidence Level
(给出理由)
```

### 9.2 Anchor Writer Skill（锚点写入治理）

**目标**：减少"记忆污染"，让锚点写入有门槛、有格式、有去重。

**产出**：
- `anchor_schema.md`（字段：type/tags/context/decision/why/when/expiry）
- 去重规则：同一主题的 anchors 合并策略
- 候选生成策略：Stop 时产生候选，默认进入 `anchors_candidates.md`

### 9.3 TaskGraph Tools Skill（图校验与可视化）

**目标**：把 TaskGraph 变成"可验证资产"。

**产出**：
- `validate_taskgraph.py`：schema 校验、检测环、检测孤儿节点
- `render_taskgraph.md`（可选）：输出 Mermaid 图便于读

---

## 10. Commands（显式入口）设计

**建议命令集（MVP）**：
- `/wukong`：智能选择轨道/模板并生成 DAG
- `/wukong_fix`：生成 Fix 模板 DAG（含验证子图）
- `/wukong_feature`：生成 Feature 模板 DAG（含并行探索节点）
- `/wukong_refactor`：生成 Refactor 模板 DAG（含风险审计）
- `/wukong_resume`：从 `.wukong/state.json` 恢复继续跑

**命令职责**：只做"创建/恢复/切换图"，不承载复杂编排逻辑（编排逻辑放 Runtime）。

---

## 11. 验证闭环（Verification 2.0）

### 11.1 默认验证子图（建议）

以 Fix 为例，一个最小闭环 DAG：

```
Ear (N-001) → Eye (N-010) → Body (N-020) → Tongue (N-030) → Nose (N-040) → Mind (N-050)
  澄清标准      定位问题       实现修复        复现+测试        风险审计       汇总决策
```

### 11.2 证据等级门槛

- **Fix** 默认至少 L2：需要"可复现步骤 + 测试或日志证据"
- **高风险模块**（性能/并发/安全）可要求 L3：需要实际跑过测试、给出输出摘要、或可引用 CI 结果

---

## 12. 记忆与锚点（Anchors）设计

### 12.1 Anchor 类型

| 类型 | 说明 |
|------|------|
| **D（Decision）** | 架构/策略决策及理由 |
| **C（Constraint）** | 不可违背约束（API、性能、平台、合规） |
| **P（Pattern）** | 可复用模式（如何调试/如何验证/如何组织代码） |
| **M（Metric）** | 度量与门槛（性能预算、质量门槛） |

### 12.2 写入流程（治理）

1. Stop 时：生成 anchors 候选（自动）→ 进入 candidates 文件
2. 手动确认或 Nose/Mind 审核后：写入 `anchors.md`（正式库）
3. 去重：同一 topic 只保留最新或合并版本
4. 过期机制（可选）：某些 anchors 标记 expiry 或 "last_validated"

### 12.3 召回策略（MVP）

- 关键词匹配（title/tags）
- 最近 10 条 Decision 优先
- 与当前任务文件路径相关的 anchors 优先（按路径标签）

---

## 13. 可观测性与产物管理

### 13.1 事件日志

`.wukong/events.jsonl`：每行一个事件（便于 grep/增量处理）

### 13.2 产物归档

- 每个 session 一个目录：`.wukong/artifacts/<session_id>/`
- 每个节点一个目录：`.../<node_id>/`
- 保存：subagent 输出原文、patch、测试输出、证据报告、关键引用索引

### 13.3 指标（可选）

- 节点耗时（started/finished）
- 成本（估算/实际）
- 失败率（重试次数）
- 证据等级分布

---

## 14. 安全与权限边界

- **工具白名单是第一道边界**：Body 允许写/跑；Nose 多为只读；Ear 不修改
- **产物目录隔离**：避免把敏感信息扩散到主对话或非必要节点
- **最小权限原则**：能只读就只读；能不 bash 就不 bash
- **审计节点（Nose）默认强制**：在高风险轨道中必须执行

---

## 15. 实施路线图（按阶段）

### 15.1 兼容策略

- 1.x 的轨道命令保留为 2.0 的模板入口（命令名可不变）
- anchors 文件与抽取脚本可复用，但写入流程升级为"候选→确认→入库"

### 15.2 Phase 0: 数据结构与目录落地

**目标**: 建立 2.0 的数据基础设施

**交付物**:
- `.wukong/runtime/schema/` - TaskGraph/Node/Event JSON Schema
- `.wukong/runtime/templates/` - fix/feature/direct 轨道 DAG 模板
- `.wukong/` 运行时数据目录 (taskgraph.json, state.json, events.jsonl, artifacts/)

**验收标准**:
- [ ] Schema 文件可通过 JSON Schema 校验工具验证
- [ ] 模板文件符合 Schema 定义
- [ ] 目录结构与设计文档一致

### 15.3 Phase 1: 六根 Subagents 原生化

**目标**: 将六根分身落地为 Claude 原生 subagents

**交付物**:
- `.claude/agents/` 下 6 个 agent 文件 (eye/ear/nose/tongue/body/mind.md)
- 每个 agent 包含: YAML frontmatter + 职责 + 输出格式 + Do/Don't

**验收标准**:
- [ ] 6 个 agent 文件创建完成
- [ ] 每个 agent 有明确的工具白名单
- [ ] 输出格式统一 (Summary/Steps/Evidence/Risks/Next)

### 15.4 Phase 2: Runtime MVP (事件驱动)

**目标**: 实现最小可用的事件驱动运行时

**交付物**:
- `event_bus.py` - 事件总线
- `state_manager.py` - 状态管理
- `scheduler.py` - 调度器
- `artifact_manager.py` - 产物管理

**验收标准**:
- [ ] 能加载 TaskGraph 模板并实例化
- [ ] 能按 DAG 顺序调度节点
- [ ] SubagentStop 事件能触发下游节点
- [ ] 产物正确归档到 artifacts/

### 15.5 Phase 3: 端到端集成 (Fix Track)

**目标**: 跑通一条完整的 Fix 轨道

**交付物**:
- `/wukong_fix` 命令更新
- Fix Track DAG 最小版: Eye → Body → Tongue

**验收标准**:
- [ ] `/wukong_fix` 能生成 DAG 并启动调度
- [ ] 每个节点产物正确归档
- [ ] 最终输出包含 L2 级别证据

### 15.6 Phase 4: 验证闭环与 Anchors

**目标**: 完善验证体系和记忆管理

**交付物**:
- Evidence Skill (SKILL.md + templates)
- Anchor 管理 (anchors.md, candidates.md, index.json)
- Hooks 集成 (on_subagent_stop.py, on_stop.py)

**验收标准**:
- [ ] 每个节点输出符合 Evidence 格式
- [ ] Stop 时自动生成 anchor 候选
- [ ] anchor 召回功能可用

### 15.7 Phase 5: 完整轨道与优化

**目标**: 补齐所有轨道，优化体验

**交付物**:
- Feature Track DAG: [Ear+Eye] → [Mind] → [Body] → [Tongue+Nose]
- Refactor Track DAG: [Eye] → [Mind] → [Body] → [Nose+Tongue]
- `/wukong_resume` 命令
- 可观测性增强 (成本/耗时/重试统计)

**验收标准**:
- [ ] 3 条轨道都能端到端运行
- [ ] 中断后能恢复继续
- [ ] 有基本的指标输出

---

## 16. MVP 验收标准（Definition of Done）

Wukong 2.0 MVP 被认为完成，当满足：

- [ ] `/wukong_fix` 能生成一个 DAG（至少 5 个节点）并落盘 `taskgraph.json`
- [ ] Runtime 能根据 DAG 调度至少 3 个 subagents 节点（串行即可）
- [ ] 子代理结束后会触发 SubagentStop，并把结果写入节点产物目录
- [ ] Stop 会生成 session summary + anchors candidates
- [ ] 能从 `state.json` 恢复（resume）继续执行未完成节点
- [ ] 至少一条链路产出 L2 证据报告（模板化）

---

## 17. 风险与开放问题

| 风险 | 说明 |
|------|------|
| **R1** | hooks 运行环境差异：不同终端/系统对 hook 脚本执行环境要求不同 |
| **R2** | 并行执行的控制：并行 subagents 可能导致输出争用与状态竞争 |
| **R3** | 记忆注入过度：anchors 召回若不克制，会再次回到上下文膨胀 |
| **R4** | 证据等级主观性：需要一套可操作的判定规则 |

---

## 18. 附录：默认输出格式规范

建议所有 subagents 遵守：

```markdown
## Summary
- ...

## Steps / Findings
1. ...
2. ...

## Evidence
- Level: L?
- Repro:
  - command:
  - result:
- References:
  - file:line
  - log snippet

## Risks / Caveats
- ...

## Next
- ...
```

---

*文档版本: v0.9 Draft | 最后更新: 2026-01-16*
