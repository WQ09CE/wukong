# Wukong 🐵

> 悟空多分身工作流 - Claude Code 的多智能体编排框架
>
> "需求即取经路，代码即降妖伏魔。"

**Wukong** 将 Claude Code 转化为高效的工程团队。本体专注用户交互，六根分身并行执行专业任务。

## 🌟 Features

### 六根分身系统

> **六根**源自佛教，指眼、耳、鼻、舌、身、意六种感知器官。

| 六根 | 分身 | 能力 |
|------|------|------|
| 👁️ 眼 | 眼分身 | 探索·搜索 |
| 👂 耳 | 耳分身 | 需求·理解 |
| 👃 鼻 | 鼻分身 | 审查·检测 |
| 👅 舌 | 舌分身 | 测试·文档 |
| ⚔️ 身 | 斗战胜佛 | 实现·行动 |
| 🧠 意 | 意分身 | 设计·决策 |
| 🔮 超越 | 内观悟空 | 反思·锚点 |

### 核心能力

- **动态轨道**: Feature / Fix / Refactor / Direct 自动选择
- **筋斗云并行**: 无依赖任务同时执行，最大 3-4 个分身
- **规则分层**: 精简规则启动加载 (98行)，详细规则按需读取
- **如意金箍棒**: 上下文管理，显式命令触发
- **验证金规**: "分身可能说谎" - 必须亲自验证

## 🚀 Installation

### 自动安装 (Mac/Linux)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/WQ09CE/wukong/main/install.sh)"
```

### 安装到指定项目

```bash
git clone https://github.com/WQ09CE/wukong.git
cd wukong
./install.sh /path/to/your/project
```

## 📂 Structure

安装后的目录结构：

```
your-project/
├── .claude/                      # Claude Code 运行时
│   ├── rules/                    # 精简核心规则 (启动加载)
│   │   └── 00-wukong-core.md
│   ├── rules-extended/           # 扩展规则 (按需加载)
│   │   ├── avatars.md
│   │   ├── orchestration.md
│   │   ├── verification.md
│   │   ├── wisdom.md
│   │   └── ruyi.md
│   ├── skills/                   # 分身技能 (召唤时加载)
│   │   ├── explorer.md
│   │   ├── architect.md
│   │   ├── implementer.md
│   │   └── ...
│   └── commands/
│       └── wukong.md             # /wukong 命令入口
│
└── .wukong/                      # 工作数据
    ├── context/                  # 上下文管理
    │   ├── sessions/             # 会话存档
    │   └── templates/
    ├── notepads/                 # 知识笔记本
    ├── plans/                    # 执行计划
    └── templates/                # 模板文件
```

## 🎮 Usage

### 基本使用

```
/wukong 你好                    # 激活悟空
/wukong 添加用户登录功能         # Feature Track (自动选择)
/wukong 修复支付模块崩溃         # Fix Track (自动选择)
/wukong 重构遗留的认证代码       # Refactor Track (自动选择)
```

### 显式指定分身 (@语法)

使用 `@` 语法可以绕过轨道选择，直接指定分身：

```
/wukong @意 设计缓存架构         # 直接召唤意分身
/wukong @眼 探索认证模块         # 直接召唤眼分身
/wukong @斗战胜佛 实现登录接口   # 直接召唤斗战胜佛
/wukong @鼻 审查这个 PR          # 直接召唤鼻分身
```

| @ 标记 | 分身 | 英文别名 |
|--------|------|----------|
| `@眼` | 眼分身 | `@explorer` |
| `@耳` | 耳分身 | `@analyst` |
| `@鼻` | 鼻分身 | `@reviewer` |
| `@舌` | 舌分身 | `@tester` |
| `@身` / `@斗战胜佛` | 斗战胜佛 | `@impl` |
| `@意` | 意分身 | `@architect` |
| `@内观` | 内观悟空 | `@reflect` |

### 上下文管理命令

| 命令 | 动作 |
|------|------|
| `/wukong 内观` | 反思 + 提取锚点 + 三态摘要 |
| `/wukong 压缩` | 生成缩形态摘要 (<500字) |
| `/wukong 存档` | 保存到 `.wukong/context/sessions/` |
| `/wukong 加载 {name}` | 恢复历史会话 |
| `/wukong 锚点` | 显示关键决策/约束 |

### 三态形态

- 🔶 **巨形态** - 完整详细信息
- 🔹 **常形态** - 结构化摘要
- 🔸 **缩形态** - 核心要点 (跨会话传递用)

## 🔧 Customization

### 添加自定义技能

在 `.claude/skills/` 下创建新的 `.md` 文件，悟空会自动发现：

```markdown
# My Custom Skill

You are **自定义分身** - ...

## Capabilities
...
```

### 修改核心规则

- 精简规则: `.claude/rules/00-wukong-core.md`
- 扩展规则: `.claude/rules-extended/*.md`

## 📜 License

MIT
