"""Tests for Wukong CLI."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from wukong_cli import __version__
from wukong_cli.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestVersion:
    """Tests for the version command."""

    def test_version_output(self, runner: CliRunner) -> None:
        """Test that version command shows version number."""
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert __version__ in result.output


class TestHelp:
    """Tests for help output."""

    def test_main_help(self, runner: CliRunner) -> None:
        """Test that main help is displayed."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Wukong" in result.output
        assert "install" in result.output
        assert "doctor" in result.output
        assert "version" in result.output

    def test_install_help(self, runner: CliRunner) -> None:
        """Test that install help is displayed."""
        result = runner.invoke(cli, ["install", "--help"])
        assert result.exit_code == 0
        assert "PATH" in result.output
        assert "--dry-run" in result.output

    def test_doctor_help(self, runner: CliRunner) -> None:
        """Test that doctor help is displayed."""
        result = runner.invoke(cli, ["doctor", "--help"])
        assert result.exit_code == 0
        assert "PATH" in result.output


class TestDoctor:
    """Tests for the doctor command."""

    def test_doctor_empty_directory(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test doctor on an empty directory (should report unhealthy)."""
        result = runner.invoke(cli, ["doctor", str(temp_dir)])
        assert result.exit_code == 1
        assert "Unhealthy" in result.output
        # Rich markup strips to just brackets, so check for errors count
        assert "errors" in result.output

    def test_doctor_with_partial_install(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test doctor on a partially installed directory."""
        # Create some directories
        (temp_dir / ".claude/rules").mkdir(parents=True)
        (temp_dir / ".wukong/context").mkdir(parents=True)

        result = runner.invoke(cli, ["doctor", str(temp_dir)])
        # Should still be unhealthy or have warnings due to missing/empty items
        assert "errors" in result.output or "warnings" in result.output


class TestInstall:
    """Tests for the install command."""

    def test_install_dry_run(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test install with --dry-run flag."""
        # Change to the wukong repo root (where .wukong exists)
        import os
        original_cwd = os.getcwd()
        try:
            # Find the wukong root (parent of wukong-cli)
            wukong_root = Path(__file__).parent.parent.parent
            if (wukong_root / ".wukong").exists():
                os.chdir(wukong_root)

            result = runner.invoke(cli, ["install", str(temp_dir), "--dry-run"])
            assert result.exit_code == 0
            assert "would create" in result.output or "would copy" in result.output
            # Verify no actual files were created in dry-run
            assert not (temp_dir / ".claude/rules").exists()
        finally:
            os.chdir(original_cwd)

    def test_install_verbose(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test install with --verbose flag."""
        import os
        original_cwd = os.getcwd()
        try:
            wukong_root = Path(__file__).parent.parent.parent
            if (wukong_root / ".wukong").exists():
                os.chdir(wukong_root)

            result = runner.invoke(cli, ["-v", "install", str(temp_dir)])
            # Should show more detailed output
            assert "Source:" in result.output or "Created" in result.output
        finally:
            os.chdir(original_cwd)

    def test_install_creates_directory_structure(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test that install creates the correct directory structure."""
        import os
        original_cwd = os.getcwd()
        try:
            wukong_root = Path(__file__).parent.parent.parent
            if (wukong_root / ".wukong").exists():
                os.chdir(wukong_root)

            result = runner.invoke(cli, ["install", str(temp_dir)])
            assert result.exit_code == 0

            # Verify all expected directories exist
            expected_dirs = [
                ".claude/rules",
                ".claude/rules-extended",
                ".claude/skills",
                ".claude/commands",
                ".wukong/context/current",
                ".wukong/context/sessions",
                ".wukong/notepads",
                ".wukong/plans",
            ]
            for dir_path in expected_dirs:
                assert (temp_dir / dir_path).exists(), f"Expected {dir_path} to exist"
                assert (temp_dir / dir_path).is_dir(), f"Expected {dir_path} to be a directory"

            # Verify anchors.md is created
            assert (temp_dir / ".wukong/context/anchors.md").exists()
        finally:
            os.chdir(original_cwd)

    def test_install_no_source_found(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test install fails gracefully when source directory not found."""
        import os
        original_cwd = os.getcwd()
        try:
            # Change to temp_dir where there's no .wukong/
            os.chdir(temp_dir)
            result = runner.invoke(cli, ["install", str(temp_dir)])
            assert result.exit_code == 1
            assert "Cannot find Wukong source files" in result.output
        finally:
            os.chdir(original_cwd)


class TestDoctorHealthy:
    """Tests for doctor command with healthy installation."""

    def test_doctor_healthy_installation(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test doctor on a healthy installation reports success."""
        import os
        original_cwd = os.getcwd()
        try:
            wukong_root = Path(__file__).parent.parent.parent
            if (wukong_root / ".wukong").exists():
                os.chdir(wukong_root)

            # First install to temp_dir
            install_result = runner.invoke(cli, ["install", str(temp_dir)])
            assert install_result.exit_code == 0

            # Now doctor should report healthy
            result = runner.invoke(cli, ["doctor", str(temp_dir)])
            assert result.exit_code == 0
            assert "Healthy" in result.output
        finally:
            os.chdir(original_cwd)

    def test_doctor_verbose(self, runner: CliRunner, temp_dir: Path) -> None:
        """Test doctor with verbose flag shows more detail."""
        import os
        original_cwd = os.getcwd()
        try:
            wukong_root = Path(__file__).parent.parent.parent
            if (wukong_root / ".wukong").exists():
                os.chdir(wukong_root)

            # First install to temp_dir
            runner.invoke(cli, ["install", str(temp_dir)])

            # Run doctor with verbose
            result = runner.invoke(cli, ["-v", "doctor", str(temp_dir)])
            # Should show check results
            assert "[ok]" in result.output or "Healthy" in result.output
        finally:
            os.chdir(original_cwd)

    def test_doctor_nonexistent_path(self, runner: CliRunner) -> None:
        """Test doctor fails on nonexistent path."""
        result = runner.invoke(cli, ["doctor", "/nonexistent/path/abc123"])
        assert result.exit_code != 0


class TestCore:
    """Tests for core module functions."""

    def test_find_source_dir_from_cwd(self) -> None:
        """Test find_source_dir finds .wukong in cwd."""
        import os
        from wukong_cli.core import find_source_dir

        original_cwd = os.getcwd()
        try:
            wukong_root = Path(__file__).parent.parent.parent
            if (wukong_root / ".wukong").exists():
                os.chdir(wukong_root)
                source = find_source_dir()
                assert source.exists()
                assert source.name == ".wukong"
        finally:
            os.chdir(original_cwd)

    def test_find_source_dir_not_found(self, temp_dir: Path) -> None:
        """Test find_source_dir raises error when source not found."""
        import os
        from wukong_cli.core import find_source_dir

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            with pytest.raises(FileNotFoundError) as exc_info:
                find_source_dir()
            assert "Cannot find Wukong source files" in str(exc_info.value)
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
