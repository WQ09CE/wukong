# Neiguan (内观) - Introspection Command

> **BLOCKING checklist** - Complete ALL steps before producing output.

## Trigger

```
/wukong 内观
```

## Pre-Check: Scope Confirmation (防锚定偏差)

> **STOP** - Before introspection, confirm the scope first!

```
┌─────────────────────────────────────────────────────────┐
│  Q1. Does user mention "today/all/total/summary"?       │
│      今天/所有/全部/总结                                 │
│                                                         │
│      YES → Cross-session introspection required         │
│      NO  → Current session only                         │
└─────────────────────────────────────────────────────────┘
```

**Anchoring Bias Triggers:**
| User Says | Wrong | Correct |
|-----------|-------|---------|
| "今天所有工作" | Current session only | All sessions today |
| "我的全部项目" | Current project | All active projects |
| "总结一下" | Current context | Confirm scope first |

---

## BLOCKING CHECKLIST (4 Steps)

> **Must complete ALL 4 steps. Skipping any step = Protocol Violation**

### Step 1: Read Session Index

```bash
# MUST execute
cat ~/.wukong/context/index.json
```

**Expected data:**
- Session list with IDs and metadata
- Project associations
- Timestamps

**If file doesn't exist:** Create empty introspection for current session only.

---

### Step 2: Read Relevant Sessions

> **Critical step - DO NOT SKIP**

```python
# Filter sessions by date (for "today" requests)
today = "YYYYMMDD"  # Current date
relevant_sessions = [s for s in index["sessions"] if today in s["id"]]

# Read EACH session's compact.md
for session in relevant_sessions:
    path = f"~/.wukong/context/sessions/{session['id']}/compact.md"
    # Read(path)
```

**Must collect from each session:**
- [ ] Project name
- [ ] Main tasks completed
- [ ] Key decisions made
- [ ] Issues encountered

**Checklist:**
```
□ Identified relevant sessions: ___
□ Read compact.md for EACH: [list files read]
□ No session skipped: [confirm]
```

---

### Step 3: Read Existing Anchors

```bash
# MUST execute
cat ~/.wukong/context/anchors.md
```

**Purpose:**
- Check for related existing anchors
- Avoid duplicate entries
- Find patterns across sessions

**If file doesn't exist:** Note that no prior anchors exist.

---

### Step 4: Generate Introspection Output

**Only after completing Steps 1-3, produce the output.**

---

## Output Template

### Single Session Output

```markdown
## 内观报告: {task_name}
**Session**: {session_id}
**Project**: {project_name}

### 1. Deviation Diagnosis (偏差诊断)
**Efficiency Loss**: {specific_description}
**Root Cause**: {analysis}

### 2. Rule Patch (规则补丁)
```yaml
rule_patch:
  - action: add|tighten|loosen|remove
    target: "{rule_file}.md"
    rule: "{content}"
    reason: "{reason}"
```

### 3. Distillation (沉淀提炼)
| ID | Type | Content | Threshold Met | Write? |
|----|------|---------|---------------|--------|
| D0xx | Decision | {decision} | Impact high | Y/N |
| P0xx | Pitfall | {pitfall} | Repeat >= 2 | Y/N |
```

### Cross-Session Output

```markdown
## 今日工作内观: {date}

### Session Overview
| Session | Project | Main Tasks | Key Decisions |
|---------|---------|------------|---------------|
| {id1} | {proj1} | {task1} | {decision1} |
| {id2} | {proj2} | {task2} | {decision2} |

### Cross-Session Patterns
- **Common patterns**: {patterns found}
- **Related issues**: {cross-session correlations}

### Per-Session Details

#### Session: {id1} - {project1}
{introspection for session 1}

#### Session: {id2} - {project2}
{introspection for session 2}

### Consolidation Suggestions
{content worth writing to .wukong/context}
```

---

## Write Threshold Check (写入门槛)

> Before writing any anchor, verify at least ONE threshold is met:

```
□ Repetition >= 2: Similar issue/decision appeared twice+
□ High Impact: Architecture/Security/Performance/Multi-module
□ Reusable: Has reference value for other projects/scenarios
```

**If NO threshold met → Do NOT write to anchors.md**

---

## Completion Verification

Before finishing, confirm:

```
┌─────────────────────────────────────────────────────────┐
│  COMPLETION CHECKLIST                                   │
│                                                         │
│  □ Step 1: index.json read (or confirmed missing)       │
│  □ Step 2: ALL relevant session compact.md read         │
│  □ Step 3: anchors.md read (or confirmed missing)       │
│  □ Step 4: Output generated with correct template       │
│  □ Anchoring bias: Scope confirmed before analysis      │
│                                                         │
│  ALL checked → Introspection complete                   │
│  ANY missing → GO BACK and complete missing steps       │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Reference

**File Paths:**
- Session index: `~/.wukong/context/index.json`
- Session data: `~/.wukong/context/sessions/{session_id}/compact.md`
- Anchors: `~/.wukong/context/anchors.md`

**Introspection Dimensions:**
1. Avatar coordination (分身配合)
2. Parallelization efficiency (并行效率)
3. Context transfer (上下文传递)
4. Verification quality (验证质量)
5. User interaction (用户交互)
6. Efficiency analysis (效率分析)

**See also:** `~/.claude/skills/hui.md` for detailed templates and T3 write process.
