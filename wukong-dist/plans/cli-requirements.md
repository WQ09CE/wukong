# Wukong CLI 需求规格书

> 版本: 1.0 | 日期: 2026-01-12

## 用户故事

1. 作为**开发者**，我想要**一键安装 Wukong 到项目**，以便**快速启用 AI Agent 协议**。
2. 作为**用户**，我想要**检查安装状态**，以便**确认配置正确**。
3. 作为**维护者**，我想要**查看版本信息**，以便**追踪和排查问题**。

## 核心需求 (Must Have)

| ID | 描述 | 验收标准 |
|----|------|----------|
| M1 | `wukong install [path]` | 复制规则/技能/命令到目标项目，创建工作目录 |
| M2 | `wukong version` | 显示 CLI 版本号 |
| M3 | `wukong doctor` | 检查 `.claude/` 和 `.wukong/` 配置完整性 |
| M4 | 彩色终端输出 | 成功/警告/错误使用不同颜色 |
| M5 | 错误处理 | 友好的错误信息，非零退出码 |

## 增强需求 (Should Have)

| ID | 描述 | 验收标准 |
|----|------|----------|
| S1 | `wukong update` | 从 GitHub 拉取最新规则并更新 |
| S2 | `wukong init` | 交互式初始化（选择性安装组件） |
| S3 | `--verbose` 标志 | 显示详细执行过程 |
| S4 | `--dry-run` 标志 | 预览操作但不执行 |

## 技术约束

- **语言**: Python 3.10+
- **依赖**: 最小化（优先使用标准库）
  - `click` 或 `typer` (CLI 框架，可选)
  - `rich` (终端美化，可选)
- **兼容**: macOS, Linux
- **安装**: `pip install wukong-cli` 或 `pipx install wukong-cli`
- **入口**: `wukong` 命令（通过 entry_points 注册）

## 命令规格

### `wukong install [path]`

**用途**: 安装 Wukong 协议到目标项目

**参数**:
- `path`: 目标项目路径（默认: 当前目录）

**行为**:
1. 确定源目录（本地 `.wukong/` 或从 GitHub 下载）
2. 创建目标目录结构:
   - `.claude/rules/` - 精简核心规则
   - `.claude/rules-extended/` - 完整规则（按需加载）
   - `.claude/commands/` - 命令
   - `.claude/skills/` - 技能
   - `.wukong/` - 工作数据
3. 复制文件
4. 初始化 anchors.md

**输出示例**:
```
Wukong Installer
Installing Wukong to /path/to/project...
  [ok] Created .claude/rules/
  [ok] Created .claude/skills/
  [ok] Created .wukong/
Done! Say 'Hello Wukong' in Claude Code.
```

### `wukong version`

**用途**: 显示版本信息

**输出示例**:
```
wukong-cli 0.1.0
```

### `wukong doctor`

**用途**: 检查安装健康状态

**检查项**:
- [ ] `.claude/rules/` 存在且包含核心规则
- [ ] `.claude/skills/` 存在且包含技能文件
- [ ] `.claude/commands/` 存在
- [ ] `.wukong/` 工作目录存在
- [ ] `anchors.md` 存在

**输出示例**:
```
Wukong Doctor
Checking /path/to/project...
  [ok] .claude/rules/00-wukong-core.md
  [ok] .claude/skills/ (7 files)
  [ok] .claude/commands/ (1 file)
  [ok] .wukong/context/anchors.md
  [warn] .wukong/notepads/ is empty

Status: Healthy (1 warning)
```

## 项目结构

```
wukong-cli/
├── pyproject.toml
├── src/
│   └── wukong_cli/
│       ├── __init__.py
│       ├── cli.py          # 命令入口
│       ├── install.py      # install 命令逻辑
│       ├── doctor.py       # doctor 命令逻辑
│       └── utils.py        # 工具函数（颜色、下载等）
└── tests/
    └── test_cli.py
```

## 验收标准

- [ ] `wukong install ~/test-project` 成功创建完整目录结构
- [ ] `wukong version` 显示版本号
- [ ] `wukong doctor` 正确检测缺失组件
- [ ] 所有命令在 macOS 和 Linux 上工作
- [ ] 错误情况返回非零退出码
- [ ] `--help` 显示帮助信息

## 未来考虑 (Won't Have Now)

- Windows 支持
- 自动升级机制
- 配置文件 (`~/.wukong/config.yaml`)
- 插件系统
