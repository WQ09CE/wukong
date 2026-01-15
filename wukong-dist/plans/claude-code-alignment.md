# Wukong-Claude Code Architecture Alignment Plan

> **Version**: 1.0
> **Date**: 2025-01-12
> **Status**: Draft - Pending Review

## Executive Summary

This document analyzes the alignment between Wukong's multi-agent orchestration system and Claude Code's native mechanisms. The goal is to leverage Claude Code's first-class primitives (Subagents, Hooks, MCP, Background Tasks) to make Wukong more robust, efficient, and maintainable.

---

## Architecture Overview Diagram

```
                         ┌─────────────────────────────────────────────────────────┐
                         │                   Claude Code Runtime                    │
                         │  ┌─────────────────────────────────────────────────────┐ │
                         │  │                     Hooks Layer                      │ │
                         │  │  ┌───────────┐ ┌───────────┐ ┌───────────────────┐  │ │
                         │  │  │PreToolUse │ │PermReq   │ │SubagentStop       │  │ │
                         │  │  │(戒关)     │ │(验证门)  │ │(锚点固化)         │  │ │
                         │  │  └───────────┘ └───────────┘ └───────────────────┘  │ │
                         │  │  ┌───────────────────────────────────────────────┐  │ │
                         │  │  │              PreCompact (缩形态生成)           │  │ │
                         │  │  └───────────────────────────────────────────────┘  │ │
                         │  └─────────────────────────────────────────────────────┘ │
                         │                            │                             │
                         │  ┌──────────────────────────┼──────────────────────────┐ │
                         │  │                  Wukong 本体                        │ │
                         │  │           (Orchestrator + User Interface)           │ │
                         │  └──────────────────────────┼──────────────────────────┘ │
                         │                            │                             │
                         │  ┌──────────────────────────┼──────────────────────────┐ │
                         │  │                    Subagents                        │ │
                         │  │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │ │
                         │  │  │ 眼  │ │ 耳  │ │ 鼻  │ │ 舌  │ │ 身  │ │ 意  │   │ │
                         │  │  │(BG) │ │     │ │(BG) │ │     │ │     │ │     │   │ │
                         │  │  └─────┘ └─────┘ └─────┘ └─────┘ └─────┘ └─────┘   │ │
                         │  │                                                     │ │
                         │  │  ┌─────────────────────────────────────────────┐   │ │
                         │  │  │        内观悟空 (Meta-Subagent)               │   │ │
                         │  │  │  - Context Health / Anchor Extraction       │   │ │
                         │  │  └─────────────────────────────────────────────┘   │ │
                         │  └─────────────────────────────────────────────────────┘ │
                         │                            │                             │
                         │  ┌──────────────────────────┼──────────────────────────┐ │
                         │  │                  Tools Layer                        │ │
                         │  │  ┌───────────────┐ ┌───────────────┐ ┌───────────┐ │ │
                         │  │  │ Built-in Tools│ │   MCP Tools   │ │Custom Tools│ │ │
                         │  │  │ (per-subagent)│ │  (chrome,etc) │ │(wukong cli)│ │ │
                         │  │  └───────────────┘ └───────────────┘ └───────────┘ │ │
                         │  └─────────────────────────────────────────────────────┘ │
                         │                            │                             │
                         │  ┌──────────────────────────┼──────────────────────────┐ │
                         │  │              Persistent Storage (阿赖耶识)          │ │
                         │  │  ┌────────────┐ ┌────────────┐ ┌────────────────┐  │ │
                         │  │  │ anchors.md │ │ notepads/  │ │ context/       │  │ │
                         │  │  └────────────┘ └────────────┘ └────────────────┘  │ │
                         │  └─────────────────────────────────────────────────────┘ │
                         └─────────────────────────────────────────────────────────┘
```

---

## Issue 1: Avatar = Subagent or Skill?

### Analysis Framework

Claude Code has two distinct mechanisms:
- **Skills**: Inject "knowledge/standards/process guidance" into current conversation
- **Subagents**: Isolated execution units with independent context, tools, and permissions

**Key Distinction**:
- Skills = "How to think" (cognitive framework)
- Subagents = "Who does the work" (execution isolation)

### Recommendation Matrix

| Avatar | Recommendation | Rationale |
|--------|---------------|-----------|
| 👁️ 眼分身 (Explorer) | **Subagent** | Heavy tool usage (Grep, Glob, WebSearch), long-running exploration, benefits from context isolation to avoid polluting main conversation |
| 👂 耳分身 (Analyst) | **Skill** | Primarily cognitive work (requirement analysis), needs access to full user context, no tool isolation needed |
| 👃 鼻分身 (Reviewer) | **Subagent** | Independent review context, can run in background, should not modify files, clear tool restrictions |
| 👅 舌分身 (Tester) | **Hybrid** | **Skill** for test strategy/documentation, **Subagent** for test execution (pytest runs benefit from isolation) |
| ⚔️ 斗战胜佛 (Implementer) | **Subagent** | Heavy file operations, needs Write/Edit tools, context isolation protects main conversation from implementation details |
| 🧠 意分身 (Architect) | **Skill** | Design thinking benefits from full context, minimal tool usage, outputs design documents |
| 🔮 内观悟空 (Introspector) | **Skill** (Special) | Needs access to entire conversation for reflection, but could be **Subagent** for automated anchor extraction |

### Detailed Breakdown

#### Why 眼分身 Should Be Subagent

```
Current: Task(prompt=skill_content + task)
Proposed: Subagent with dedicated exploration context

Benefits:
├── Search results don't pollute main context
├── Can run multiple explorations in parallel (background=true)
├── Can resume exploration with `resume: "<agent_id>"`
└── Independent tool permissions (read-only)
```

#### Why 耳分身 Should Be Skill

```
Current: Task(prompt=skill_content + user_request)
Proposed: Skill injection into main conversation

Benefits:
├── Full access to user context and conversation history
├── Can ask clarifying questions directly
├── Requirement understanding needs dialogue flow
└── No isolation overhead for cognitive work
```

#### Why 斗战胜佛 Should Be Subagent

```
Current: Task(prompt=skill_content + design_doc + context)
Proposed: Subagent with write permissions + design context

Benefits:
├── Implementation details isolated from orchestrator
├── Clear tool boundary (can Write/Edit)
├── Subagent completion triggers verification hooks
└── Can route to different model for coding tasks
```

---

## Issue 2: Tool Permission Matrix

### Proposed Permission Model

| Avatar | Allowed Built-in Tools | Forbidden Tools | MCP Access |
|--------|----------------------|-----------------|------------|
| 👁️ 眼分身 | Read, Glob, Grep, WebSearch, WebFetch | Write, Edit, NotebookEdit | chrome (read-only) |
| 👂 耳分身 | Read (limited), Glob (for context) | Write, Edit, Bash (exec) | None |
| 👃 鼻分身 | Read, Glob, Grep, mcp__ide__getDiagnostics | Write, Edit, Bash (exec) | chrome (for UI review) |
| 👅 舌分身 | Read, Write (tests only), Glob, Bash (pytest) | Edit (prod code) | None |
| ⚔️ 斗战胜佛 | Read, Write, Edit, Glob, Grep, Bash | None (full access) | All available |
| 🧠 意分身 | Read, Glob, WebSearch | Write (except design.md), Bash | None |
| 🔮 内观悟空 | Read, Write (context/ only), Glob | Edit, Bash | None |

### Implementation via Claude Code `--tools` Flag

```bash
# Example: Spawning Explorer with restricted tools
claude --tools="Read,Glob,Grep,WebSearch,WebFetch" \
  --system-prompt="$(cat .wukong/skills/explorer.md)" \
  "Explore the authentication module"
```

### Permission Enforcement via Hooks

```typescript
// hooks/PreToolUse.ts - Enforce tool boundaries
export default async function preToolUse(event: PreToolUseEvent) {
  const { tool_name, subagent_id } = event;
  const avatarType = getAvatarType(subagent_id);

  const forbidden = FORBIDDEN_TOOLS[avatarType];
  if (forbidden?.includes(tool_name)) {
    return {
      decision: "block",
      reason: `[戒关] ${avatarType} cannot use ${tool_name}`
    };
  }

  return { decision: "allow" };
}
```

---

## Issue 3: Parallelization Strategy

### Current State Analysis

Wukong defines 5 parallelization patterns:
1. **分身群攻** (Multi-Module Implementation)
2. **侦察兵+主力军** (Scout & Infantry)
3. **TDD钳形攻势** (Test + Implement Pincer)
4. **代码+配置并行** (Code + Config Parallel)
5. **蜂群模式** (Mass Operations)

### Claude Code Parallelization Options

| Mechanism | Use Case | Cost | Context Impact |
|-----------|----------|------|----------------|
| **Multiple Subagents** | Independent tasks, different contexts | Higher (multiple API calls) | Isolated - no pollution |
| **Background Bash** | Long-running commands | Lower (single thread) | Shared context |
| **Parallel Tool Calls** | Independent tool operations | Lowest | Shared context |

### Recommended Strategy

```
Decision Tree:
│
├── Tasks need different contexts?
│   ├── Yes → Multiple Subagents
│   └── No → Continue
│
├── Tasks are long-running CLI commands?
│   ├── Yes → Background Bash
│   └── No → Continue
│
├── Tasks are independent tool calls?
│   ├── Yes → Parallel Tool Calls (same message)
│   └── No → Sequential execution
```

### Pattern Mapping

| Wukong Pattern | Claude Code Implementation |
|----------------|---------------------------|
| 分身群攻 | Multiple Subagents (max 3-4) |
| 侦察兵+主力军 | 1 Background Subagent (眼) + 1 Foreground (斗战胜佛) |
| TDD钳形攻势 | 2 Subagents: Test Writer + Implementer |
| 代码+配置并行 | 1 Subagent (斗战胜佛) + Background Bash (config gen) |
| 蜂群模式 | Multiple Background Subagents (batch processing) |

### When Background Bash Beats Subagent

```
Use Background Bash when:
├── Running tests: `pytest -v` (run_in_background=true)
├── Building: `cmake --build build` (run_in_background=true)
├── Linting: `ruff check . && mypy src/` (run_in_background=true)
└── Git operations: `git status && git diff` (run_in_background=true)

Use Subagent when:
├── Need independent reasoning context
├── Task requires specialized skill injection
├── Output needs isolation from main conversation
└── Running parallel explorations
```

---

## Issue 4: Verification Golden Rules via Hooks

### Current Verification Framework

Wukong's 戒定慧 (Sila-Samadhi-Prajna) verification pipeline:
1. **末那识 (Manas)**: Filter assumptions and biases
2. **戒关 (Sila Gate)**: Rule compliance check
3. **定关 (Samadhi Gate)**: Reproducibility check
4. **慧关 (Prajna Gate)**: Abstraction and validation
5. **阿赖耶识 (Alaya Store)**: Persistence and learning

### Hooks Mapping

| Verification Stage | Claude Code Hook | Implementation |
|-------------------|------------------|----------------|
| 末那识 (Assumption Filter) | PreToolUse | Block tools when assumptions detected in prompt |
| 戒关 (Rule Check) | PreToolUse | Block Write/Edit if Output Contract incomplete |
| 定关 (Reproducibility) | PermissionRequest | Auto-allow verified commands, prompt for risky ones |
| 慧关 (Validation) | SubagentStop | Trigger verification before accepting results |
| 阿赖耶识 (Persistence) | SubagentStop | Extract anchors, update notepads |

### Hook Implementation Examples

#### PreToolUse: 戒关 (Rule Enforcement)

```typescript
// hooks/PreToolUse.ts
export default async function preToolUse(event: PreToolUseEvent) {
  const { tool_name, tool_input, subagent_id } = event;

  // 戒关: Check if avatar is within its territory
  if (tool_name === "Write" || tool_name === "Edit") {
    const avatarType = getAvatarType(subagent_id);
    const declaredTerritory = getTerritoryDeclaration(subagent_id);
    const targetFile = tool_input.file_path;

    if (!isInTerritory(targetFile, declaredTerritory)) {
      return {
        decision: "block",
        reason: `[戒关] File ${targetFile} not in declared territory: ${declaredTerritory}`
      };
    }
  }

  return { decision: "allow" };
}
```

#### PermissionRequest: 定关 (Reproducibility Gate)

```typescript
// hooks/PermissionRequest.ts
export default async function permissionRequest(event: PermissionRequestEvent) {
  const { tool_name, tool_input } = event;

  // Auto-allow verification commands
  const SAFE_VERIFICATION = [
    /^pytest/,
    /^mypy/,
    /^ruff check/,
    /^cmake --build/,
    /^ctest/
  ];

  if (tool_name === "Bash") {
    const command = tool_input.command;
    if (SAFE_VERIFICATION.some(pattern => pattern.test(command))) {
      return { decision: "allow" };
    }
  }

  // Prompt for risky operations
  return { decision: "ask" };
}
```

#### SubagentStop: 锚点固化 + 结果验证

```typescript
// hooks/SubagentStop.ts
export default async function subagentStop(event: SubagentStopEvent) {
  const { subagent_id, output, exit_reason } = event;

  // 1. Extract potential anchors from output
  const anchors = extractAnchors(output);
  if (anchors.length > 0) {
    await appendToFile(".wukong/context/anchors.md", formatAnchors(anchors));
  }

  // 2. Verify implementation results
  const avatarType = getAvatarType(subagent_id);
  if (avatarType === "斗战胜佛") {
    // Trigger verification
    const verificationResult = await runVerification(output);
    if (!verificationResult.passed) {
      // Notify main conversation
      return {
        postMessage: `[定关] Verification failed: ${verificationResult.errors.join(", ")}`
      };
    }
  }

  // 3. Update context
  await updateContextState(subagent_id, output);

  return {};
}
```

---

## Issue 5: Three Forms and Compact Alignment

### Current State

Wukong's 如意金箍棒 (Ruyi Jingu Bang) protocol defines three context forms:
- 🔸 **缩形态 (Compact)**: <500 chars, for cross-session transfer
- 🔹 **常形态 (Normal)**: 500-2000 chars, for standard operations
- 🔶 **巨形态 (Expanded)**: Full content, for debugging

### Claude Code's PreCompact Hook

The `PreCompact` hook fires **before** context compaction, making it ideal for:
1. Extracting and persisting anchors
2. Generating 缩形态 summary
3. Saving state to persistent storage

### Alignment Strategy

#### When to Write Anchors

| Trigger | Hook | Action |
|---------|------|--------|
| Subagent completes | SubagentStop | Extract decisions, constraints, interfaces |
| Context > 75% | PreCompact | Force anchor extraction before compaction |
| User requests "内观" | Manual | Deep reflection + full anchor audit |
| Session ends | PreCompact | Ensure all key decisions captured |

#### PreCompact Hook Implementation

```typescript
// hooks/PreCompact.ts
export default async function preCompact(event: PreCompactEvent) {
  const { conversation_history, context_usage } = event;

  // 1. Extract anchors not yet persisted
  const newAnchors = extractNewAnchors(conversation_history);
  await appendToFile(".wukong/context/anchors.md", formatAnchors(newAnchors));

  // 2. Generate compact summary (缩形态)
  const compactSummary = await generateCompactSummary(conversation_history, {
    maxChars: 500,
    includeAnchors: true,
    includeTasks: true,
    includeDecisions: true
  });

  // 3. Save to persistent storage
  await writeFile(".wukong/context/current/compact.md", compactSummary);

  // 4. Optionally generate normal form
  if (context_usage > 0.75) {
    const normalSummary = await generateNormalSummary(conversation_history);
    await writeFile(".wukong/context/current/normal.md", normalSummary);
  }

  // 5. Return compact summary to be included in compacted context
  return {
    inject_content: compactSummary
  };
}
```

#### Cross-Session Transfer

```
Session 1 ends:
├── PreCompact fires
├── Extract anchors → anchors.md
├── Generate compact → compact.md
└── User closes session

Session 2 starts:
├── User: "继续上次的任务"
├── Load compact.md
├── Load relevant anchors
└── Resume with minimal context usage
```

### Compact Form Template (Optimized for Claude Code)

```markdown
## 🔸 Context Resume

**Task**: {one-line goal}
**Track**: Feature|Fix|Refactor
**Progress**: Phase {N}/{Total}

**Active Anchors**:
- [D001] {decision}: {choice} - {why}
- [C001] {constraint}: {rule}
- [I001] {interface}: `signature`

**State**:
- Done: {completed_items}
- Current: {in_progress}
- Next: {pending}

**Files Modified**: {file_list}

**Resume Command**: "继续 {task_name}"
```

---

## Files to Modify

### Priority 1: Core Infrastructure

| File | Change | Effort |
|------|--------|--------|
| `.wukong/rules-lite/00-wukong-core.md` | Add Subagent vs Skill distinction | Medium |
| `.wukong/skills/orchestration.md` | Update Task() calls to match Subagent API | Medium |
| `NEW: .wukong/hooks/PreToolUse.ts` | Implement 戒关 tool blocking | High |
| `NEW: .wukong/hooks/SubagentStop.ts` | Implement anchor extraction + verification | High |
| `NEW: .wukong/hooks/PreCompact.ts` | Implement 缩形态 generation | Medium |

### Priority 2: Skill Files

| File | Change | Effort |
|------|--------|--------|
| `.wukong/skills/explorer.md` | Add Subagent-specific instructions | Low |
| `.wukong/skills/implementer.md` | Add territory declaration protocol | Low |
| `.wukong/skills/hui.md (merged from introspector)` | Align with PreCompact hook | Medium |
| `NEW: .wukong/skills/subagent-base.md` | Common Subagent instructions | Medium |

### Priority 3: Context Management

| File | Change | Effort |
|------|--------|--------|
| `.wukong/skills/ruyi.md` | Add PreCompact integration | Medium |
| `.wukong/context/templates/compact-template.md` | Optimize for Claude Code | Low |
| `NEW: .wukong/context/dcp-hooks.yaml` | DCP strategy as hook config | Medium |

### Priority 4: Documentation

| File | Change | Effort |
|------|--------|--------|
| `.wukong/commands/wukong.md` | Update summoning syntax for Subagents | Low |
| `NEW: .wukong/docs/claude-code-integration.md` | Document hook architecture | Medium |

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)

```
Goals:
├── Implement PreToolUse hook for tool boundary enforcement
├── Update 眼分身 to use true Subagent isolation
├── Update 斗战胜佛 to use Subagent with full tool access
└── Implement basic SubagentStop for result verification
```

### Phase 2: Verification Pipeline (Week 2)

```
Goals:
├── Implement 戒关 rules as PreToolUse blocks
├── Implement 定关 as PermissionRequest auto-allows
├── Implement anchor extraction in SubagentStop
└── Add territory declaration and enforcement
```

### Phase 3: Context Management (Week 3)

```
Goals:
├── Implement PreCompact for 缩形态 generation
├── Integrate DCP strategies with hooks
├── Implement cross-session resume
└── Test anchor persistence and retrieval
```

### Phase 4: Optimization (Week 4)

```
Goals:
├── Profile and optimize hook performance
├── Tune parallel Subagent limits
├── Document best practices
└── Create migration guide for existing workflows
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Hook overhead slows down workflow | Medium | Medium | Profile and optimize, use async hooks |
| Subagent context isolation breaks existing patterns | High | High | Gradual migration, maintain backward compatibility |
| Anchor extraction misses key decisions | Medium | High | Multiple extraction points (SubagentStop + PreCompact) |
| Tool restrictions too aggressive | Medium | Medium | Start permissive, tighten based on feedback |

---

## Success Metrics

1. **Verification Coverage**: 100% of Subagent outputs pass through 戒定慧 pipeline
2. **Context Efficiency**: <5% context usage for resume (缩形态 working)
3. **Parallel Utilization**: Average 2-3 Subagents running in parallel for complex tasks
4. **Anchor Persistence**: 95%+ of key decisions captured as anchors
5. **Hook Performance**: <100ms average latency per hook invocation

---

## Conclusion

The alignment between Wukong and Claude Code's native mechanisms presents a significant opportunity to make the multi-agent workflow more robust and efficient. The key insights are:

1. **Subagents are not role-play** - They are isolated execution units with real benefits for context management and tool control.

2. **Hooks are the control plane** - PreToolUse for 戒关, PermissionRequest for 定关, SubagentStop for result convergence, PreCompact for context preservation.

3. **Skills complement Subagents** - Use Skills for cognitive framing (耳分身, 意分身), Subagents for execution isolation (眼分身, 斗战胜佛, 鼻分身).

4. **Parallelization has two axes** - Subagent parallelism for independent contexts, Background Bash for CLI commands.

5. **Context management aligns naturally** - 缩形态 maps perfectly to PreCompact, anchors persist via SubagentStop.

The implementation should proceed incrementally, starting with the foundation (Subagent isolation + basic hooks) and building up to full verification pipeline and context management integration.
