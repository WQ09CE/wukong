# Wukong

> Multi-Agent Orchestration Framework for Claude Code

A framework that transforms Claude Code into a coordinated engineering team through **specialized agents**, **verification pipelines**, and **persistent knowledge management**.

## Core Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           User                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Coordinator (Main Agent)                      │
│  • Task decomposition  • Agent dispatch  • Result verification   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Specialized Agents (6 Types)                   │
│  Explorer   Analyst   Reviewer   Tester   Implementer  Architect │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Verification Pipeline                         │
│   Compliance ──→ Reproducibility ──→ Reflection ──→ Storage     │
└─────────────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Separation of Concerns

Each agent has a strictly defined:
- **Responsibility Boundary** - What it can/cannot do
- **Output Contract** - Standardized output format
- **Tool Allowlist** - Permitted tool access

| Agent | Role | Can Do | Cannot Do | Tools |
|-------|------|--------|-----------|-------|
| Explorer | Search & Discovery | Search, locate files | Modify code | Glob, Grep, Read |
| Analyst | Requirements | Clarify requirements, define AC | Design or implement | Read |
| Reviewer | Code Review | Audit, scan issues | Fix code | Read, Grep |
| Tester | Testing & Docs | Write tests, documentation | Implement features | Read, Write, Bash |
| Implementer | Implementation | Write code, fix bugs | Skip verification | All |
| Architect | Design | System design, decisions | Write implementation | Read, Write(md) |

### 2. Verification Pipeline

Every agent output passes through a 4-stage verification:

```
Agent Output ──→ Compliance ──→ Reproducibility ──→ Reflection ──→ Storage
                    │                │                  │            │
                 Contract         Evidence           Extract       Persist
                 checking         levels             insights      anchors
```

**Evidence Levels:**
| Level | Description | Trust |
|-------|-------------|-------|
| L0 | Speculation ("should work...") | ❌ Reject |
| L1 | Reference (docs, comments) | ⚠️ Conditional |
| L2 | Local verification (tests pass) | ✅ Accept |
| L3 | Integration verification (CI pass) | ✅✅ Full trust |

### 3. Persistent Knowledge (Anchors)

Critical decisions persist across sessions as **anchors**:

| Type | Prefix | Purpose |
|------|--------|---------|
| Decision | D | Architecture/tech decisions |
| Constraint | C | Rules that must be followed |
| Interface | I | Key API definitions |
| Problem | P | Known issues/pitfalls |
| Pattern | M | Reusable patterns |

### 4. Parallel Execution

Independent tasks execute concurrently:
- **Max parallelism**: 3-4 agents
- **Same file**: Must serialize
- **Dependencies**: Execute in order

**Mandatory parallelization:**
- Modifying ≥2 independent files → One agent per file
- ≥2 independent modules → One agent per module

### 5. Context Management

Three context compression levels:

| Level | Size | Use Case |
|-------|------|----------|
| Expanded | Unlimited | Complex debugging |
| Normal | 500-2000 chars | Regular work |
| Compact | <500 chars | Cross-session, agent handoff |

### 6. Feedback Loop

Knowledge flows back to agents before task execution:

- **T1 (Pre-task)**: Query Problems/Constraints/Patterns → Risk warnings
- **T2 (Post-design)**: Query Decisions/Interfaces → Historical context

## Installation

```bash
# Clone and install
git clone https://github.com/anthropics/wukong.git
cd wukong
./install.sh /path/to/your/project

# Or install to current directory
./install.sh
```

The installer will:
1. Copy rules, skills, and commands to `.claude/`
2. Install hooks to `~/.wukong/hooks/`
3. Register hooks in `~/.claude/settings.json` (with confirmation)

## Usage

### Direct Agent Dispatch

```bash
/wukong @explorer search for authentication code
/wukong @architect design a caching layer
/wukong @implementer implement the login endpoint
/wukong @reviewer audit this PR
```

### Automatic Workflow Selection

```bash
/wukong add user authentication    # → Feature workflow
/wukong fix the login bug          # → Fix workflow
/wukong refactor the auth module   # → Refactor workflow
```

### Context Commands

| Command | Action |
|---------|--------|
| `/wukong reflect` | Extract insights and anchors |
| `/wukong compress` | Generate compact summary |
| `/wukong archive` | Save session to storage |
| `/wukong load {name}` | Restore previous session |
| `/wukong anchors` | Show all anchors |

## Project Structure

```
project/
├── .claude/
│   ├── rules/              # Auto-loaded rules
│   ├── skills/             # Agent skill definitions
│   └── commands/           # Command handlers
│
└── .wukong/
    ├── context/
    │   ├── anchors.md      # Persistent anchors
    │   ├── index.json      # Session index
    │   └── sessions/       # Session archives
    └── plans/              # Design documents
```

## Key Constraints

**Coordinator MUST delegate:**
- Multi-file exploration → Explorer (background)
- Code changes >10 lines → Implementer
- File creation → Implementer
- Build/test execution → Tester or Implementer

**Coordinator MAY handle directly:**
- Reading 1-2 files
- Single Glob/Grep query
- Simple verification checks
- User communication

## Documentation

- [System Overview](.wukong/plans/wukong-system-overview.md)
- [Core Rules](.claude/rules/00-wukong-core.md)
- [Agent Skills](.claude/skills/)
- [Mythology Version](README-mythology.md) - With Eastern philosophy terminology

## References

- [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode)
- [claude-code-settings](https://github.com/feiskyer/claude-code-settings)

## License

MIT
