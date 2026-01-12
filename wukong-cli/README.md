# Wukong CLI

Wukong AI Agent Protocol Installer for Claude Code projects.

## Installation

```bash
pip install wukong-cli
```

Or install from source:

```bash
cd wukong-cli
pip install -e .
```

## Usage

### Install Wukong to a project

```bash
# Install to current directory
wukong install

# Install to a specific path
wukong install /path/to/project

# Preview without making changes
wukong install --dry-run

# Show detailed output
wukong -v install

# Force overwrite existing installation (skip confirmation)
wukong install --force
# or
wukong install -f
```

### Check installation health

```bash
wukong doctor
wukong doctor /path/to/project
```

### Show version

```bash
wukong version
```

## Commands

| Command | Description |
|---------|-------------|
| `wukong install [PATH]` | Install Wukong protocol files to a project |
| `wukong doctor [PATH]` | Check installation health and report issues |
| `wukong version` | Show CLI version |

## Options

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Show detailed output |
| `--dry-run` | Preview actions without executing (install only) |
| `-f, --force` | Overwrite existing installation without confirmation (install only) |
| `--help` | Show help message |
