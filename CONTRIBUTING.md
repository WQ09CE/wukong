# Contributing to Wukong

Thank you for your interest in contributing to Wukong! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- Bash (for Unix) or PowerShell 5.0+ (for Windows)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/WQ09CE/wukong.git
cd wukong

# Install development dependencies
pip install pytest

# Run tests to verify setup
python -m pytest tests/ -v
```

### Project Structure

```
wukong/
├── wukong-dist/          # Source files (rules, skills, commands)
│   ├── rules/            # Core rules (auto-loaded by Claude Code)
│   ├── skills/           # Avatar skill definitions
│   ├── commands/         # Custom commands
│   ├── hooks/            # PreCompact hooks
│   └── templates/        # Context templates
├── tests/                # Test suite
├── docs/                 # Documentation
├── install.sh            # Unix installer
└── install.ps1           # Windows installer
```

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md)
3. Include:
   - Clear description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version)

### Suggesting Features

1. Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md)
2. Explain the use case and expected benefit
3. Consider how it fits with the Six Roots (六根) avatar system

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Run tests: `python -m pytest tests/ -v`
5. Commit with conventional commits (see below)
6. Push and create a Pull Request

## Coding Standards

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add new avatar skill
fix: Correct path handling on Windows
docs: Update installation instructions
refactor: Simplify context management
test: Add tests for path validation
```

### Shell Scripts

- Use `shellcheck` for linting: `shellcheck install.sh`
- Include error handling with `set -e`
- Add comments for complex logic

### Markdown Files

- Use clear, descriptive headings
- Include code examples where helpful
- Support both English and Chinese where appropriate

### Python Code

- Follow PEP 8 style guidelines
- Add docstrings for functions
- Include type hints where practical

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_path_references.py -v

# Run installation test (Unix)
./tests/test_install.sh
```

### What Tests Cover

- Path reference validation (catches wrong paths like `~/.wukong/skills/`)
- Installation script verification
- Cross-platform compatibility

## Wukong-Specific Guidelines

### Working with Six Roots Avatars

When contributing skill files:

| Avatar | File | Focus |
|--------|------|-------|
| 眼 (Eye) | `explorer.md` | Exploration, search |
| 耳 (Ear) | `requirements-analyst.md` | Requirements analysis |
| 鼻 (Nose) | `code-reviewer.md` | Code review |
| 舌 (Tongue) | `tester.md` | Testing, documentation |
| 身 (Body) | `implementer.md` | Implementation |
| 意 (Mind) | `architect.md` | Architecture, design |

### Path Conventions

- Claude Code config: `~/.claude/` (skills, rules, commands)
- Runtime data: `~/.wukong/` (hooks, context, notepads)
- Never use `~/.wukong/skills/` - skills belong in `~/.claude/skills/`

## Getting Help

- Read the [README](README.md) for usage
- Check [CLAUDE.md](CLAUDE.md) for development context
- Open an issue for questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
