# Candidate Anchors (候选锚点)

> 等待审核和提升的锚点候选。满足写入门槛后可提升为正式锚点。

_Last updated: {timestamp}_

## Pending Review

<!-- 待审核的候选锚点列表 -->

### Example Candidate

**ID**: `cand_example001`
**Type**: lesson
**Evidence Level**: L2
**Created**: 2024-01-15T10:30:00Z

**Title**: Validate file existence before JSON parsing

**Content**:
在解析 JSON 文件前，必须先检查文件是否存在。否则会抛出 FileNotFoundError，
且错误信息可能不够明确，难以定位问题根源。

```python
# Bad
with open(config_path) as f:
    config = json.load(f)

# Good
if not config_path.exists():
    raise FileNotFoundError(f"Config file not found: {config_path}")
with open(config_path) as f:
    config = json.load(f)
```

**Keywords**: json, file, validation, error-handling

**Source**:
- Graph ID: tg_abc123
- Node ID: body_implement

**Promotion Criteria**:
- [x] Evidence Level >= L2
- [ ] Reviewed by human
- [ ] Similar issue occurred 2+ times

---

## Write Threshold (写入门槛)

候选锚点需满足至少一项条件才能被提升为正式锚点：

| 条件 | 说明 | 如何验证 |
|------|------|----------|
| **重复 >= 2** | 类似问题/决策出现两次以上 | 搜索历史记录 |
| **影响大** | 涉及架构、安全、性能、多模块 | 人工判断 |
| **可复用** | 在其他项目/场景中有参考价值 | 通用性评估 |

## Candidate Lifecycle

```
创建候选 ─────────────────────────────────────────┐
     │                                            │
     ▼                                            │
┌─────────────────┐                               │
│  Pending Review │ ← 等待审核                     │
└────────┬────────┘                               │
         │                                        │
         ├── 满足门槛 ──→ Promote ──→ 正式锚点     │
         │                                        │
         ├── 不满足门槛 ──→ Keep ──→ 继续等待      │
         │                                        │
         └── 无价值 ──→ Delete ──→ 删除 ──────────┘
```

## Quick Actions

### Promote to Anchor

```bash
# 提升候选为正式锚点
python3 ~/.wukong/runtime/cli.py anchor promote cand_example001

# 提升到特定项目
python3 ~/.wukong/runtime/cli.py anchor promote cand_example001 --project myproject
```

### Delete Candidate

```bash
# 删除候选
python3 ~/.wukong/runtime/cli.py anchor delete-candidate cand_example001
```

### List All Candidates

```bash
# 列出所有候选
python3 ~/.wukong/runtime/cli.py anchor list-candidates
```

---

## Auto-Extraction Rules

on_stop Hook 自动提取候选锚点的规则：

### 1. Decision Detection

检测输出中的决策模式：

```
触发词: "决定", "选择", "采用", "使用", "决策"
         "decided", "chose", "adopted", "selected"

示例: "我们决定使用 PostgreSQL 作为主数据库"
      → 创建 type=decision 的候选
```

### 2. Constraint Detection

检测约束和限制：

```
触发词: "必须", "不能", "限制", "要求", "约束"
         "must", "cannot", "constraint", "require", "limit"

示例: "必须保持与 Python 3.8 的兼容性"
      → 创建 type=constraint 的候选
```

### 3. Lesson Detection

检测经验教训：

```
触发词: "教训", "发现", "注意", "问题", "bug", "fix"
         "lesson", "learned", "discovered", "issue", "gotcha"

示例: "发现必须在解析 JSON 前检查文件存在"
      → 创建 type=lesson 的候选
```

### 4. Interface Detection

检测接口定义：

```
触发词: "接口", "API", "schema", "格式", "协议"
         "interface", "endpoint", "contract"

示例: "定义了新的 TaskGraph JSON schema"
      → 创建 type=interface 的候选
```

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Candidates | {count} |
| Pending Review | {pending} |
| Promoted (this month) | {promoted} |
| Deleted (this month) | {deleted} |

### By Type

| Type | Count |
|------|-------|
| decision | {decision_count} |
| constraint | {constraint_count} |
| interface | {interface_count} |
| lesson | {lesson_count} |

### By Evidence Level

| Level | Count |
|-------|-------|
| L0 | {l0_count} |
| L1 | {l1_count} |
| L2 | {l2_count} |
| L3 | {l3_count} |

---

_This file is auto-generated. Use `cli.py anchor list-candidates` to refresh._
