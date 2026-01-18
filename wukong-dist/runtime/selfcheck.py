#!/usr/bin/env python3
"""
Wukong Self-Check - Environment validation for Wukong 2.0

Usage:
    python3 ~/.wukong/runtime/selfcheck.py

This script validates the Wukong installation and configuration,
checking for required files, modules, and CLI functionality.
"""

import importlib.util
import os
import sys
from pathlib import Path
from typing import Tuple, List, Optional


# Status icons
ICON_OK = "\u2713"      # checkmark
ICON_FAIL = "\u2717"    # X mark
ICON_WARN = "\u26a0"    # warning


def get_home() -> Path:
    """Get user home directory (cross-platform)."""
    return Path.home()


def get_wukong_dir() -> Path:
    """Get Wukong runtime directory."""
    return get_home() / ".wukong"


def get_claude_dir() -> Path:
    """Get Claude configuration directory."""
    return get_home() / ".claude"


def count_files(directory: Path, pattern: str = "*.md") -> int:
    """Count files matching pattern in directory."""
    if not directory.exists():
        return 0
    return len(list(directory.glob(pattern)))


def check_files_exist(directory: Path, filenames: List[str]) -> Tuple[int, int]:
    """
    Check which files exist in a directory.

    Returns:
        Tuple of (found_count, missing_count)
    """
    found = 0
    missing = 0
    for filename in filenames:
        if (directory / filename).exists():
            found += 1
        else:
            missing += 1
    return found, missing


def print_header() -> None:
    """Print the self-check header."""
    print("=" * 55)
    print(" Wukong 2.0 Self-Check (\u609f\u7a7a\u81ea\u68c0)")
    print("=" * 55)
    print()


def print_footer() -> None:
    """Print the self-check footer."""
    print()
    print("=" * 55)
    print(" Self-Check Complete")
    print("=" * 55)


def check_skills() -> bool:
    """Check skill files (project-level or global)."""
    print("1. Skills")
    cwd = Path.cwd()

    # Check project-level first
    project_skills = count_files(cwd / ".claude" / "skills")
    if project_skills > 0:
        print(f"   {ICON_OK} Found {project_skills} skill files (project: .claude/skills/)")
        return True

    # Check global
    global_skills = count_files(get_claude_dir() / "skills")
    if global_skills > 0:
        print(f"   {ICON_OK} Found {global_skills} skill files (global: ~/.claude/skills/)")
        return True

    print(f"   {ICON_FAIL} No skill files found")
    return False


def check_rules() -> bool:
    """Check rule files (project-level or global)."""
    print()
    print("2. Rules")
    cwd = Path.cwd()

    # Check project-level first
    project_rules = count_files(cwd / ".claude" / "rules")
    if project_rules > 0:
        print(f"   {ICON_OK} Found {project_rules} rule files (project: .claude/rules/)")
        return True

    # Check global
    global_rules = count_files(get_claude_dir() / "rules")
    if global_rules > 0:
        print(f"   {ICON_OK} Found {global_rules} rule files (global: ~/.claude/rules/)")
        return True

    print(f"   {ICON_FAIL} No rule files found (run install.sh in project)")
    return False


def check_hooks() -> bool:
    """Check hook files."""
    print()
    print("3. Hooks (~/.wukong/hooks/)")

    hooks_dir = get_wukong_dir() / "hooks"
    hook_files = ["hui-extract.py", "on_subagent_stop.py", "on_stop.py"]

    found, missing = check_files_exist(hooks_dir, hook_files)
    total = found + missing

    if missing == 0:
        print(f"   {ICON_OK} All {found} hooks present")
        return True
    else:
        print(f"   {ICON_WARN} {found}/{total} hooks present")
        return False


def check_runtime_modules() -> bool:
    """Check Runtime 2.0 modules."""
    print()
    print("4. Runtime 2.0 (~/.wukong/runtime/)")

    runtime_dir = get_wukong_dir() / "runtime"
    runtime_files = [
        "cli.py",
        "event_bus.py",
        "state_manager.py",
        "scheduler.py",
        "artifact_manager.py",
        "anchor_manager.py",
        "metrics.py",
        "visualizer.py",
        "health_monitor.py",
    ]

    found, missing = check_files_exist(runtime_dir, runtime_files)
    total = found + missing

    if missing == 0:
        print(f"   {ICON_OK} All {found} runtime modules present")
        return True
    else:
        print(f"   {ICON_WARN} {found}/{total} modules present")
        return False


def check_dag_templates() -> bool:
    """Check DAG templates."""
    print()
    print("5. DAG Templates (~/.wukong/runtime/templates/)")

    templates_dir = get_wukong_dir() / "runtime" / "templates"
    template_files = [
        "fix_track.json",
        "feature_track.json",
        "refactor_track.json",
        "direct_track.json",
    ]

    found, _ = check_files_exist(templates_dir, template_files)

    if found == 4:
        print(f"   {ICON_OK} All 4 track templates present")
        return True
    else:
        print(f"   {ICON_WARN} {found}/4 templates present")
        return False


def check_context_module() -> bool:
    """Check context module."""
    print()
    print("6. Context (~/.wukong/context/)")

    context_dir = get_wukong_dir() / "context"
    snapshot_file = context_dir / "snapshot.py"

    if snapshot_file.exists():
        print(f"   {ICON_OK} Context module present")
        return True
    else:
        print(f"   {ICON_WARN} Context module missing")
        return False


def check_runtime_imports() -> bool:
    """Test Runtime 2.0 module imports."""
    print()
    print("7. Testing Runtime 2.0 CLI...")

    runtime_dir = get_wukong_dir() / "runtime"

    # Add runtime dir to path temporarily
    str_runtime_dir = str(runtime_dir)
    if str_runtime_dir not in sys.path:
        sys.path.insert(0, str_runtime_dir)

    modules_to_test = [
        "event_bus",
        "state_manager",
        "scheduler",
        "artifact_manager",
        "anchor_manager",
        "metrics",
    ]

    try:
        for module_name in modules_to_test:
            module_path = runtime_dir / f"{module_name}.py"
            if module_path.exists():
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

        print(f"   {ICON_OK} All runtime modules importable")
        return True

    except ImportError as e:
        print(f"   {ICON_FAIL} Import error: {e}")
        return False
    except Exception as e:
        print(f"   {ICON_FAIL} Error: {e}")
        return False


def check_cli_commands() -> bool:
    """Test Runtime CLI commands."""
    print()
    print("8. Testing CLI commands...")

    cli_path = get_wukong_dir() / "runtime" / "cli.py"

    if not cli_path.exists():
        print(f"   {ICON_WARN} CLI not found")
        return False

    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, str(cli_path), "analyze", "Fix login bug"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print(f"   {ICON_OK} CLI analyze command works")
            return True
        else:
            print(f"   {ICON_WARN} CLI analyze command failed")
            return False

    except subprocess.TimeoutExpired:
        print(f"   {ICON_WARN} CLI command timed out")
        return False
    except Exception as e:
        print(f"   {ICON_FAIL} CLI error: {e}")
        return False


def main() -> int:
    """
    Run all self-checks.

    Returns:
        0 if all checks pass, 1 if any critical check fails
    """
    print_header()

    results = []

    # Run all checks
    results.append(("Skills", check_skills()))
    results.append(("Rules", check_rules()))
    results.append(("Hooks", check_hooks()))
    results.append(("Runtime", check_runtime_modules()))
    results.append(("Templates", check_dag_templates()))
    results.append(("Context", check_context_module()))
    results.append(("Imports", check_runtime_imports()))
    results.append(("CLI", check_cli_commands()))

    print_footer()

    # Critical checks: Skills and Rules
    critical_checks = ["Skills", "Rules"]
    critical_failed = any(
        not passed for name, passed in results if name in critical_checks
    )

    return 1 if critical_failed else 0


if __name__ == "__main__":
    sys.exit(main())
