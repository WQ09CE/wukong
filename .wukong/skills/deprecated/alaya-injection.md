# Alaya Injection Protocol (阿赖耶识注入协议)

> **阿赖耶识是"被动、稀疏、前置"的惯性提示器**
> 不是"指挥官"，只是"惯性提示器"
> 只影响"默认选项与风险提醒"，不影响"决策结论与执行路径"

## Philosophy (设计理念)

```
┌─────────────────────────────────────────────────────────────────┐
│                     内观 vs 阿赖耶识 分工                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  内观悟空                     阿赖耶识                           │
│  ┌─────────────┐              ┌─────────────┐                    │
│  │ 主动        │              │ 被动        │                    │
│  │ 判断        │              │ 不判断      │                    │
│  │ 即时        │              │ 不即时      │                    │
│  │ 不跨会话    │              │ 跨会话      │                    │
│  │ 决定"要不要"│              │ 只提供内容  │                    │
│  └─────────────┘              └─────────────┘                    │
│        │                             │                           │
│        └──────────┬──────────────────┘                           │
│                   │                                              │
│                   ▼                                              │
│            内观是阿赖耶识的"读写门户"                            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**核心原则**:
- **被动**: 阿赖耶识不主动触发，只在特定时机被查询
- **稀疏**: 注入内容精简，不超过 500 字
- **前置**: 在决策发生前提供提示，不事后评判

---

## The Three Golden Injection Timings (三个黄金注入时机)

```
用户请求
    │
    ├─────────────────────────────────────────┐
    │                                          │
    ▼                                          │
┌─────────┐                                    │
│ 时机 1  │ ← 任务启动 / 轨道确定之前           │
│ T1      │   注入: 风险标签、Anti-pattern      │
└────┬────┘                                    │
     │                                         │
     ▼                                         │
[轨道选择] → [需求/探索] → [设计]              │
     │                          │              │
     │                          ▼              │
     │                    ┌─────────┐          │
     │                    │ 时机 2  │ ← 意→身  │
     │                    │ T2      │   注入: ADR、tradeoff
     │                    └────┬────┘          │
     │                         │               │
     │                         ▼               │
     │                    [实现] → [测试/审查] │
     │                         │               │
     │                         ▼               │
     │                    [收敛/验证]          │
     │                         │               │
     │                         ▼               │
     │                    ┌─────────┐          │
     │                    │ 时机 3  │ ← 存档前 │
     │                    │ T3      │   写入门户
     │                    └────┬────┘          │
     │                         │               │
     └─────────────────────────┴───────────────┘
```

---

## Timing 1: Pre-Track (任务启动前)

### 触发条件
- 用户发送新请求
- 本体进入轨道选择前

### 目的
- 注入相似任务的风险标签
- 提醒 Anti-pattern
- 标记特殊约束

### 查询逻辑

```python
def alaya_query_t1(user_request: str) -> AlayaContext:
    """
    时机 1: 任务启动前查询
    """
    # 1. 提取关键词
    keywords = extract_keywords(user_request)
    # 技术栈: python, fastapi, ffmpeg...
    # 模块名: auth, api, video...
    # 问题类型: bug, feature, refactor...

    # 2. 检索相关锚点
    relevant_anchors = search_anchors(
        anchors_path=".wukong/context/anchors.md",
        keywords=keywords,
        types=["P", "C", "M"],  # 问题、约束、模式
        threshold=0.7  # 相似度阈值
    )

    # 3. 构建注入上下文
    return AlayaContext(
        warnings=filter_by_type(relevant_anchors, "P"),
        constraints=filter_by_type(relevant_anchors, "C"),
        patterns=filter_by_type(relevant_anchors, "M"),
        references=get_anchor_ids(relevant_anchors)
    )
```

### 注入格式

```markdown
## [Alaya T1] 启动提示

⚠️ **相关风险** (warnings):
- [P001] FFmpeg 在某格式下内存泄漏 - 涉及视频处理时注意
- [P003] async 递归深度限制 - 涉及异步处理时注意

📌 **约束提醒** (constraints):
- [C001] 所有输出必须脱敏 - 涉及用户数据时必须遵守

🚫 **Anti-pattern**:
- 避免在 main.py 写业务逻辑 (M002)
- 避免同步阻塞调用 (M005)

---
> *以上为阿赖耶识惯性提示，仅供参考，不影响轨道选择*
```

### 字数限制
- 最大 300 字
- 最多 5 条 warning
- 最多 3 条 constraint
- 最多 3 条 anti-pattern

---

## Timing 2: Pre-Implementation (方案冻结后)

### 触发条件
- 意分身完成设计方案
- 斗战胜佛开始实现前
- **仅适用于有设计阶段的轨道**

### 轨道适配矩阵

| 轨道 | 时机 2 触发 | 说明 |
|------|------------|------|
| Feature | Yes | 意分身完成 design.md 后 |
| Refactor | Yes | 意分身完成重构策略后 |
| Fix | Conditional | 若涉及意分身则触发 |
| Direct | No | 无设计阶段，跳过 |

### 查询逻辑

```python
def alaya_query_t2(design_doc: str) -> AlayaDesignContext:
    """
    时机 2: 方案冻结后查询
    """
    # 1. 提取设计中的技术选型
    tech_choices = extract_tech_choices(design_doc)
    # 例如: ["Ollama", "FastAPI", "PostgreSQL"]

    # 2. 检索相关历史 ADR
    historical_adrs = search_anchors(
        anchors_path=".wukong/context/anchors.md",
        keywords=tech_choices,
        types=["D"],  # 决策锚点
        threshold=0.6
    )

    # 3. 提取 tradeoff 和回滚经验
    return AlayaDesignContext(
        historical_decisions=historical_adrs,
        known_tradeoffs=extract_tradeoffs(historical_adrs),
        rollback_experience=extract_rollbacks(historical_adrs)
    )
```

### 注入格式

```markdown
## [Alaya T2] 设计参考

📜 **历史决策** (historical_decisions):
| ID | 决策 | 理由 | 后果 |
|----|------|------|------|
| [D001] | Ollama vs OpenAI | 成本低、数据本地化 | 需 GPU 支持 |
| [D003] | 正则+规则脱敏 | 灵活性好 | 性能略低 |

⚖️ **已知 Tradeoff**:
- **微服务 vs 单体** (D005): 上次选单体
  - 后续发现: 扩展性受限
  - 建议: 若预期增长，考虑模块化

🔙 **回滚经验**:
- D001 回滚方式: `LLM_BACKEND=openai`
- D003 回滚方式: 恢复原脱敏逻辑

---
> *以上为阿赖耶识参考，决策权在本体/意分身*
```

### 字数限制
- 最大 400 字
- 最多 5 条历史决策
- 最多 3 条 tradeoff

---

## Timing 3: Pre-Archive (存档前)

### 触发条件
- 内观悟空执行存档
- 用户触发 `压缩` / `存档` 命令
- 上下文使用 > 85%

### 目的
- **写入通道**: 判断哪些信息值得写入阿赖耶识
- **去重检查**: 检查是否已有类似锚点
- **质量把关**: 确保写入内容符合 ADR 格式

### 写入门槛 (Anchor Write Threshold)

```
┌─────────────────────────────────────────────────────────────────┐
│                    写入门槛检查 (至少满足一项)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  □ 重复性 (Frequency)                                            │
│    └─ 类似问题/决策在本次会话或历史中出现 ≥ 2 次                  │
│                                                                   │
│  □ 影响面 (Impact)                                               │
│    └─ 涉及以下任一:                                              │
│       - 架构决策                                                  │
│       - 安全相关                                                  │
│       - 性能关键                                                  │
│       - 多模块影响                                                │
│                                                                   │
│  □ 可复用性 (Reusability)                                        │
│    └─ 在其他项目/场景中有参考价值                                 │
│    └─ 可以抽象为通用模式                                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 写入流程

```python
def alaya_write_t3(session_context: SessionContext) -> WriteResult:
    """
    时机 3: 存档前写入
    """
    # 1. 收集候选锚点 (由内观悟空标记)
    candidates = session_context.introspection_output.candidate_anchors

    for anchor in candidates:
        # 2. 检查写入门槛
        if not meets_threshold(anchor):
            continue

        # 3. 去重检查
        similar = find_similar_anchor(
            anchors_path=".wukong/context/anchors.md",
            anchor=anchor,
            similarity_threshold=0.8
        )

        if similar:
            if should_merge(anchor, similar):
                # 合并到现有锚点
                update_anchor(similar.id, anchor)
            else:
                # 标记待人工审核
                mark_for_review(anchor, similar)
        else:
            # 4. 写入新锚点
            write_anchor(anchor)

    return WriteResult(
        written=written_anchors,
        merged=merged_anchors,
        pending_review=review_anchors
    )
```

### 去重策略

| 情况 | 处理方式 |
|------|----------|
| 标题相似度 > 0.8 | 合并或更新现有锚点 |
| 决策冲突 | 标记待人工审核 |
| 同一问题不同解决方案 | 保留最新，链接历史 |
| 补充信息 | 追加到现有锚点 |

---

## Unidirectional Rule (单向规则)

### 可读字段 (Read-Only)

阿赖耶识注入时，**只能**包含以下字段:

| 字段 | 说明 | 示例 |
|------|------|------|
| `warnings` | 风险提醒 | [P001] FFmpeg 内存泄漏 |
| `tags` | 分类标签 | #security #performance |
| `references` | 锚点引用 | [D001], [C002] |
| `historical_decisions` | 历史决策 | ADR 列表 |
| `known_tradeoffs` | 已知权衡 | 性能 vs 可读性 |
| `rollback_experience` | 回滚经验 | 如何撤销决策 |
| `anti_patterns` | 反模式提醒 | 避免同步阻塞 |

### 禁止字段 (Never Include)

以下字段**禁止**出现在阿赖耶识注入中:

| 字段 | 原因 |
|------|------|
| `recommended_solution` | 会干预决策 |
| `final_decision` | 决策权在本体/分身 |
| `must_use` | 强制性约束应走戒关 |
| `priority_order` | 优先级判断是主动行为 |
| `confidence_score` | 暗示决策方向 |

### 检查机制

```
阿赖耶识输出内容
        │
        ▼
┌─────────────────────────────────────────┐
│  单向规则检查 (Unidirectional Check)    │
│  ┌───────────────────────────────────┐  │
│  │ 扫描禁止字段:                      │  │
│  │ □ recommended_solution            │  │
│  │ □ final_decision                  │  │
│  │ □ must_use                        │  │
│  │ □ priority_order                  │  │
│  │ □ confidence_score                │  │
│  └───────────────────────────────────┘  │
│                                         │
│  发现禁止字段 → 过滤移除 + 警告日志      │
│  全部合规 → 通过注入                     │
└─────────────────────────────────────────┘
```

---

## Integration with Existing Systems (与现有系统集成)

### 与八识验证流水线集成

```
六根分身输出
      │
      ▼
┌─────────────┐
│ [Alaya T1]  │ ← 任务启动前
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  末那识     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ [Alaya T2]  │ ← 意→身 (如适用)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  戒定慧三关 │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ [Alaya T3]  │ ← 存档前
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  阿赖耶识   │ ← 持久化存储
└─────────────┘
```

### 与如意金箍棒协议集成

- **锚点是阿赖耶识的核心数据结构**
- 时机 1/2 读取锚点进行注入
- 时机 3 写入新锚点
- 三态压缩时，阿赖耶识提示优先保留

### 与内观悟空协议集成

内观悟空是阿赖耶识的"读写门户":

```
┌─────────────────────────────────────────────────────────────────┐
│                    内观悟空的阿赖耶识职责                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  读取职责 (在内观开始时):                                         │
│  ├── 查询相关历史锚点                                             │
│  ├── 对比本次行为与历史模式                                       │
│  └── 识别重复出现的问题/决策                                      │
│                                                                   │
│  写入职责 (在内观结束时):                                         │
│  ├── 标记候选锚点                                                 │
│  ├── 检查写入门槛                                                 │
│  ├── 执行去重检查                                                 │
│  └── 提交写入请求                                                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration (配置)

存储位置: `.wukong/context/alaya-config.yaml`

```yaml
# Alaya Injection 配置
alaya:
  enabled: true

  # 时机 1: 任务启动前
  timing_1:
    enabled: true
    max_words: 300
    max_warnings: 5
    max_constraints: 3
    max_antipatterns: 3
    similarity_threshold: 0.7

  # 时机 2: 方案冻结后
  timing_2:
    enabled: true
    max_words: 400
    max_decisions: 5
    max_tradeoffs: 3
    similarity_threshold: 0.6
    # 轨道适配
    tracks:
      feature: true
      refactor: true
      fix: conditional  # 有意分身参与时触发
      direct: false

  # 时机 3: 存档前
  timing_3:
    enabled: true
    # 写入门槛
    threshold:
      min_frequency: 2
      impact_types: [architecture, security, performance, multi_module]
      require_reusability: false  # 至少满足一项即可
    # 去重
    deduplication:
      similarity_threshold: 0.8
      auto_merge: true
      conflict_review: true

  # 单向规则
  unidirectional:
    allowed_fields:
      - warnings
      - tags
      - references
      - historical_decisions
      - known_tradeoffs
      - rollback_experience
      - anti_patterns
    forbidden_fields:
      - recommended_solution
      - final_decision
      - must_use
      - priority_order
      - confidence_score
```

---

## Commands (命令)

| 命令 | 描述 |
|------|------|
| `阿赖耶 查询` | 手动触发时机 1 查询 |
| `阿赖耶 设计参考` | 手动触发时机 2 查询 |
| `阿赖耶 写入检查` | 检查候选锚点是否满足写入门槛 |
| `阿赖耶 统计` | 显示阿赖耶识存储统计 |

---

## Anti-Patterns (禁忌)

**NEVER (绝不)**:
- 在注入中包含 `recommended_solution` 或类似决策性字段
- 让阿赖耶识"主动触发"（必须在特定时机被查询）
- 注入过多内容干扰当前决策（遵守字数限制）
- 跳过写入门槛检查直接写入
- 允许阿赖耶识"覆盖"本体或分身的决策

**ALWAYS (始终)**:
- 在注入末尾标注"仅供参考，不影响决策"
- 遵守单向规则，只提供提示不提供结论
- 内观作为唯一的写入门户
- 写入前进行去重检查
- 保持注入内容精简（被动、稀疏、前置）

---

## Example: Full Workflow (完整工作流示例)

```
用户: "帮我实现一个视频转码功能"

=== 时机 1: 任务启动前 ===

本体查询阿赖耶识:
- 关键词: [视频, 转码, ffmpeg]
- 匹配锚点: [P001] FFmpeg 内存泄漏, [D007] 使用 NVENC 硬件加速

注入:
## [Alaya T1] 启动提示
⚠️ 相关风险:
- [P001] FFmpeg 在某格式下内存泄漏 - 建议限制并发数

=== 本体选择轨道: Feature Track ===
=== 耳分身分析需求 → 意分身设计方案 ===

=== 时机 2: 方案冻结后 ===

本体查询阿赖耶识:
- 设计中的技术选型: [FFmpeg, NVENC, 异步队列]
- 匹配决策: [D007] NVENC vs 软编码

注入:
## [Alaya T2] 设计参考
📜 历史决策:
- [D007] NVENC vs 软编码: 选择 NVENC
  - 理由: 性能提升 10x
  - 后果: 需要 NVIDIA GPU
  - 回滚: `ENCODER=libx264`

=== 斗战胜佛实现 → 舌分身测试 → 鼻分身审查 ===
=== 内观悟空反思 ===

=== 时机 3: 存档前 ===

内观标记候选锚点:
- [P_new] 发现 HEVC 格式兼容性问题

写入检查:
- 重复性: 否 (首次出现)
- 影响面: 是 (多格式支持)
- 可复用: 是 (通用视频处理)
- 门槛: 通过

去重检查:
- 相似锚点: 无

执行写入:
- 新增 [P002] HEVC 格式兼容性问题

=== 存档完成 ===
```

---

## Version History

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-01-12 | 初始版本 |

---

*此协议由意分身(架构悟空)设计，遵循 Wukong 八识架构*
