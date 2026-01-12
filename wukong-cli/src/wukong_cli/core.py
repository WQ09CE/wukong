"""Wukong CLI - Core business logic for install and doctor commands."""

import os
import shutil
from pathlib import Path
from typing import List, Tuple

from rich.console import Console

console = Console()


class InstallStats:
    """Track installation statistics."""

    def __init__(self):
        self.dirs_created = 0
        self.files_copied = 0

    def add_dirs(self, count: int) -> None:
        self.dirs_created += count

    def add_files(self, count: int) -> None:
        self.files_copied += count

    def summary(self) -> str:
        return f"Created {self.dirs_created} directories, copied {self.files_copied} files"


def find_source_dir() -> Path:
    """Find the Wukong source directory.

    Search order:
    1. WUKONG_HOME environment variable
    2. Current working directory's .wukong/ (development mode)
    3. Package's built-in assets/ (packaged mode)

    Returns:
        Path to the source directory.

    Raises:
        FileNotFoundError: If no source directory is found.
    """
    # 1. WUKONG_HOME environment variable
    wukong_home = os.environ.get("WUKONG_HOME")
    if wukong_home:
        wukong_home_path = Path(wukong_home) / ".wukong"
        if wukong_home_path.exists():
            return wukong_home_path

    # 2. Current directory (development mode)
    cwd_source = Path.cwd() / ".wukong"
    if cwd_source.exists():
        return cwd_source

    # 3. Package built-in assets (packaged mode)
    pkg_assets = Path(__file__).parent / "assets"
    if pkg_assets.exists():
        return pkg_assets

    raise FileNotFoundError(
        "Cannot find Wukong source files.\n\n"
        "Please try one of:\n"
        "  1. Run from wukong repo root (where .wukong/ exists)\n"
        "  2. Set WUKONG_HOME environment variable\n"
        "  3. pip install wukong-cli[assets] (coming soon)"
    )


def check_existing_installation(target_path: Path) -> bool:
    """Check if target has existing .claude/ directory.

    Args:
        target_path: Target project path.

    Returns:
        True if .claude/ exists, False otherwise.
    """
    return (target_path / ".claude").exists()


def do_install(
    target: str,
    dry_run: bool = False,
    verbose: bool = False,
    force: bool = False,
) -> int:
    """Execute the install command.

    Args:
        target: Target project path.
        dry_run: If True, preview actions without executing.
        verbose: If True, show detailed output.
        force: If True, skip confirmation for overwriting existing installation.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    target_path = Path(target).resolve()

    # If target_path ends with .claude, treat it as the project root's parent
    # e.g., ~/.claude -> ~ (so files go to ~/.claude/rules, not ~/.claude/.claude/rules)
    if target_path.name == ".claude":
        target_path = target_path.parent

    stats = InstallStats()

    console.print("[bold blue]Wukong Installer[/bold blue]")
    console.print(f"Installing to [cyan]{target_path}[/cyan]...")
    if dry_run:
        console.print("[dim](dry-run mode - no changes will be made)[/dim]")
    console.print()

    # Find source directory
    try:
        source = find_source_dir()
        if verbose:
            console.print(f"  [dim]Source: {source}[/dim]")
    except FileNotFoundError as e:
        console.print(f"[red][error][/red] {e}")
        return 1

    # Check for existing installation (skip in dry-run mode)
    if not dry_run and check_existing_installation(target_path) and not force:
        console.print("[yellow]Existing .claude/ found.[/yellow]")
        try:
            response = console.input("Overwrite? [y/N] ")
            if response.lower() not in ("y", "yes"):
                console.print("[dim]Aborted.[/dim]")
                return 1
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Aborted.[/dim]")
            return 1

    # Directory structure to create
    dirs_to_create = [
        ".claude/rules",
        ".claude/skills",
        ".claude/commands",
        ".wukong/context/current",
        ".wukong/context/sessions",
        ".wukong/notepads",
        ".wukong/plans",
    ]

    # Create directories
    dirs_created_count = 0
    for dir_path in dirs_to_create:
        full_path = target_path / dir_path
        if dry_run:
            console.print(f"  [dim]would create[/dim] {dir_path}/")
        else:
            if not full_path.exists():
                dirs_created_count += 1
            full_path.mkdir(parents=True, exist_ok=True)
            if verbose:
                console.print(f"  [green][ok][/green] Created {dir_path}/")
    stats.add_dirs(dirs_created_count)

    # Copy core rule to .claude/rules/ (auto-loaded at startup)
    core_rule = source / "rules" / "00-wukong-core.md"
    if core_rule.exists():
        rules_dst = target_path / ".claude/rules"
        if dry_run:
            console.print(f"  [dim]would copy[/dim] Core rule")
        else:
            shutil.copy2(core_rule, rules_dst / "00-wukong-core.md")
            if verbose:
                console.print(f"  [green][ok][/green] Core rule")
            stats.add_files(1)

    # Copy skills
    skills_src = source / "skills"
    if skills_src.exists():
        skills_dst = target_path / ".claude/skills"
        count = _copy_files(skills_src, skills_dst, "*.md", "Skills", dry_run, verbose)
        stats.add_files(count)

    # Copy commands
    commands_src = source / "commands"
    if commands_src.exists():
        commands_dst = target_path / ".claude/commands"
        count = _copy_files(commands_src, commands_dst, "*.md", "Commands", dry_run, verbose)
        stats.add_files(count)

    # Copy templates (if exist)
    templates_src = source / "templates"
    if templates_src.exists():
        templates_dst = target_path / ".wukong/templates"
        if dry_run:
            console.print(f"  [dim]would copy[/dim] Templates")
        else:
            templates_dst.mkdir(parents=True, exist_ok=True)
            shutil.copytree(templates_src, templates_dst, dirs_exist_ok=True)
            template_count = len(list(templates_src.rglob("*")))
            stats.add_files(template_count)
            if verbose:
                console.print(f"  [green][ok][/green] Templates ({template_count} files)")

    # Copy context templates (if exist)
    ctx_templates_src = source / "context/templates"
    if ctx_templates_src.exists():
        ctx_templates_dst = target_path / ".wukong/context/templates"
        if dry_run:
            console.print(f"  [dim]would copy[/dim] Context templates")
        else:
            ctx_templates_dst.mkdir(parents=True, exist_ok=True)
            shutil.copytree(ctx_templates_src, ctx_templates_dst, dirs_exist_ok=True)
            ctx_template_count = len(list(ctx_templates_src.rglob("*")))
            stats.add_files(ctx_template_count)
            if verbose:
                console.print(f"  [green][ok][/green] Context templates ({ctx_template_count} files)")

    # Initialize anchors.md
    anchors_path = target_path / ".wukong/context/anchors.md"
    if not anchors_path.exists():
        if dry_run:
            console.print(f"  [dim]would create[/dim] anchors.md")
        else:
            anchors_path.write_text(
                "# Anchors (锚点)\n\n"
                "Global anchors for this project.\n"
            )
            stats.add_files(1)
            if verbose:
                console.print(f"  [green][ok][/green] Initialized anchors.md")

    # Done
    console.print()
    if not dry_run:
        console.print(f"[green][ok][/green] {stats.summary()}")
    console.print("[bold green]Done![/bold green] Start Claude Code and say: 'Hello Wukong'")
    return 0


def _copy_files(
    src_dir: Path,
    dst_dir: Path,
    pattern: str,
    description: str,
    dry_run: bool,
    verbose: bool,
) -> int:
    """Copy files matching pattern from src to dst.

    Returns:
        Number of files copied.
    """
    files = list(src_dir.glob(pattern))
    if not files:
        if verbose:
            console.print(f"  [yellow][skip][/yellow] {description} (no files)")
        return 0

    if dry_run:
        console.print(f"  [dim]would copy[/dim] {description} ({len(files)} files)")
    else:
        for f in files:
            shutil.copy2(f, dst_dir / f.name)
        if verbose:
            console.print(f"  [green][ok][/green] {description} ({len(files)} files)")

    return len(files)


def do_doctor(target: str, verbose: bool = False) -> int:
    """Execute the doctor command.

    Args:
        target: Target project path to check.
        verbose: If True, show detailed output.

    Returns:
        Exit code (0 for healthy, 1 for unhealthy).
    """
    target_path = Path(target).resolve()

    # If target_path ends with .claude, treat it as the project root's parent
    if target_path.name == ".claude":
        target_path = target_path.parent

    console.print("[bold blue]Wukong Doctor[/bold blue]")
    console.print(f"Checking [cyan]{target_path}[/cyan]...")
    console.print()

    # Items to check: (relative_path, type, description)
    checks: List[Tuple[str, str, str]] = [
        (".claude/rules/00-wukong-core.md", "file", "Core rule"),
        (".claude/rules/", "dir", "Rules directory"),
        (".claude/skills/", "dir", "Skills"),
        (".claude/commands/", "dir", "Commands"),
        (".wukong/context/anchors.md", "file", "Anchors file"),
        (".wukong/notepads/", "dir", "Notepads"),
        (".wukong/plans/", "dir", "Plans"),
    ]

    ok_count = 0
    warn_count = 0
    error_count = 0

    for rel_path, check_type, desc in checks:
        full_path = target_path / rel_path

        if check_type == "file":
            if full_path.exists() and full_path.is_file():
                console.print(f"  [green][ok][/green] {rel_path}")
                ok_count += 1
            else:
                console.print(f"  [red][missing][/red] {rel_path}")
                error_count += 1
        else:  # dir
            if full_path.exists() and full_path.is_dir():
                # Count non-hidden files
                file_count = len([f for f in full_path.iterdir() if not f.name.startswith(".")])
                if file_count > 0:
                    console.print(f"  [green][ok][/green] {rel_path} ({file_count} files)")
                    ok_count += 1
                else:
                    console.print(f"  [yellow][warn][/yellow] {rel_path} (empty)")
                    warn_count += 1
            else:
                console.print(f"  [red][missing][/red] {rel_path}")
                error_count += 1

    # Summary
    console.print()
    if error_count > 0:
        console.print(
            f"[red]Status: Unhealthy[/red] ({error_count} errors, {warn_count} warnings)"
        )
        return 1
    elif warn_count > 0:
        console.print(f"[yellow]Status: Healthy[/yellow] ({warn_count} warnings)")
        return 0
    else:
        console.print("[green]Status: Healthy[/green]")
        return 0
