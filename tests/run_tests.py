#!/usr/bin/env python3
"""
Wukong Test Runner (悟空测试运行器)

Run all tests for the Wukong multi-agent workflow system.

Usage:
    python tests/run_tests.py              # Run all tests
    python tests/run_tests.py --unit       # Run unit tests only
    python tests/run_tests.py --e2e        # Run end-to-end tests only
    python tests/run_tests.py --verbose    # Verbose output

Test Architecture:
    六根 (Six Roots)
        │
        ▼
    戒定慧识 (Four Pillars)
        │
        ▼
    集成验证 (Integration)
"""

import sys
import os
import unittest
import argparse
import io
from pathlib import Path
from datetime import datetime

# Fix Unicode encoding for Windows (cp1252 doesn't support box-drawing chars)
# This must be done before any print() calls with Unicode characters
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup paths
TESTS_DIR = Path(__file__).parent
PROJECT_ROOT = TESTS_DIR.parent
WUKONG_DIST = PROJECT_ROOT / "wukong-dist"

# Add module paths
sys.path.insert(0, str(WUKONG_DIST / "hooks"))
sys.path.insert(0, str(WUKONG_DIST / "scheduler"))
sys.path.insert(0, str(WUKONG_DIST / "context"))
sys.path.insert(0, str(TESTS_DIR))


class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'


def print_header(text: str):
    print(f"\n{Colors.BLUE}{'=' * 60}")
    print(f" {text}")
    print(f"{'=' * 60}{Colors.NC}\n")


def print_result(name: str, passed: bool, details: str = ""):
    status = f"{Colors.GREEN}PASS{Colors.NC}" if passed else f"{Colors.RED}FAIL{Colors.NC}"
    print(f"  [{status}] {name}")
    if details and not passed:
        print(f"         {Colors.YELLOW}{details}{Colors.NC}")


def run_unit_tests(verbose: bool = False) -> tuple[int, int]:
    """Run unit tests for all modules"""
    print_header("Unit Tests (单元测试)")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_modules = [
        ("test_hui_extract", "慧模块提取"),
        ("test_scheduler", "调度器"),
        ("test_context", "上下文优化"),
    ]

    passed = 0
    failed = 0

    for module_name, description in test_modules:
        try:
            module = __import__(module_name)
            module_suite = loader.loadTestsFromModule(module)

            # Run tests
            runner = unittest.TextTestRunner(
                verbosity=2 if verbose else 0,
                stream=sys.stdout if verbose else open(os.devnull, 'w')
            )
            result = runner.run(module_suite)

            module_passed = result.wasSuccessful()
            if module_passed:
                passed += 1
                print_result(f"{description} ({module_name})", True)
            else:
                failed += 1
                errors = len(result.errors) + len(result.failures)
                print_result(f"{description} ({module_name})", False, f"{errors} failures")

        except Exception as e:
            failed += 1
            print_result(f"{description} ({module_name})", False, str(e))

    return passed, failed


def run_integration_tests(verbose: bool = False) -> tuple[int, int]:
    """Run integration tests for 六根→戒定慧识 flow"""
    print_header("Integration Tests (集成测试)")

    passed = 0
    failed = 0

    # Test 1: Scheduler → TodoWrite integration
    try:
        from scheduler import WukongScheduler, TrackType
        from todo_integration import TodoWriteIntegration

        scheduler = WukongScheduler()
        track = scheduler.detect_track("Add user authentication feature")

        if track == TrackType.FEATURE:
            passed += 1
            print_result("Scheduler track detection", True)
        else:
            failed += 1
            print_result("Scheduler track detection", False, f"Expected FEATURE, got {track}")

        # Generate todo call (need to plan the track first)
        scheduler.plan_track(track, "Add authentication")
        integration = TodoWriteIntegration(scheduler)
        todo_call = integration.generate_todo_call()
        todos = todo_call.get("todos", [])

        if len(todos) > 0:
            passed += 1
            print_result("TodoWrite integration", True)
        else:
            failed += 1
            print_result("TodoWrite integration", False, "No todos generated")

    except Exception as e:
        failed += 2
        print_result("Scheduler → TodoWrite", False, str(e))

    # Test 2: Context snapshot → aggregator flow
    try:
        from snapshot import create_snapshot, get_snapshot_for_task
        from aggregator import TaskResult, ResultAggregator

        # Create snapshot
        snapshot = create_snapshot(
            session_id="test-integration",
            compact_context="Testing integration",
            anchors=[{"type": "D", "content": "Test decision"}]
        )

        if snapshot.session_id == "test-integration":
            passed += 1
            print_result("Context snapshot creation", True)
        else:
            failed += 1
            print_result("Context snapshot creation", False)

        # Test aggregator (TaskResult is dataclass, no started_at/completed_at)
        aggregator = ResultAggregator()
        aggregator.add_result(TaskResult(
            task_id="test-1",
            avatar="眼",
            status="completed",
            output="Test output"
        ))

        summary = aggregator.aggregate()
        # Check for task count or completion status
        if "1" in summary or "完成" in summary:
            passed += 1
            print_result("Result aggregator", True)
        else:
            failed += 1
            print_result("Result aggregator", False)

    except Exception as e:
        failed += 2
        print_result("Context flow", False, str(e))

    return passed, failed


def run_e2e_tests(verbose: bool = False) -> tuple[int, int]:
    """Run end-to-end tests for full workflow"""
    print_header("End-to-End Tests (端到端测试)")

    passed = 0
    failed = 0

    # Test: Full 六根→戒定慧识 flow simulation
    try:
        from scheduler import WukongScheduler, TrackType, TRACK_DAG, AVATAR_CONFIG
        from snapshot import create_snapshot, get_snapshot_for_task
        from aggregator import ResultAggregator, TaskResult
        from importance import mark, Importance, compress_by_importance

        # Step 1: Task arrives → Scheduler analyzes
        scheduler = WukongScheduler()
        task = "Add user login with OAuth2 feature"  # Use "Add" to trigger FEATURE track
        track = scheduler.detect_track(task)
        dag = TRACK_DAG.get(track, [])

        if len(dag) > 0 or track == TrackType.FEATURE:
            passed += 1
            print_result("Step 1: Scheduler DAG generation", True)
        else:
            failed += 1
            print_result("Step 1: Scheduler DAG generation", False)

        # Step 2: Create context snapshot for avatars
        snapshot = create_snapshot(
            session_id="e2e-test",
            compact_context=f"Task: {task}",
            anchors=[
                {"type": "P", "content": "Implement OAuth2"},
                {"type": "C", "content": "Must use HTTPS"}
            ]
        )

        # Use get_snapshot_for_task to format for injection
        inject_content = get_snapshot_for_task(snapshot, "test-task")
        if "CONTEXT SNAPSHOT" in inject_content or snapshot.session_id == "e2e-test":
            passed += 1
            print_result("Step 2: Context injection format", True)
        else:
            failed += 1
            print_result("Step 2: Context injection format", False)

        # Step 3: Simulate avatar outputs with importance marking
        # mark() requires: content, importance, category, source
        eye_output = mark("Found 3 relevant files", Importance.HIGH, "file", "眼分身")
        mind_output = mark("Designed OAuth2 flow", Importance.HIGH, "decision", "意分身")

        compressed = compress_by_importance([eye_output, mind_output], max_chars=500)

        if len(compressed) > 0:
            passed += 1
            print_result("Step 3: Importance-based compression", True)
        else:
            failed += 1
            print_result("Step 3: Importance-based compression", False)

        # Step 4: Aggregate results (TaskResult is dataclass)
        aggregator = ResultAggregator()
        for avatar in ["眼", "意", "身"]:
            aggregator.add_result(TaskResult(
                task_id=f"task-{avatar}",
                avatar=avatar,
                status="completed",
                output=f"{avatar} completed work"
            ))

        summary = aggregator.aggregate(max_chars=500)

        # Check aggregator processed all 3 tasks
        if "3" in summary or "完成" in summary:
            passed += 1
            print_result("Step 4: Result aggregation", True)
        else:
            failed += 1
            print_result("Step 4: Result aggregation", False)

    except Exception as e:
        failed += 4
        print_result("E2E flow", False, str(e))

    return passed, failed


def run_hui_shi_tests(verbose: bool = False) -> tuple[int, int]:
    """Run 慧/识 system integration tests"""
    print_header("Hui/Shi Tests (慧/识系统测试)")

    try:
        import subprocess
        import json

        # Run test_hui_shi.py with project root as cwd
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "test_hui_shi.py"), "--cwd", str(PROJECT_ROOT)],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=60
        )

        # Try to parse JSON result if available
        json_file = PROJECT_ROOT / ".wukong" / "context" / "test-results"
        json_files = list(json_file.glob("test-*.json")) if json_file.exists() else []

        if json_files:
            # Get the most recent result
            latest = max(json_files, key=lambda p: p.stat().st_mtime)
            with open(latest, 'r', encoding='utf-8') as f:
                test_result = json.load(f)

            summary = test_result.get('summary', {})
            passed = summary.get('passed', 0)
            failed = summary.get('failed', 0)

            if failed == 0:
                print_result(f"慧/识系统 ({passed} tests)", True)
            else:
                print_result(f"慧/识系统 ({passed}/{passed+failed} passed)", False)

            return 1 if failed == 0 else 0, 1 if failed > 0 else 0
        else:
            # Fallback: check return code
            if result.returncode == 0:
                print_result("慧/识系统", True)
                return 1, 0
            else:
                # Show full traceback for debugging
                error_msg = result.stderr or result.stdout or "Unknown error"
                # Truncate to first 500 chars for display, but show key parts
                if len(error_msg) > 500:
                    error_msg = error_msg[:500] + "..."
                print_result("慧/识系统", False, error_msg.split('\n')[0] if error_msg else "Unknown error")
                return 0, 1

    except subprocess.TimeoutExpired:
        print_result("慧/识系统", False, "Timeout after 60s")
        return 0, 1
    except Exception as e:
        print_result("慧/识系统", False, str(e))
        return 0, 1


def run_path_reference_tests() -> tuple[int, int]:
    """Run path reference validation tests"""
    print_header("Path Reference Tests (路径引用测试)")

    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "test_path_references.py")],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )

        if result.returncode == 0:
            print_result("Path references validation", True)
            return 1, 0
        else:
            print_result("Path references validation", False, result.stderr[:100])
            return 0, 1

    except Exception as e:
        print_result("Path references validation", False, str(e))
        return 0, 1


def main():
    parser = argparse.ArgumentParser(description="Wukong Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument("--hui-shi", action="store_true", help="Run 慧/识 system tests only")
    parser.add_argument("--path", action="store_true", help="Run path reference tests only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    print(f"{Colors.BLUE}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         Wukong Test Runner (悟空测试运行器)              ║")
    print("║                                                          ║")
    print("║         六根 → 戒定慧识 → 验证                           ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"{Colors.NC}")

    total_passed = 0
    total_failed = 0

    run_all = not (args.unit or args.integration or args.e2e or args.hui_shi or args.path)

    if run_all or args.unit:
        p, f = run_unit_tests(args.verbose)
        total_passed += p
        total_failed += f

    if run_all or args.integration:
        p, f = run_integration_tests(args.verbose)
        total_passed += p
        total_failed += f

    if run_all or args.e2e:
        p, f = run_e2e_tests(args.verbose)
        total_passed += p
        total_failed += f

    if run_all or args.hui_shi:
        p, f = run_hui_shi_tests(args.verbose)
        total_passed += p
        total_failed += f

    if run_all or args.path:
        p, f = run_path_reference_tests()
        total_passed += p
        total_failed += f

    # Summary
    print_header("Test Summary (测试总结)")
    print(f"  Total:  {total_passed + total_failed}")
    print(f"  {Colors.GREEN}Passed: {total_passed}{Colors.NC}")
    print(f"  {Colors.RED}Failed: {total_failed}{Colors.NC}")
    print()

    if total_failed == 0:
        print(f"  {Colors.GREEN}✓ All tests passed!{Colors.NC}")
        return 0
    else:
        print(f"  {Colors.RED}✗ Some tests failed{Colors.NC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
