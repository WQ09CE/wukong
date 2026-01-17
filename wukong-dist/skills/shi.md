# 识 (Shi) - 信息存储模块

> **识**：含藏一切，跨越时空。

## 职责

识模块是 Wukong 的"记忆系统"，负责：
- **当前会话上下文** - 三态存储 (巨/常/缩)
- **永久锚点存储** - ADR 决策记录
- **跨会话知识传承** - 历史存档
- **PreCompact Hook 保存** - 压缩前自动保存

## 核心原则

> **只存"能影响未来决策"的东西**，而不是什么都存。

## 存储结构

> **用户级别存储** - 所有上下文存储在 `~/.wukong/context/`，支持跨项目沉淀

```
~/.wukong/context/
├── active/                         # 活跃会话 (按 session_id 隔离，避免多会话冲突)
│   └── {session_id}/
│       ├── compact.md              # 🔸 缩形态 (<500字)
│       └── metadata.json           # 元数据 (project, cwd, timestamp)
├── sessions/                       # 历史存档 (带项目名和时间戳)
│   └── {project}-{timestamp}-{session[:8]}/
│       ├── compact.md
│       ├── hui-output.json         # 慧模块完整输出
│       └── shi-result.json         # 识模块写入结果
├── anchors/                        # 锚点存储
│   ├── projects/                   # 按项目分文件
│   │   └── {project}.md            # 项目级锚点
│   └── global.md                   # 全局锚点 (跨项目)
└── index.json                      # 会话索引
```

## 三态上下文

### 🔸 缩形态 (Compact Form)

**适用**: 分身启动、上下文 >75%、跨会话传递
**限制**: < 500 字

```markdown
## 🔸 缩形态上下文

【任务】{一句话描述目标}

【已决策】
- {决策1}: {选择} (原因: {简要原因})
- {决策2}: {选择}

【约束】
- {必须遵守的规则1}
- {必须遵守的规则2}

【当前进度】
- 已完成: {完成项}
- 进行中: {当前任务}
- 待处理: {下一步}

【锚点引用】
- 见 [D001], [C002], [I003]
```

### 🔹 常形态 (Normal Form)

**适用**: 正常工作、分身间传递、上下文 50-75%
**限制**: 500-2000 字

```markdown
## 🔹 常形态上下文

### 任务背景
{2-3 句话描述背景和目标}

### 已完成工作
| 阶段 | 内容 | 产出 |
|------|------|------|
| 需求 | {描述} | requirements.md |
| 设计 | {描述} | design.md |

### 关键决策
| ID | 决策 | 选择 | 原因 |
|----|------|------|------|
| D001 | {决策} | {选择} | {原因} |

### 当前焦点
{详细描述当前任务}

### 接口约定
```python
{关键接口签名}
```

### 锚点索引
{相关锚点 ID}
```

### 🔶 巨形态 (Expanded Form)

**适用**: 调试复杂问题、上下文 <50%
**限制**: 无限制

存储位置: `.wukong/context/current/expanded.md`

## 锚点存储

### 锚点类型

| 类型 | 前缀 | 说明 | 示例 |
|------|------|------|------|
| 决策 | D | 架构/技术决策 | [D001] 使用 Ollama |
| 约束 | C | 必须遵守的规则 | [C001] 输出必须脱敏 |
| 接口 | I | 关键接口定义 | [I001] Agent.review() |
| 问题 | P | 已知问题/陷阱 | [P001] FFmpeg 内存泄漏 |
| 模式 | M | 可复用模式 | [M001] Repository 模式 |

### 锚点格式 (完整)

```markdown
## [D001] 使用 Ollama 作为本地 LLM

**日期**: 2024-01-15
**状态**: ✅ 生效

### Decision
使用 Ollama 作为代码审查的本地 LLM 后端。

### Alternatives
| 方案 | 优点 | 缺点 |
|------|------|------|
| OpenAI API | 能力强 | 成本高、数据出境 |
| Ollama | 免费、本地 | 需部署 |

### Why
1. 成本低
2. 数据本地化
3. 满足合规

### Impact
- `src/llm/`: LLM 接口模块
- `docker-compose.yaml`: 需要 Ollama 容器

### Rollback
设置 `LLM_BACKEND=openai`
```

### 锚点格式 (缩略)

```markdown
[D001] Ollama 作为本地 LLM
- Why: 成本低、数据本地化
- Impact: src/llm/, docker-compose
- Rollback: LLM_BACKEND=openai
```

### 锚点引用

在任何形态中，通过 `[D001]` 格式引用：

```markdown
根据 [D001]，我们使用 Ollama 作为 LLM 后端。
考虑到 [C001] 的脱敏要求，需要在返回前调用 Sanitizer。
```

## 写入规则

### 写入门槛 (由慧模块检查)

```
至少满足一项:
□ 重复 ≥ 2: 类似问题/决策出现两次以上
□ 影响大: 涉及架构、安全、性能、多模块
□ 可复用: 在其他项目/场景中有参考价值
```

### 去重检查

| 情况 | 处理 |
|------|------|
| 标题相似度 > 0.8 | 合并或更新 |
| 决策冲突 | 标记待审核 |
| 补充信息 | 追加到现有 |

### 写入流程

```
慧模块输出
    │
    ├─ 候选锚点列表
    │
    ▼
识模块写入
    │
    ├─ 1. 门槛检查 (不满足则跳过)
    ├─ 2. 去重检查 (重复则合并)
    └─ 3. 写入 anchors.md
```

## 形态切换

### 自动切换

```
上下文使用:
├── < 50%  → 🔶 巨形态
├── 50-70% → 🔹 常形态
├── 70-85% → 🔸 缩形态 + 提醒
├── 85-95% → 触发 DCP 修剪
└── > 95%  → 存档+重启
```

### 手动切换

| 命令 | 动作 |
|------|------|
| `存档` | 保存到 sessions/ |
| `加载 {name}` | 恢复历史会话 |
| `压缩` | 强制切换到缩形态 |
| `展开` | 强制切换到巨形态 |
| `锚点` | 显示所有锚点 |

## PreCompact Hook 集成

> 识模块接收来自 PreCompact Hook 的保存请求。

### Hook 输入

```json
{
  "hook_event_name": "PreCompact",
  "session_id": "xxx",
  "transcript_path": "/path/to/transcript.jsonl",
  "trigger": "auto",
  "cwd": "/path/to/project"
}
```

### 保存内容

1. **会话上下文** → `~/.wukong/context/active/{session_id}/compact.md`
2. **新锚点** → `~/.wukong/context/anchors/projects/{project}.md` (追加)
3. **完整存档** → `~/.wukong/context/sessions/{project}-{timestamp}-{session[:8]}/`
4. **会话索引** → `~/.wukong/context/index.json` (更新)

## 读取接口 (Read Interface)

> 供 Hui/Neiguan 模块查询识系统数据

### 查询项目锚点

```bash
# Get project name from git root or current directory
PROJECT_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")

# Read project-specific anchors
cat ~/.wukong/context/anchors/projects/${PROJECT_NAME}.md

# Read global anchors
cat ~/.wukong/context/anchors/global.md
```

### 查询会话数据

```bash
# List all sessions for a project (session_dir format: {project}-{timestamp}-{session[:8]})
ls -1d ~/.wukong/context/sessions/${PROJECT_NAME}-*/

# Read specific session context
cat ~/.wukong/context/sessions/${SESSION_DIR}/compact.md
cat ~/.wukong/context/sessions/${SESSION_DIR}/hui-output.json
cat ~/.wukong/context/sessions/${SESSION_DIR}/shi-result.json
```

### 通过 index.json 查询

```python
import json
import os

with open(os.path.expanduser("~/.wukong/context/index.json")) as f:
    index = json.load(f)

# Filter sessions by project
project_sessions = [s for s in index["sessions"]
                    if s["project_path"].endswith(project_name)]

# Get session directory (format: {project}-{timestamp}-{session[:8]})
for session in project_sessions:
    session_id = session["session_id"]
    timestamp = session.get("timestamp", "")
    # Session directory naming convention
    session_dir = f"{project_name}-{timestamp}-{session_id[:8]}"
```

### 文件路径速查

| 数据类型 | 路径 |
|----------|------|
| 会话索引 | `~/.wukong/context/index.json` |
| 项目锚点 | `~/.wukong/context/anchors/projects/{project}.md` |
| 全局锚点 | `~/.wukong/context/anchors/global.md` |
| 会话缩形态 | `~/.wukong/context/sessions/{session_dir}/compact.md` |
| 会话慧输出 | `~/.wukong/context/sessions/{session_dir}/hui-output.json` |
| 会话识结果 | `~/.wukong/context/sessions/{session_dir}/shi-result.json` |
| 活跃会话 | `~/.wukong/context/active/{session_id}/compact.md` |

> **Note**: `session_dir` format is `{project}-{timestamp}-{session_id[:8]}`

## 惯性提示 (读取)

> 识模块在特定时机被查询，提供惯性提示。

### 时机 1: 任务启动前 (T1)

**查询类型**: P(问题) + C(约束) + M(模式)
**适用分身**: 眼、身、舌、鼻

```markdown
## [识 T1] 启动提示

⚠️ **相关风险**:
- [P001] FFmpeg 内存泄漏

📌 **约束提醒**:
- [C001] 输出必须脱敏

🔄 **可复用模式**:
- [M001] Repository 模式

---
> 仅供参考，不影响决策
```

### 时机 2: 方案冻结后 (T2)

**查询类型**: D(决策) + I(接口)
**适用分身**: 意、身、鼻

```markdown
## [识 T2] 设计参考

📜 **历史决策**:
| ID | 决策 | 理由 |
|----|------|------|
| [D001] | Ollama | 成本低 |

🔌 **相关接口**:
- [I001] Agent.review()

🔙 **回滚经验**:
- D001: `LLM_BACKEND=openai`

---
> 仅供参考，决策权在本体
```

### API 函数 (hui-extract.py)

```python
# 获取 T1 惯性提示
from hui_extract import get_shi_t1_prompt
t1 = get_shi_t1_prompt('/path/to/project', ['API', '认证'])

# 获取 T2 惯性提示
from hui_extract import get_shi_t2_prompt
t2 = get_shi_t2_prompt('/path/to/project', ['数据库'])

# 根据分身类型自动选择
from hui_extract import get_shi_prompt_for_avatar
prompt = get_shi_prompt_for_avatar(cwd, '斗战胜佛', task_desc)
```

### 分身惯性提示配置

| 分身 | T1 (风险/约束) | T2 (决策/接口) | 说明 |
|------|----------------|----------------|------|
| 眼 | ✓ | - | 探索前提示已知问题 |
| 耳 | - | - | 需求分析无需历史包袱 |
| 意 | - | ✓ | 设计时参考历史决策 |
| 身 | ✓ | ✓ | 实现前获取完整上下文 |
| 舌 | ✓ | - | 测试时提示已知陷阱 |
| 鼻 | ✓ | ✓ | 审查时参考约束和决策 |

## 与其他模块关系

```
戒 (规则) ──→ 定 (复现) ──→ 慧 (反思) ──→ 识 (存储)
                                         │
                                         ├─ 写入: 接收慧的锚点候选
                                         ├─ 读取: T1/T2 惯性提示
                                         └─ Hook: PreCompact 触发保存
```

## 召唤分身时的上下文传递

```python
# 获取惯性提示 (根据分身类型自动选择 T1/T2)
shi_prompt = get_shi_prompt_for_avatar(cwd, '斗战胜佛', task_description)

Task(
    subagent_type="general-purpose",
    prompt=f"""
## 🔸 缩形态上下文
{read_compact_context(session_id)}

## 惯性提示
{shi_prompt}

## 你的任务
{task_description}

## 注意
如需更多上下文，可 Read("~/.wukong/context/active/{session_id}/compact.md")
"""
)
```

## Notepad 知识传承

> 跨任务积累和传递知识，避免重复犯错，利用成功模式。

### Notepad 结构

```
.wukong/notepads/{plan-name}/
├── requirements.md    # 需求规格书
├── design.md          # 架构设计
├── learnings.md       # 发现和经验
├── decisions.md       # 决策记录
├── issues.md          # 问题跟踪
├── review.md          # 审查结果
├── verification.md    # 验证记录
└── breakthroughs.md   # 技术突破记录 (Eureka!)
```

### 读取知识

**BEFORE starting any significant task:**

1. Check if notepad exists: `Glob(".wukong/notepads/{plan-name}/*.md")`
2. Read relevant entries: `learnings.md`, `issues.md`, `decisions.md`
3. Include in task context:

```markdown
## 继承的知识

### 需要遵循的模式
- {from learnings.md}

### 需要避免的问题
- {from issues.md}

### 已做出的决策
- {from decisions.md}
```

### 记录知识 (关键模板)

#### learnings.md

```markdown
# 学习记录: {Plan Name}

## {Date} - {Context}
- **发现**: {what you learned}
- **示例**: {code or reference}
- **应用场景**: {when to apply}

## 代码库规范
- {convention}

## 有效模式
- {pattern}
```

#### breakthroughs.md (Eureka!)

> 捕获技术突破，转化为可复用的知识资产。

**触发信号**: "终于搞定了！" / 解决阻塞>1小时 / 性能提升>50%

```markdown
## {Date} - {Breakthrough Title}

### 一句话总结
{achievement}

### 问题描述
{what was blocking}

### 核心洞察
{key insight}

### 可复用模式
{abstracted pattern}

### 标签
#performance #debugging #architecture
```

### 向分身传递知识

```python
Task(
    prompt=f"""
## 继承的知识

### 代码库规范
- 使用 snake_case 命名 Python 函数
- C++ 类使用 PascalCase

### 已知问题
- [P001] FFmpeg 在某些格式下会泄漏内存

### 已有决策
- [D001] 使用 ONNX Runtime 而非 TensorRT

## 你的任务
{actual task description}
"""
)
```

### 知识生命周期

```
1. 开始任务 └─ 读取现有知识
2. 任务执行中 └─ 记录发现
3. 任务完成 └─ 记录学习/决策/问题/验证
4. 下一个任务 └─ 继承知识，在此基础上构建
```

### 初始化 Notepad

```bash
cp -r .wukong/templates/notepad .wukong/notepads/{plan-name}
```

## 禁忌

**NEVER**:
- 不经门槛检查直接写入
- 存储临时性、一次性信息
- 在惯性提示中包含决策结论

**ALWAYS**:
- 遵守三态格式
- 去重后再写入
- 惯性提示末尾标注"仅供参考"
