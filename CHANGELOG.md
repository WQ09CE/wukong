# Changelog

All notable changes to Wukong will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2026-01-17

### Fixed
- **neiguan.md**: Fixed anchor path mismatch - changed from single `anchors.md` to `anchors/projects/{project}.md` structure
- **neiguan.md**: Added Step 2.5 to read `hui-output.json` for each session (decisions, constraints, problems, interfaces)
- **neiguan.md**: Updated completion checklist with new verification steps
- **shi.md**: Added "Read Interface" section documenting how to query Shi system data

### Changed
- Introspection now correctly reads all Shi system data sources:
  - Session index (`index.json`)
  - Session compact forms (`compact.md`)
  - Session Hui outputs (`hui-output.json`) - NEW
  - Project anchors (`anchors/projects/{project}.md`) - FIXED
  - Global anchors (`anchors/global.md`) - NEW

## [2.0.0] - 2026-01-17

### 🚀 Major Features

#### Runtime 2.0 Architecture
- **New**: Full-featured runtime engine (`~/.wukong/runtime/`)
  - `scheduler.py` - DAG-based task scheduling with template support
  - `state.py` - Persistent state management with atomic writes
  - `events.py` - Event bus for inter-agent communication
  - `metrics.py` - Cost tracking and performance metrics
  - `anchors.py` - Knowledge anchor management system
  - `cli.py` - Unified command-line interface

#### Six Roots Agent Definitions
- **New**: Dedicated agent files in `~/.claude/agents/`
  - `eye.md` - 眼分身 (Explorer) - Codebase exploration
  - `ear.md` - 耳分身 (Analyst) - Requirements analysis
  - `nose.md` - 鼻分身 (Reviewer) - Code review & security
  - `tongue.md` - 舌分身 (Tester) - Testing & documentation
  - `body.md` - 斗战胜佛 (Implementer) - Code implementation
  - `mind.md` - 意分身 (Architect) - Design & architecture

#### Hook System
- **New**: `on_stop.py` - Graph completion hook with anchor extraction
- **New**: `on_subagent_stop.py` - Subagent validation with evidence levels (L0-L3)

#### Introspection Command
- **New**: `/neiguan` (内观) - BLOCKING checklist for self-reflection

### Changed
- **BREAKING**: Removed legacy scheduler (`~/.wukong/scheduler/`), replaced by Runtime 2.0
- Unified `--clear-state` behavior across install.sh and install.ps1
  - Only clears runtime state files (state.json, taskgraph.json, events.jsonl)
  - User data (notepads, plans, sessions) is ALWAYS preserved
- Updated CI tests to verify Runtime 2.0 modules
- Self-check (`/wukong 自检`) now tests Runtime 2.0 modules only

### Removed
- Legacy scheduler module (`wukong-dist/scheduler/`)
- Scheduler installation from install.sh (cleanup still runs for upgrades)

## [1.7.3] - 2026-01-15

### Changed
- Scheduler now installs to **user-level** `~/.wukong/scheduler/` (global)
- `/schedule` command discovery: user-level (`~/.wukong/`) takes priority over project-level (`.wukong/`)
- Added `wukong-dist/commands/` directory for command source files

### Fixed
- Fixed install.sh to handle identical file copy errors gracefully

## [1.7.2] - 2026-01-15

### Added
- Lightweight scheduler module (`wukong-dist/scheduler/`)
  - Cost-aware avatar routing (CHEAP/MEDIUM/EXPENSIVE)
  - Track DAG for Feature/Fix/Refactor workflows
  - Territory conflict detection
  - TodoWrite integration
- Context optimization modules (`wukong-dist/context/`)
  - `snapshot.py`: Parallel context snapshots for avatar consistency
  - `importance.py`: HIGH/MEDIUM/LOW marking with smart compression
  - `aggregator.py`: Auto-aggregate background task results
- `/schedule` command for task analysis and planning

### Changed
- Upgraded 斗战胜佛 (Implementer) model from sonnet to **opus**
- Both 身 (Body) and 意 (Mind) now use opus model
- `install.sh` now installs scheduler and context modules
- Move scheduler from `.wukong/` to `wukong-dist/` (proper source location)

### Fixed
- `.wukong/` directory now properly ignored in git (runtime directory)

## [1.7.1] - 2026-01-15

### Added
- Community governance files (CODE_OF_CONDUCT, CONTRIBUTING, SECURITY)
- GitHub issue and PR templates

### Fixed
- CI install script path handling

## [1.7] - 2026-01-15

### Added
- CLAUDE.md for development context

## [1.6] - 2026-01-15

### Added
- CI/CD with GitHub Actions
  - Cross-platform testing (Ubuntu, macOS, Windows)
  - Automated release on tag push
  - Shell script linting with shellcheck
  - Installation verification tests
- P0 tests for path references and installation validation

### Fixed
- Test exceptions for CLAUDE.md documentation examples

### Changed
- Improved test coverage for path validation

## [1.5] - 2025-01-14

### Added
- Cross-platform path handling for Windows compatibility
- Information disclosure security checks in jie.md (戒)

### Fixed
- Correct skills path from `~/.wukong/skills/` to `~/.claude/skills/`

### Changed
- Directory structure reorganization for clarity

## [1.0] - 2025-01-12

### Added
- Initial release of Wukong multi-agent framework
- Six Roots (六根) avatar system
  - 眼 (Eye) - Explorer
  - 耳 (Ear) - Requirements Analyst
  - 鼻 (Nose) - Code Reviewer
  - 舌 (Tongue) - Tester
  - 身 (Body) - Implementer (斗战胜佛)
  - 意 (Mind) - Architect
- Four Pillars (戒定慧识) verification system
  - 戒 (Jie) - Rules and boundary checking
  - 定 (Ding) - Reproducible verification
  - 慧 (Hui) - Reflection and knowledge extraction
  - 识 (Shi) - Information storage and feedback
- Track-based workflow selection (Feature/Fix/Refactor)
- Context management with three states (巨/常/缩)
- Cross-platform installation (Bash + PowerShell)
- PreCompact hook for knowledge preservation

---

## Migration Guide

### Upgrading from 1.5 to 1.6

No breaking changes. Simply re-run the installer:

```bash
./install.sh
```

### Upgrading from 1.0 to 1.5

**Important**: Skills path changed from `~/.wukong/skills/` to `~/.claude/skills/`

1. Re-run the installer
2. If you have custom skills, move them:
   ```bash
   mv ~/.wukong/skills/* ~/.claude/skills/
   ```

---

## Version History

| Version | Date | Highlights |
|---------|------|------------|
| 2.0.0 | 2026-01-17 | Runtime 2.0, Agent definitions, Hook system |
| 1.8.1 | 2026-01-16 | Bug fixes |
| 1.6 | 2025-01-15 | CI/CD, automated releases |
| 1.5 | 2025-01-14 | Windows support, security checks |
| 1.0 | 2025-01-12 | Initial release |
