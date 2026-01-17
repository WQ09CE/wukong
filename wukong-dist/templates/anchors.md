# Anchors (锚点库)

> 跨会话持久化的关键知识，包含架构决策、约束条件、接口定义和重要教训。

_Last updated: {timestamp}_

## Architecture Decisions (架构决策)

<!-- ADR 格式的架构决策记录 -->

### Example: Use JWT for Authentication

**ID**: `anc_example001`
**Evidence Level**: L2
**Keywords**: auth, jwt, security, stateless

**Context**: 需要实现用户认证机制，支持分布式部署。

**Decision**: 使用 JWT (JSON Web Tokens) 进行无状态认证。

**Rationale**:
- 无状态：不需要服务器端存储会话
- 可扩展：适合分布式和微服务架构
- 标准化：广泛支持，库丰富

**Consequences**:
- (+) 水平扩展更容易
- (+) 跨服务认证简单
- (-) Token 无法主动撤销（需要额外机制）
- (-) Token 大小比 Session ID 大

_Source: tg_example / mind_design_

---

## Constraints (约束条件)

<!-- 项目或系统级的约束 -->

### Example: Python 3.8+ Compatibility

**ID**: `anc_example002`
**Evidence Level**: L3
**Keywords**: python, compatibility, version

**Constraint**: 所有代码必须兼容 Python 3.8+。

**Reason**:
- 生产环境部分服务器仍在使用 Python 3.8
- 需要支持 Ubuntu 20.04 LTS 默认 Python 版本

**Enforcement**:
- CI 中使用 Python 3.8 运行测试
- 禁止使用 3.9+ 专有特性（如 `dict | dict` 语法）
- 使用 `from __future__ import annotations` 支持新式类型注解

---

## Interface Definitions (接口定义)

<!-- 关键 API 和接口契约 -->

### Example: Task Graph Schema

**ID**: `anc_example003`
**Evidence Level**: L2
**Keywords**: taskgraph, schema, api

**Interface**: Task Graph JSON Schema

```json
{
  "id": "tg_{uuid}",
  "title": "string",
  "track": "fix|feature|refactor|direct",
  "status": "created|running|paused|completed|aborted",
  "nodes": [
    {
      "id": "string",
      "role": "eye|ear|nose|tongue|body|mind",
      "status": "pending|running|done|failed|blocked"
    }
  ],
  "edges": [
    {
      "from": "node_id",
      "to": "node_id",
      "condition": "on_success|on_failure|always"
    }
  ]
}
```

**Consumers**: CLI, Scheduler, StateManager

---

## Lessons Learned (教训)

<!-- 从错误和经验中学到的教训 -->

### Example: Always Validate Evidence Level

**ID**: `anc_example004`
**Evidence Level**: L2
**Keywords**: validation, evidence, testing

**Incident**: 分身报告"所有测试通过"，但实际上部分测试被跳过。

**Root Cause**:
- 分身输出仅基于推测 (L0)
- 未执行实际验证命令
- 没有检查测试覆盖率

**Lesson**:
> **永远不要相信未经验证的声明。**
> 分身可能说谎 - 没有证据 = 没有完成。

**Prevention**:
1. 强制要求 L2 级证据（本地命令验证）
2. 检查 pytest 输出中的 "passed/failed" 计数
3. 实现 Evidence Skill 自动验证

---

## Quick Reference

### Anchor Types

| Type | 用途 | 示例 |
|------|------|------|
| `decision` | 架构/技术决策 | 选择数据库、框架 |
| `constraint` | 限制条件 | 版本兼容、性能要求 |
| `interface` | API/接口定义 | Schema、协议 |
| `lesson` | 经验教训 | 故障分析、最佳实践 |

### Evidence Levels

| Level | 可信度 | 说明 |
|-------|--------|------|
| L0 | 不可信 | 基于推测 |
| L1 | 条件可信 | 有引用但未验证 |
| L2 | 默认可信 | 本地命令验证 |
| L3 | 完全可信 | 端到端验证 |

### Writing Good Anchors

1. **标题清晰**: 用动词开头，明确表达决策或约束
2. **上下文完整**: 说明为什么需要这个决策/约束
3. **关键词精准**: 便于搜索和关联
4. **证据等级明确**: 标注验证程度
5. **来源可追溯**: 记录产生此锚点的任务图

---

## Index

<!-- 自动生成的索引，按关键词分组 -->

### By Keyword

- **auth**: anc_example001
- **security**: anc_example001
- **python**: anc_example002
- **compatibility**: anc_example002
- **schema**: anc_example003
- **validation**: anc_example004
- **testing**: anc_example004

### By Type

- **decision**: anc_example001
- **constraint**: anc_example002
- **interface**: anc_example003
- **lesson**: anc_example004

---

_This file is auto-generated. Use `cli.py anchor export` to regenerate._
