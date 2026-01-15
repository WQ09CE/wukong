# Wukong Development Guide (for Claude)

> This file provides context for Claude to iterate on the Wukong project correctly.

## Directory Mapping

```
Source (repo)              →  Installed (user home)
─────────────────────────────────────────────────────
wukong-dist/rules/         →  ~/.claude/rules/
wukong-dist/skills/        →  ~/.claude/skills/
wukong-dist/commands/      →  ~/.claude/commands/
wukong-dist/hooks/         →  ~/.wukong/hooks/
wukong-dist/context/       →  ~/.wukong/context/
wukong-dist/templates/     →  ~/.wukong/templates/
```

**Key Insight:**
- `~/.claude/` = Claude Code configuration (rules, skills, commands)
- `~/.wukong/` = Runtime data (hooks, context, notepads, plans)

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
├── README.md              # User documentation
├── install.sh             # Installation script (Mac/Linux)
├── install.ps1            # Installation script (Windows)
├── wukong-dist/           # Source files (edit here!)
│   ├── rules/             # Core rules (auto-loaded)
│   ├── skills/            # Skill definitions
│   ├── commands/          # Custom commands
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

# Run installation test
./tests/test_install.sh

# Run all tests
python -m pytest tests/ -v
```

**What tests catch:**
- Wrong paths like `~/.wukong/skills/` (should be `~/.claude/skills/`)
- References to non-existent files
- Installation script failures

## Version Control

- **Always commit to repo** (wukong-dist/)
- **Never commit ~/.claude/** (it's user-specific)
- **Sync direction**: repo → home (not reverse, unless recovering edits)
