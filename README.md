# Wukong

> **Six Roots in Parallel, Four Pillars Standing Guard**

Give Claude Code memory, teach it reflection, enable continuous evolution.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![中文文档](https://img.shields.io/badge/docs-%E4%B8%AD%E6%96%87-blue)](README-zh.md)

---

## What is Wukong?

**Wukong** is a multi-agent orchestration framework designed specifically for Claude Code. It transforms a single AI assistant into a **coordinated engineering team** with specialized roles, and through its innovative **verification pipeline** and **knowledge persistence system**, makes your AI assistant smarter over time.

```
┌─────────────────────────────────────────────────────────────────┐
│                           User                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Wukong Coordinator                            │
│      Task Decomposition · Agent Dispatch · Verification          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Six Roots      │ │   Verification   │ │   Knowledge     │
│   Agent System   │ │   Pipeline       │ │   System        │
│  Parallel Exec   │ │  Rules+Evidence  │ │  Reflect+Store  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Three Core Highlights

### 1. Six Roots - Multi-Agent Collaboration for Complex Engineering

> One command, automatic task decomposition, parallel execution, aggregated results

Inspired by the Buddhist concept of "Six Roots" (six sense organs), Wukong decomposes complex engineering tasks across six specialized agents:

| Root | Agent | Responsibility | Best For |
|:----:|-------|----------------|----------|
| 👁️ Eye | Explorer | Observe · Search · Discover | Codebase exploration, file search, dependency analysis |
| 👂 Ear | Analyst | Listen · Understand · Clarify | Requirements analysis, boundary clarification |
| 👃 Nose | Reviewer | Sense · Audit · Detect | Code review, security scanning, compliance |
| 👅 Tongue | Tester | Express · Document · Verify | Test writing, documentation, API specs |
| ⚔️ Body | Implementer | Execute · Build · Act | Code implementation, bug fixes, features |
| 🧠 Mind | Architect | Think · Design · Decide | System design, tech decisions, architecture |

**Intelligent Scheduling:**
- **Cost-Aware Routing** - CHEAP agents run 10+ in parallel, EXPENSIVE agents block for quality
- **Dynamic Tracks** - Feature/Fix/Refactor auto-selects optimal workflow
- **Extensible** - Custom skill files enable unlimited capability expansion

```bash
# Explicit agent dispatch
/wukong @explorer search for authentication implementation
/wukong @architect design a caching strategy
/wukong @implementer implement the login endpoint

# Automatic track selection
/wukong add user authentication    # → Feature track: Ear→Mind→Body→Tongue→Nose
/wukong fix the login bug          # → Fix track: Eye→Body→Tongue
```

---

### 2. Verification Pipeline - Double Insurance for Quality

> Say goodbye to "it should work" - every conclusion backed by verifiable evidence

```
Agent Output ──→ Compliance ──→ Reproducibility ──→ Delivery
                    │                │
                    │                └─ Evidence Level Check
                    │                   L0 Speculation → ❌ Reject
                    │                   L1 Reference   → ⚠️ Conditional
                    │                   L2 Local Test  → ✅ Accept
                    │                   L3 CI Pass     → ✅✅ Full Trust
                    │
                    └─ Contract Completeness
                       Do/Don't Boundary Check
                       Sensitive Info Scanning
```

| Module | Role | Golden Rule |
|--------|------|-------------|
| **Compliance** | Rule boundary checking | Violations get rejected, no exceptions |
| **Reproducibility** | Evidence verification | **No evidence = Not done** |

**Auto-Intercepted Red Flags:**
- "Should work..." / "Probably can..." → L0 speculation, blocked
- "No problem" / "Should be fine" → Optimism bias, requires test evidence

---

### 3. Knowledge Loop - Gets Smarter Over Time

> Reflection + Persistence = Continuously Evolving AI Assistant

```
Work Process ──→ Reflect ──→ Store ──→ Feed Back to Next Decision
                   │           │              │
                   │           │              └─ Inertia Prompts
                   │           │                 Past decisions / Known pitfalls
                   │           │
                   │           └─ Anchor Storage
                   │              [D] Decisions / [C] Constraints
                   │              [P] Problems  / [M] Patterns
                   │
                   └─ Bias Scanning
                      Detect assumptions / blind spots
```

| Capability | Description |
|------------|-------------|
| **Cross-Session Memory** | Multi-session isolation, user-level knowledge persistence |
| **Introspection** | Review and summarize work across any time span |
| **Inertia Prompts** | Past decisions and known pitfalls auto-injected into new tasks |
| **Three-Level Compression** | Expanded→Normal→Compact, smart context window management |

```bash
# Introspection commands
/wukong introspect today      # Generate today's work report
/wukong introspect this week  # Generate weekly summary
/wukong anchors               # View all persisted decisions/problems/patterns
```

**User Value:**
- Never repeat mistakes - Problem anchors [P] auto-remind
- Decisions are traceable - Decision anchors [D] record context
- Patterns are reusable - Pattern anchors [M] persist across projects

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/anthropics/wukong.git
cd wukong

# Install to your project
./install.sh /path/to/your/project

# Or install to current directory
./install.sh
```

The installer will:
1. Copy rules, skills, and commands to `.claude/` in your project
2. Install hooks to `~/.wukong/hooks/`
3. Register PreCompact Hook in `~/.claude/settings.json` (with confirmation)

### Usage

```bash
# Activate Wukong
/wukong

# Start working
/wukong add user login feature
```

---

## Comparison

| Feature | Vanilla Claude Code | Wukong |
|---------|---------------------|--------|
| Task Execution | Single Agent | Six specialized agents in parallel |
| Output Verification | None | Dual verification pipeline |
| Context Management | Auto-compact with loss | Three-level compression + PreCompact save |
| Cross-Session Memory | None | Anchor system + Inertia prompts |
| Self-Reflection | None | Bias scanning + Introspection |
| Knowledge Persistence | None | Decisions/Problems/Patterns stored |

---

## Project Structure

```
wukong/
├── wukong-dist/              # Distribution source
│   ├── rules/                # Core rules (Compliance)
│   ├── skills/               # Agent skill definitions
│   ├── commands/             # Command handlers
│   └── hooks/                # PreCompact Hook (Reflection)
│
├── install.sh                # Installer script
├── README.md                 # English README
└── README-zh.md              # Chinese README

# User directory after installation
~/.wukong/
├── hooks/                    # Global hooks
└── context/                  # Knowledge storage
    ├── active/               # Active sessions
    ├── sessions/             # Session archives
    ├── anchors/              # Anchor storage
    └── index.json            # Session index
```

---

## Design Philosophy

Wukong's design draws from Eastern philosophy:

- **Six Roots (六根)** - Buddhist concept of six sense organs, mapped to six specialized agents
- **Three Trainings (戒定慧)** - Buddhist practice of discipline, concentration, and wisdom, mapped to the verification pipeline
- **Store Consciousness (识)** - Buddhist concept of repository consciousness, mapped to the knowledge storage system
- **Manas (末那识)** - Buddhist concept of ego-consciousness, mapped to bias detection

---

## References

- [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode)
- [claude-code-settings](https://github.com/feiskyer/claude-code-settings)

## License

MIT

---

<p align="center">
  <b>Six Roots in Parallel, Four Pillars Standing Guard</b><br>
  Making Claude Code better and smarter with every use
</p>
