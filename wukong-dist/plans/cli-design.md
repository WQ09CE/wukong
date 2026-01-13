# Wukong CLI 架构设计

> 版本: 1.0 | 日期: 2026-01-12 | 设计者: 架构悟空

## 设计决策

### 1. 依赖选择

**选择方案**: `click` + `rich` (可选依赖)

| 方案 | 优点 | 缺点 |
|------|------|------|
| 纯标准库 argparse | 零依赖 | 代码冗长，彩色输出需手写 |
| **click + rich** | 简洁声明式、丰富输出 | 需要两个依赖 |
| typer + rich | 类型提示、自动补全 | typer 较重，学习曲线 |

**理由**:
- `click` 是成熟的 CLI 标准，代码简洁（比 argparse 少 50% 代码）
- `rich` 提供开箱即用的彩色输出和表格
- 两者都是轻量级、广泛使用的库
- 可以通过 `extras` 使 `rich` 成为可选依赖

### 2. 项目结构

**选择方案**: 精简三文件结构

| 方案 | 文件数 | 适用场景 |
|------|--------|----------|
| 单文件 | 1 | <200行代码 |
| **精简结构** | 3-4 | 200-500行，本项目适用 |
| 标准结构 | 5+ | >500行，需要扩展 |

**理由**:
- 预估核心代码约 300 行，单文件会显得臃肿
- 但需求明确有限，不需要过度模块化
- 三文件足够：入口 + 命令 + 工具

### 3. 安装源策略

**选择方案**: 本地优先 + GitHub 备用

```
查找顺序:
1. 当前工作目录的 .wukong/ (开发模式)
2. CLI 安装包内置的 assets/ (打包模式)
3. GitHub 下载 (在线模式，未来实现)
```

**理由**:
- 本地开发时直接使用 `.wukong/` 源文件
- 发布时将资源文件打包进 wheel
- 保持离线可用，GitHub 作为更新源

## 最终架构

### 文件结构

```
wukong-cli/
├── pyproject.toml          # 项目配置 + 依赖 + entry_points
├── README.md               # 使用说明
├── src/
│   └── wukong_cli/
│       ├── __init__.py     # 版本号 + 包信息
│       ├── cli.py          # Click 命令定义 (入口)
│       └── core.py         # 业务逻辑 (install/doctor)
└── tests/
    └── test_cli.py         # 基础测试
```

**注意**: 故意省略 `utils.py`，工具函数直接放在 `core.py` 中，避免过度拆分。

### 模块职责

| 模块 | 职责 | 行数估计 |
|------|------|----------|
| `__init__.py` | 版本定义、包元信息 | ~10 |
| `cli.py` | Click 命令声明、参数解析、调用 core | ~80 |
| `core.py` | install/doctor 逻辑、文件操作、输出格式化 | ~200 |

### 核心接口

```python
# src/wukong_cli/__init__.py
__version__ = "0.1.0"

# src/wukong_cli/cli.py
import click
from rich.console import Console

console = Console()

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='显示详细信息')
@click.pass_context
def cli(ctx, verbose):
    """Wukong - AI Agent 协议安装工具"""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose

@cli.command()
def version():
    """显示版本信息"""
    from . import __version__
    click.echo(f"wukong-cli {__version__}")

@cli.command()
@click.argument('path', default='.', type=click.Path())
@click.option('--dry-run', is_flag=True, help='预览操作但不执行')
@click.pass_context
def install(ctx, path, dry_run):
    """安装 Wukong 到目标项目"""
    from .core import do_install
    do_install(path, dry_run=dry_run, verbose=ctx.obj['verbose'])

@cli.command()
@click.argument('path', default='.', type=click.Path(exists=True))
@click.pass_context
def doctor(ctx, path):
    """检查安装健康状态"""
    from .core import do_doctor
    do_doctor(path, verbose=ctx.obj['verbose'])

# src/wukong_cli/core.py
from pathlib import Path
from typing import List, Tuple
from rich.console import Console
from rich.table import Table

console = Console()

# 安装清单：(源相对路径, 目标相对路径, 描述)
INSTALL_MANIFEST = [
    (".wukong/rules/00-wukong-core.md", ".claude/rules/00-wukong-core.md", "核心规则"),
    (".wukong/rules/", ".claude/rules-extended/", "扩展规则"),
    (".wukong/skills/", ".claude/skills/", "技能文件"),
    (".wukong/commands/", ".claude/commands/", "命令文件"),
]

def find_source_dir() -> Path:
    """查找 Wukong 源文件目录"""
    # 1. 当前目录 (开发模式)
    if Path(".wukong").exists():
        return Path(".wukong")
    # 2. 包内置资源 (打包模式)
    pkg_assets = Path(__file__).parent / "assets"
    if pkg_assets.exists():
        return pkg_assets
    raise FileNotFoundError("找不到 Wukong 源文件")

def do_install(target: str, dry_run: bool = False, verbose: bool = False) -> int:
    """执行安装"""
    target_path = Path(target).resolve()
    console.print(f"[bold]Wukong Installer[/bold]")
    console.print(f"Installing to {target_path}...")

    try:
        source = find_source_dir()
    except FileNotFoundError as e:
        console.print(f"[red][error][/red] {e}")
        return 1

    # 创建目录结构
    dirs_to_create = [
        ".claude/rules",
        ".claude/rules-extended",
        ".claude/skills",
        ".claude/commands",
        ".wukong/context",
        ".wukong/notepads",
    ]

    for dir_path in dirs_to_create:
        full_path = target_path / dir_path
        if dry_run:
            console.print(f"  [dim]would create[/dim] {dir_path}/")
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            if verbose:
                console.print(f"  [green][ok][/green] Created {dir_path}/")

    # 复制文件
    import shutil
    for src_rel, dst_rel, desc in INSTALL_MANIFEST:
        src_path = source / src_rel.lstrip(".wukong/")
        dst_path = target_path / dst_rel

        if not src_path.exists():
            console.print(f"  [yellow][skip][/yellow] {desc} (源不存在)")
            continue

        if dry_run:
            console.print(f"  [dim]would copy[/dim] {desc}")
        else:
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dst_path)
            console.print(f"  [green][ok][/green] {desc}")

    # 初始化 anchors.md
    anchors_path = target_path / ".wukong/context/anchors.md"
    if not anchors_path.exists() and not dry_run:
        anchors_path.write_text("# Anchors\n\n> 关键决策和约束记录\n")
        console.print(f"  [green][ok][/green] 初始化 anchors.md")

    console.print(f"\n[bold green]Done![/bold green] Say 'Hello Wukong' in Claude Code.")
    return 0

def do_doctor(target: str, verbose: bool = False) -> int:
    """检查安装状态"""
    target_path = Path(target).resolve()
    console.print(f"[bold]Wukong Doctor[/bold]")
    console.print(f"Checking {target_path}...\n")

    checks = [
        (".claude/rules/00-wukong-core.md", "file", "核心规则"),
        (".claude/skills/", "dir", "技能文件"),
        (".claude/commands/", "dir", "命令文件"),
        (".wukong/context/anchors.md", "file", "锚点文件"),
        (".wukong/notepads/", "dir", "笔记目录"),
    ]

    ok_count = 0
    warn_count = 0
    error_count = 0

    for rel_path, check_type, desc in checks:
        full_path = target_path / rel_path

        if check_type == "file":
            if full_path.exists():
                console.print(f"  [green][ok][/green] {rel_path}")
                ok_count += 1
            else:
                console.print(f"  [red][missing][/red] {rel_path}")
                error_count += 1
        else:  # dir
            if full_path.exists() and full_path.is_dir():
                file_count = len(list(full_path.iterdir()))
                if file_count > 0:
                    console.print(f"  [green][ok][/green] {rel_path} ({file_count} files)")
                    ok_count += 1
                else:
                    console.print(f"  [yellow][warn][/yellow] {rel_path} (empty)")
                    warn_count += 1
            else:
                console.print(f"  [red][missing][/red] {rel_path}")
                error_count += 1

    # 状态总结
    console.print()
    if error_count > 0:
        console.print(f"[red]Status: Unhealthy[/red] ({error_count} errors, {warn_count} warnings)")
        return 1
    elif warn_count > 0:
        console.print(f"[yellow]Status: Healthy[/yellow] ({warn_count} warnings)")
        return 0
    else:
        console.print(f"[green]Status: Healthy[/green]")
        return 0
```

### 数据流

```
┌─────────────────────────────────────────────────────────────┐
│                        用户输入                              │
│                  wukong install ./my-project                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      cli.py (Click)                          │
│  - 解析命令: install                                         │
│  - 解析参数: path="./my-project"                             │
│  - 解析标志: --verbose, --dry-run                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     core.py (业务逻辑)                       │
│  1. find_source_dir() → 定位源文件                          │
│  2. 创建目录结构                                             │
│  3. 复制文件 (INSTALL_MANIFEST)                             │
│  4. 初始化 anchors.md                                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     终端输出 (Rich)                          │
│  Wukong Installer                                            │
│  Installing to /path/to/my-project...                        │
│    [ok] Created .claude/rules/                               │
│    [ok] 核心规则                                             │
│  Done! Say 'Hello Wukong' in Claude Code.                   │
└─────────────────────────────────────────────────────────────┘
```

### pyproject.toml 配置

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "wukong-cli"
version = "0.1.0"
description = "Wukong AI Agent Protocol Installer"
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
authors = [{ name = "Wukong Team" }]
dependencies = [
    "click>=8.0",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0"]

[project.scripts]
wukong = "wukong_cli.cli:cli"

[tool.hatch.build.targets.wheel]
packages = ["src/wukong_cli"]
```

## 实施计划

### Phase 1: 骨架 (斗战胜佛 Task 1)

1. 创建 `wukong-cli/` 目录结构
2. 编写 `pyproject.toml`
3. 实现 `cli.py` 命令框架 (version 命令)
4. 验证: `pip install -e .` + `wukong version`

**产出**: 可安装的空壳 CLI

### Phase 2: Install 命令 (斗战胜佛 Task 2)

1. 实现 `core.py` 的 `find_source_dir()`
2. 实现 `do_install()` 完整逻辑
3. 添加 `--dry-run` 和 `--verbose` 支持
4. 验证: `wukong install /tmp/test-project`

**产出**: 功能完整的 install 命令

### Phase 3: Doctor 命令 (斗战胜佛 Task 3)

1. 实现 `do_doctor()` 检查逻辑
2. 添加彩色状态输出
3. 验证: `wukong doctor /tmp/test-project`

**产出**: 功能完整的 doctor 命令

### Phase 4: 测试与打包 (舌分身)

1. 编写基础测试 `test_cli.py`
2. 验证 `pip install .` 打包
3. 测试在空目录运行

**验收标准**:
- [ ] `wukong version` 输出版本号
- [ ] `wukong install ./test` 创建完整结构
- [ ] `wukong doctor ./test` 显示健康状态
- [ ] `wukong --help` 显示帮助
- [ ] 错误情况返回非零退出码

---

## 设计备注

### 为什么不用单文件?

虽然单文件 (`wukong.py`) 更简单，但:
- Click 命令定义 + 业务逻辑混在一起会超过 400 行
- 测试时难以 mock 业务逻辑
- 未来添加 `update` 命令时扩展困难

三文件是当前需求的最优平衡点。

### 为什么选择 Rich 而不是手写 ANSI?

```python
# 手写 ANSI (繁琐)
print(f"\033[32m[ok]\033[0m Created .claude/rules/")

# Rich (简洁)
console.print("[green][ok][/green] Created .claude/rules/")
```

Rich 还提供 Windows 兼容性和表格/进度条等功能，未来扩展方便。

### 离线优先策略

CLI 不应该依赖网络才能工作。GitHub 下载只用于 `update` 命令（Should Have），install 命令完全离线可用。
