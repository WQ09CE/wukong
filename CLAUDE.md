# Wukong Development Guide (for Claude)

> This file provides context for Claude to iterate on the Wukong project correctly.
>
> **See also:** `AGENTS.md` for available agents and their capabilities.

## Core Protocol

Wukong 使用六根分身系统。**本体是调度者，不是执行者。**

- 核心协议: `~/.claude/rules/00-wukong-core.md`
- 分身定义: `~/.wukong/agents/*.md`
- 分身边界: `~/.claude/skills/jie.md`

调用分身使用 Task tool:
```
Task(subagent_type="eye", prompt="...")   # 眼分身 - 探索
Task(subagent_type="body", prompt="...")  # 斗战胜佛 - 实现
Task(subagent_type="mind", prompt="...")  # 意分身 - 设计
```

## Directory Mapping

```
Source (repo)              →  Installed (user home)
─────────────────────────────────────────────────────
wukong-dist/rules/         →  ~/.claude/rules/
wukong-dist/skills/        →  ~/.claude/skills/
wukong-dist/commands/      →  ~/.claude/commands/
wukong-dist/agents/        →  ~/.wukong/agents/      ← Agent definitions
wukong-dist/hooks/         →  ~/.wukong/hooks/
wukong-dist/context/       →  ~/.wukong/context/
wukong-dist/templates/     →  ~/.wukong/templates/
```

**Key Insight:**
- `~/.claude/` = Claude Code configuration (rules, skills, commands)
- `~/.wukong/` = Runtime data (hooks, context, agents, notepads, plans)

## Development Workflow

```
1. Edit source     →  wukong-dist/{rules,skills,commands}/*.md
2. Sync to home    →  cp wukong-dist/xxx ~/.claude/xxx
                      (or run install.sh for full sync)
3. Test changes    →  Use /wukong command to verify
4. Commit & push   →  git add && git commit && git push
```

**Reverse Sync** (if edited in ~/.claude first):
```bash
cp ~/.claude/rules/00-wukong-core.md wukong-dist/rules/
```

## Common Pitfalls

| Wrong | Correct | Note |
|-------|---------|------|
| `~/.wukong/skills/` | `~/.claude/skills/` | Skills are in .claude, not .wukong |
| `~/.wukong/rules/` | `~/.claude/rules/` | Rules are in .claude, not .wukong |
| Edit ~/.claude directly | Edit wukong-dist/ first | Source of truth is repo |

## Quick Commands

```bash
# Sync single file to installed location
cp wukong-dist/rules/00-wukong-core.md ~/.claude/rules/

# Sync all rules
cp wukong-dist/rules/*.md ~/.claude/rules/

# Sync all skills
cp wukong-dist/skills/*.md ~/.claude/skills/

# Full install (recommended for major changes)
./install.sh

# Reverse sync (from installed back to repo)
cp ~/.claude/rules/00-wukong-core.md wukong-dist/rules/
```

## Project Structure

```
wukong/
├── CLAUDE.md              # This file (Claude dev context)
├── AGENTS.md              # Agent registry (Claude Code reads this!)
├── README.md              # User documentation
├── install.sh             # Installation script (Mac/Linux)
├── install.ps1            # Installation script (Windows)
├── wukong-dist/           # Source files (edit here!)
│   ├── rules/             # Core rules (auto-loaded)
│   ├── skills/            # Skill definitions
│   ├── commands/          # Custom commands
│   ├── agents/            # Agent definitions (六根分身)
│   ├── hooks/             # PreCompact hooks etc.
│   ├── context/           # Context templates
│   └── templates/         # Notepad templates
├── wukong-cli/            # CLI tool (Python)
└── docs/                  # Additional documentation
```

## Testing Changes

After modifying rules or skills:

1. **Quick test**: Run `/wukong` and check behavior
2. **Verify paths**: `ls ~/.claude/skills/` to confirm files exist
3. **Check syntax**: Ensure markdown renders correctly

### Automated Tests

```bash
# Run path reference validation (catches wrong path errors)
python -m pytest tests/test_path_references.py -v

# Run all tests
python -m pytest tests/ -v
```

**What tests catch:**
- Wrong paths like `~/.wukong/skills/` (should be `~/.claude/skills/`)
- References to non-existent files
- Module import errors

### Tongue Avatar Test Checklist (舌分身测试清单)

> 当召唤舌分身(@舌/@tester)执行测试时，必须完成以下全部步骤：

```bash
# 1. Shell Lint (如有 .sh 文件修改)
shellcheck install.sh

# 2. Python 语法检查
python3 -m py_compile <modified_file.py>

# 3. 单元测试
python3 -m pytest tests/ -v --tb=short

# 4. 完整 CI Check (提交前必须)
./scripts/ci-check.sh
```

**验收标准:**
- [ ] shellcheck 无错误
- [ ] pytest 全部通过 (0 failed)
- [ ] CI check 全部通过

> **注意**: 只运行 pytest 不运行 CI check = 不完整测试

### Before Creating PR (IMPORTANT!)

> **[P005] Local Tests ≠ CI Tests**: Local environment has installed modules
> and dependencies that CI doesn't have. Always run the full CI check locally.

```bash
# Full CI check (mirrors GitHub Actions)
./scripts/ci-check.sh

# Quick check (skip installation test)
./scripts/ci-check.sh --quick
```

**CI Check includes:**
1. **Shell Lint** - `shellcheck install.sh` (style + errors)
2. **Python Tests** - `pytest tests/ -v` (all test files)
3. **Installation Test** - Verify install.sh works in clean directory

**Common CI failures and fixes:**

| CI Error | Cause | Fix |
|----------|-------|-----|
| ShellCheck SC2012 | `ls \| wc -l` | Use `find \| wc -l` |
| ShellCheck SC2129 | Multiple `>>` redirects | Use `{ } >> file` |
| ModuleNotFoundError | Test file missing sys.path | Add path setup at file top |
| pytest collection error | Non-pytest file in tests/ | Move to `scripts/` |

**Prerequisites:**
```bash
# macOS
brew install shellcheck

# Linux
apt install shellcheck

# Python
pip install pytest
```

## Version Control

- **Always commit to repo** (wukong-dist/)
- **Never commit ~/.claude/** (it's user-specific)
- **Sync direction**: repo → home (not reverse, unless recovering edits)
