"""Wukong CLI - Command definitions using Click."""

from typing import Optional

import click
from rich.console import Console

from . import __version__
from .core import do_doctor, do_install

console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Wukong - AI Agent Protocol Installer.

    Install and manage Wukong protocol files for Claude Code projects.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
def version() -> None:
    """Show version information."""
    console.print(f"wukong-cli [bold]{__version__}[/bold]")


@cli.command()
@click.argument("path", default=".", type=click.Path())
@click.option("--dry-run", is_flag=True, help="Preview actions without executing")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing installation without confirmation")
@click.pass_context
def install(ctx: click.Context, path: str, dry_run: bool, force: bool) -> None:
    """Install Wukong protocol to a project.

    PATH is the target project directory (default: current directory).
    """
    verbose = ctx.obj.get("verbose", False)
    exit_code = do_install(path, dry_run=dry_run, verbose=verbose, force=force)
    ctx.exit(exit_code)


@cli.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.pass_context
def doctor(ctx: click.Context, path: str) -> None:
    """Check Wukong installation health.

    PATH is the project directory to check (default: current directory).
    """
    verbose = ctx.obj.get("verbose", False)
    exit_code = do_doctor(path, verbose=verbose)
    ctx.exit(exit_code)


if __name__ == "__main__":
    cli()
