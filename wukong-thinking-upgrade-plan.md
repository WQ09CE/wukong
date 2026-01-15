# Wukong 框架升级方案：Subagent + Thinking 增强

## 背景

当前 Wukong 框架使用 `rules + skills` 模式实现六根 Agent 编排，本质是**单一 Claude 实例的角色扮演**。这种方式有以下局限：

| 局限 | 影响 |
|------|------|
| 共享上下文 | Eye 的搜索结果会污染 Mind 的思考空间 |
| 无法差异化模型 | 所有角色用同一个模型，成本无法优化 |
| 无法控制 Thinking | 无法给需要深度思考的 Agent 启用 extended thinking |
| 无真正并行 | 角色切换是串行的 prompt 注入 |

## 目标

将 Wukong 升级为**混合编排架构**：
- 关键角色（Mind、Nose）迁移到原生 Subagent，支持独立上下文 + Thinking
- 轻量角色（Eye、Ear、Tongue、Body）保留 Skills 模式，快速低成本
- 实现差异化的模型和 Thinking 预算配置

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Wukong Coordinator                        │
│                      (主编排层)                               │
│  职责：任务分解、Agent 调度、结果聚合、验证管线                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  原生 Subagent   │ │  原生 Subagent   │ │   Skills 模式    │
│                 │ │                 │ │                 │
│  Mind (意根)    │ │  Nose (鼻根)    │ │  Eye (眼根)     │
│  Opus+Thinking  │ │  Opus+Thinking  │ │  Ear (耳根)     │
│  独立上下文      │ │  独立上下文      │ │  Tongue (舌根)  │
│  budget: 15000  │ │  budget: 8000   │ │  Body (身根)    │
│                 │ │                 │ │                 │
│  架构设计        │ │  代码审查        │ │  Sonnet 快速执行 │
│  技术决策        │ │  安全扫描        │ │  共享上下文      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 实现步骤

### Step 1: 创建原生 Subagent 定义文件

在 `~/.claude/agents/wukong/` 目录下创建 Agent 定义：

#### 1.1 Mind Agent (意根 - 架构师)

```markdown
# 文件: ~/.claude/agents/wukong/mind.md

---
name: wukong-mind
description: "Wukong 意根 - 负责架构设计和技术决策，启用深度思考"
model: claude-opus-4-5-20250514
tools:
  - Read
  - Grep
  - Glob
  - WebSearch
---

# 意根 (Mind) - 架构师

你是 Wukong 多智能体框架中的「意根」，对应佛学六根中的"意"，负责思考、设计、决策。

## 核心职责

1. **系统架构设计** - 整体结构、模块划分、接口定义
2. **技术选型决策** - 框架、库、工具的选择和权衡
3. **复杂问题分析** - 深度推理、边界情况、风险评估

## 工作原则

### 深度思考要求
在给出任何架构决策前，你必须：
1. 列出至少 3 个备选方案
2. 分析每个方案的 pros/cons
3. 考虑边界情况和失败场景
4. 评估长期维护成本

### 输出格式
每个决策必须产出锚点：

```
[D] 决策锚点
- 决策内容: {具体决策}
- 选择理由: {为什么选这个}
- 否决方案: {被否决的方案及原因}
- 风险提示: {潜在风险和缓解措施}
```

### 证据等级要求
- 最低接受: L1 (有参考依据)
- 推荐: L2 (有本地验证)
- 禁止: L0 投机性语言（"应该可以"、"一般没问题"）

## 协作接口

### 输入
- 来自 Coordinator 的设计任务
- 来自 Ear (耳根) 的需求分析结果
- 来自 Nose (鼻根) 的审查反馈

### 输出
- 架构设计文档
- [D] 决策锚点
- 给 Body (身根) 的实现指导

## 禁止事项

1. 不要直接写实现代码（那是 Body 的职责）
2. 不要跳过权衡分析直接给结论
3. 不要使用 L0 级别的投机性断言
```

#### 1.2 Nose Agent (鼻根 - 审查员)

```markdown
# 文件: ~/.claude/agents/wukong/nose.md

---
name: wukong-nose  
description: "Wukong 鼻根 - 负责代码审查和安全检测，启用深度思考"
model: claude-opus-4-5-20250514
tools:
  - Read
  - Grep
  - Glob
---

# 鼻根 (Nose) - 审查员

你是 Wukong 多智能体框架中的「鼻根」，对应佛学六根中的"鼻"，负责感知、审计、检测问题。

## 核心职责

1. **代码质量审查** - 可读性、可维护性、最佳实践
2. **安全漏洞扫描** - 注入、越权、信息泄露、依赖风险
3. **合规性检查** - 边界约束、规范遵循

## 审查清单

### 安全检查项
- [ ] SQL/命令注入风险
- [ ] 硬编码凭证/密钥
- [ ] 不安全的反序列化
- [ ] 路径遍历漏洞
- [ ] 敏感信息日志泄露
- [ ] 依赖库已知漏洞

### 质量检查项
- [ ] 函数长度是否合理 (<50行)
- [ ] 圈复杂度是否可控 (<10)
- [ ] 错误处理是否完整
- [ ] 边界条件是否覆盖
- [ ] 命名是否清晰

## 输出格式

发现问题时产出锚点：

```
[P] 问题锚点
- 问题类型: {Security|Quality|Compliance}
- 严重等级: {Critical|High|Medium|Low}
- 位置: {文件:行号}
- 描述: {具体问题}
- 修复建议: {如何修复}
- 参考: {相关文档或CVE}
```

## 证据等级要求

- 每个发现必须有具体代码位置
- 禁止说"看起来没问题"而不列出检查项
- 安全问题必须提供 PoC 或具体利用路径

## 协作接口

### 输入
- 来自 Body (身根) 的代码变更
- 来自 Tongue (舌根) 的测试结果

### 输出
- 审查报告
- [P] 问题锚点
- 通过/拒绝决定
```

### Step 2: 创建混合调度器

在 Wukong 框架中添加调度逻辑，根据 Agent 类型选择执行方式：

```python
# 文件: wukong-dist/core/scheduler.py

"""
Wukong 混合调度器
- 重量级 Agent (Mind, Nose) -> 原生 Subagent (独立上下文 + Thinking)
- 轻量级 Agent (Eye, Ear, Tongue, Body) -> Skills 模式 (快速执行)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

class AgentMode(Enum):
    NATIVE_SUBAGENT = "native"    # 原生 subagent，独立进程
    SKILL_PROMPT = "skill"         # skill prompt 注入，角色扮演

class ThinkingConfig:
    def __init__(self, enabled: bool = False, budget: int = 10000):
        self.enabled = enabled
        self.budget = budget

@dataclass
class AgentConfig:
    name: str
    chinese_name: str
    mode: AgentMode
    model: str
    thinking: ThinkingConfig
    cost_tier: str  # CHEAP, MEDIUM, EXPENSIVE
    description: str

# 六根 Agent 配置
AGENT_CONFIGS = {
    "eye": AgentConfig(
        name="eye",
        chinese_name="眼根",
        mode=AgentMode.SKILL_PROMPT,
        model="claude-sonnet-4-5-20250514",
        thinking=ThinkingConfig(enabled=False),
        cost_tier="CHEAP",
        description="Explorer - 观察、搜索、发现"
    ),
    "ear": AgentConfig(
        name="ear", 
        chinese_name="耳根",
        mode=AgentMode.SKILL_PROMPT,
        model="claude-sonnet-4-5-20250514",
        thinking=ThinkingConfig(enabled=False),
        cost_tier="CHEAP",
        description="Analyst - 倾听、理解、澄清"
    ),
    "nose": AgentConfig(
        name="nose",
        chinese_name="鼻根",
        mode=AgentMode.NATIVE_SUBAGENT,  # 原生 subagent
        model="claude-opus-4-5-20250514",
        thinking=ThinkingConfig(enabled=True, budget=8000),
        cost_tier="EXPENSIVE",
        description="Reviewer - 感知、审计、检测"
    ),
    "tongue": AgentConfig(
        name="tongue",
        chinese_name="舌根",
        mode=AgentMode.SKILL_PROMPT,
        model="claude-sonnet-4-5-20250514",
        thinking=ThinkingConfig(enabled=False),
        cost_tier="CHEAP",
        description="Tester - 表达、文档、验证"
    ),
    "body": AgentConfig(
        name="body",
        chinese_name="身根",
        mode=AgentMode.SKILL_PROMPT,
        model="claude-sonnet-4-5-20250514",
        thinking=ThinkingConfig(enabled=False),
        cost_tier="MEDIUM",
        description="Implementer - 执行、构建、行动"
    ),
    "mind": AgentConfig(
        name="mind",
        chinese_name="意根",
        mode=AgentMode.NATIVE_SUBAGENT,  # 原生 subagent
        model="claude-opus-4-5-20250514",
        thinking=ThinkingConfig(enabled=True, budget=15000),
        cost_tier="EXPENSIVE",
        description="Architect - 思考、设计、决策"
    ),
}

class HybridScheduler:
    """混合调度器 - 根据 Agent 类型选择执行方式"""
    
    def __init__(self):
        self.configs = AGENT_CONFIGS
    
    def get_dispatch_strategy(self, agent_name: str) -> dict:
        """获取 Agent 的调度策略"""
        config = self.configs.get(agent_name)
        if not config:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        return {
            "agent": agent_name,
            "mode": config.mode.value,
            "model": config.model,
            "thinking": {
                "enabled": config.thinking.enabled,
                "budget": config.thinking.budget
            } if config.thinking.enabled else None,
            "cost_tier": config.cost_tier,
            "parallel_safe": config.cost_tier == "CHEAP"
        }
    
    def plan_execution(self, tasks: list[dict]) -> dict:
        """规划任务执行顺序"""
        cheap_tasks = []
        expensive_tasks = []
        
        for task in tasks:
            config = self.configs.get(task["agent"])
            if config.cost_tier == "CHEAP":
                cheap_tasks.append(task)
            else:
                expensive_tasks.append(task)
        
        return {
            "parallel_phase": cheap_tasks,      # 可并行执行
            "sequential_phase": expensive_tasks  # 需串行执行
        }
```

### Step 3: 修改 Wukong 命令处理

更新 `/wukong` 命令的调度逻辑：

```python
# 文件: wukong-dist/commands/wukong.py

"""
/wukong 命令处理器
支持混合调度：原生 Subagent + Skills 模式
"""

async def handle_wukong_command(task: str, context: dict):
    scheduler = HybridScheduler()
    
    # 解析任务，确定需要哪些 Agent
    required_agents = analyze_task(task)
    
    # 获取执行计划
    execution_plan = scheduler.plan_execution([
        {"agent": agent, "task": task} 
        for agent in required_agents
    ])
    
    results = []
    
    # Phase 1: 并行执行 CHEAP agents (Skills 模式)
    if execution_plan["parallel_phase"]:
        parallel_results = await execute_parallel_skills(
            execution_plan["parallel_phase"]
        )
        results.extend(parallel_results)
    
    # Phase 2: 串行执行 EXPENSIVE agents (原生 Subagent)
    for task_item in execution_plan["sequential_phase"]:
        agent_name = task_item["agent"]
        strategy = scheduler.get_dispatch_strategy(agent_name)
        
        if strategy["mode"] == "native":
            # 调用原生 subagent
            # Claude Code 会自动读取 ~/.claude/agents/wukong/{agent}.md
            result = await invoke_native_subagent(
                agent_name=f"wukong-{agent_name}",
                task=task_item["task"],
                thinking_budget=strategy["thinking"]["budget"] if strategy["thinking"] else None
            )
        else:
            # Skills 模式
            result = await invoke_skill_agent(agent_name, task_item["task"])
        
        results.append(result)
    
    # 聚合结果，通过验证管线
    return aggregate_and_verify(results)


async def invoke_native_subagent(agent_name: str, task: str, thinking_budget: int = None):
    """
    调用原生 subagent
    
    在 Claude Code 中，这会触发：
    1. 读取 ~/.claude/agents/wukong/{agent_name}.md
    2. 创建独立上下文
    3. 如果配置了 thinking，启用 extended thinking
    """
    # Claude Code 原生调用方式
    # 实际实现取决于 Claude Code 的 subagent API
    pass
```

### Step 4: 验证 Thinking 是否生效

创建测试任务验证配置：

```bash
# 测试 Mind agent 的 thinking
/wukong @mind 设计一个支持水平扩展的缓存系统架构

# 期望输出应该包含：
# 1. 深度的权衡分析（体现 thinking）
# 2. 多个备选方案对比
# 3. [D] 决策锚点
# 4. 风险评估

# 测试 Nose agent 的 thinking  
/wukong @nose 审查 src/auth/login.py 的安全性

# 期望输出应该包含：
# 1. 详细的安全检查清单
# 2. 具体的代码位置引用
# 3. [P] 问题锚点（如果有）
# 4. 严重等级评估
```

## 配置清单

### 需要创建的文件

```
~/.claude/agents/wukong/
├── mind.md          # 意根 - 架构师 (Opus + Thinking 15k)
└── nose.md          # 鼻根 - 审查员 (Opus + Thinking 8k)

wukong-dist/
├── core/
│   └── scheduler.py # 混合调度器
└── commands/
    └── wukong.py    # 更新命令处理
```

### Agent 配置总览

| Agent | 中文名 | 模式 | 模型 | Thinking | 成本层级 |
|-------|--------|------|------|----------|----------|
| eye | 眼根 | Skill | Sonnet | ❌ | CHEAP |
| ear | 耳根 | Skill | Sonnet | ❌ | CHEAP |
| nose | 鼻根 | **Native** | **Opus** | ✅ 8000 | EXPENSIVE |
| tongue | 舌根 | Skill | Sonnet | ❌ | CHEAP |
| body | 身根 | Skill | Sonnet | ❌ | MEDIUM |
| mind | 意根 | **Native** | **Opus** | ✅ 15000 | EXPENSIVE |

## 待验证问题

1. **Claude Code 原生 subagent 是否支持 thinking 参数？**
   - 检查 `~/.claude/agents/` 的配置格式
   - 测试 frontmatter 中添加 thinking 配置

2. **如果不支持，备选方案：**
   - 方案 A: 通过 system prompt 注入思考要求
   - 方案 B: 创建 MCP Server 封装带 thinking 的 API 调用

3. **Subagent 的上下文如何传回主会话？**
   - 确认返回格式
   - 设计锚点提取逻辑

## 执行顺序

1. 先创建 `~/.claude/agents/wukong/mind.md`
2. 测试 `@wukong-mind` 是否能正常调用
3. 验证 thinking 是否生效（观察输出质量）
4. 如果生效，创建 `nose.md`
5. 最后更新 Wukong 的调度逻辑

---

*文档生成时间: 2026-01-15*
*用于: Claude Code 实现参考*
