# Changelog

All notable changes to Wukong will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
| 1.6 | 2025-01-15 | CI/CD, automated releases |
| 1.5 | 2025-01-14 | Windows support, security checks |
| 1.0 | 2025-01-12 | Initial release |
