# Wukong Multi-Agent System (悟空多智能体系统)

**Version:** 1.0
**Purpose:** 六根分身多智能体编排系统

## Overview

Wukong 是一个基于"六根"概念的多智能体系统。本体(主控)负责调度，六个专业分身负责执行。

**核心原则:** 本体是调度者，不是执行者。

## Agent Discovery

Claude Code 通过 Task tool 调用分身，使用以下语法：

```
Task(subagent_type="eye", prompt="...")   # 眼分身
Task(subagent_type="body", prompt="...")  # 身分身/斗战胜佛
```

## Available Agents (六根分身 + 规划器)

| Agent | 中文名 | Model | Cost | Background | Purpose |
|-------|--------|-------|------|------------|---------|
| `eye` | 眼分身 | Sonnet | CHEAP | Required | 探索·搜索·观察 |
| `ear` | 耳分身 | Sonnet | CHEAP | Optional | 需求·理解·澄清 |
| `nose` | 鼻分身 | Sonnet | CHEAP | Required | 审查·检测·安全 |
| `tongue` | 舌分身 | Sonnet | MEDIUM | Optional | 测试·文档·验证 |
| `body` | 斗战胜佛 | Opus | EXPENSIVE | Forbidden | 实现·修复·重构 |
| `mind` | 意分身 | Opus | EXPENSIVE | Forbidden | 设计·架构·决策 |
| `planner` | 规划分身 | Haiku | CHEAP | Optional | L1路由·任务规划 |

### Planner Agent (L1 智能路由)

Planner 是一个特殊的轻量级 agent，用于 L1 路由层：

- **触发时机**: L0 规则路由返回 `confidence < 0.7` 时
- **职责**: 分析任务，返回 track + phases + complexity
- **模型**: Haiku (快速、低成本)
- **输入**: `TASK: {任务描述}` + `L0_RESULT: {规则匹配结果}`
- **输出**: JSON 格式的执行计划

```
L0 规则路由 → confidence < 0.7 → Planner (Haiku) → 执行计划
            → confidence >= 0.7 → 直接使用 L0 结果
```

### Agent Selection Guide

| Task Type | Best Agent | @Syntax |
|-----------|------------|---------|
| 探索代码库、搜索文件 | `eye` | `@眼` / `@explorer` |
| 分析需求、澄清意图 | `ear` | `@耳` / `@analyst` |
| 代码审查、安全扫描 | `nose` | `@鼻` / `@reviewer` |
| 编写测试、生成文档 | `tongue` | `@舌` / `@tester` |
| 实现功能、修复 Bug | `body` | `@身` / `@impl` |
| 架构设计、技术决策 | `mind` | `@意` / `@architect` |

### Agent Boundaries (Critical)

每个分身都有严格的职责边界：

| Agent | CAN DO | CANNOT DO |
|-------|--------|-----------|
| `eye` | Read, Glob, Grep, WebSearch | Write, Edit, Bash, Task |
| `ear` | Read | Write, Edit, Bash, Glob, Grep, Task |
| `nose` | Read, Glob, Grep | Write, Edit, Bash, Task |
| `tongue` | Read, Write (tests/docs only), Bash, Glob | Edit, Task |
| `body` | Read, Write, Edit, Bash, Glob, Grep | Task |
| `mind` | Read, Write (.md only), Glob, Grep | Edit, Bash, Task |

## Tracks (执行轨道)

根据任务类型自动选择轨道：

| Track | Trigger Keywords | DAG Flow |
|-------|------------------|----------|
| **feature** | add, create, new, implement | [ear+eye] → [mind] → [body] → [tongue+nose] |
| **fix** | fix, bug, error, crash | [eye+nose] → [body] → [tongue] |
| **refactor** | refactor, clean, optimize | [eye] → [mind] → [body] → [nose+tongue] |
| **research** | explore, research, understand | [eye] |
| **direct** | simple, single-line | (本体直接执行) |

## Parallelization (筋斗云)

- **CHEAP agents** (eye, ear, nose): 10+ 并发，eye/nose 强制后台
- **MEDIUM agents** (tongue): 2-3 并发，可选后台
- **EXPENSIVE agents** (body, mind): 1 阻塞，禁止后台

同一 Phase 的 agents 可并行执行：`[ear+eye]` 表示 ear 和 eye 同时运行。

## Core Protocol Reference

详细协议见：
- `~/.claude/rules/00-wukong-core.md` - 核心协议
- `~/.claude/skills/jie.md` - 分身边界详细定义
- `~/.claude/skills/summoning.md` - 召唤协议

## Agent Definition Files

Agent 定义文件位置：`~/.claude/agents/`（Claude Code 标准位置）

```
~/.claude/agents/
├── eye.md      # 眼分身定义
├── ear.md      # 耳分身定义
├── nose.md     # 鼻分身定义
├── tongue.md   # 舌分身定义
├── body.md     # 斗战胜佛定义
├── mind.md     # 意分身定义
└── planner.md  # 规划分身定义 (L1 路由)
```

> **重要**: 必须放在 `~/.claude/agents/` 目录下，Claude Code 的 Task tool 才能识别自定义 `subagent_type`。

## Commands & Skills

| Command | Description |
|---------|-------------|
| `/wukong` | 激活悟空多分身工作流 |
| `/qujing <url>` | 取经 - 从开源项目学习 |
| `/neiguan` | 内观 - 反思与沉淀 |
| `/schedule` | 调度 - 任务分析与轨道选择 |

## Anti-Patterns (禁止行为)

- **本体直接实现**: 超过 10 行代码必须委派给 body
- **跳过 CHECKPOINT**: 必须先分析任务再执行
- **串行执行可并行任务**: 同 Phase 的 agents 应并行
- **分身召唤分身**: 分身禁止使用 Task tool
- **未验证就报告完成**: 必须有 Evidence

## Verification (验证金规)

**Iron Law:** 没有证据 = 没有完成

```
验证清单:
□ 文件存在 (Glob/Read)
□ 构建通过 (build command)
□ 测试通过 (test command)
□ 类型检查 (type check)
```
