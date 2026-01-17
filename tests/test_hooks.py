"""
Wukong Hooks Module Tests

Tests for:
- on_stop.py: Task completion handler
- on_subagent_stop.py: Subagent completion handler

This test suite covers:
1. Helper functions (timestamps, keyword extraction)
2. Anchor extraction patterns (decisions, constraints, lessons, interfaces)
3. Node output aggregation
4. Evidence level evaluation
5. Output format validation
6. Track threshold checking
7. Complete flow processing
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
test_dir = Path(__file__).parent.resolve()
project_root = test_dir.parent
hooks_dir = project_root / "wukong-dist" / "hooks"

if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

# Import after path setup
from on_stop import (
    get_timestamp,
    extract_keywords,
    extract_anchor_candidates,
    aggregate_node_outputs,
    write_anchor_candidates,
    generate_completion_summary,
    process_stop_event,
    DECISION_PATTERNS,
    CONSTRAINT_PATTERNS,
    LESSON_PATTERNS,
    INTERFACE_PATTERNS,
)

from on_subagent_stop import (
    detect_l0_signals,
    detect_healthy_signals,
    evaluate_evidence_level,
    validate_output_format,
    check_track_threshold,
    process_subagent_stop,
    L0_PATTERNS,
    HEALTHY_PATTERNS,
    TRACK_THRESHOLDS,
)


# =============================================================================
# Tests for on_stop.py
# =============================================================================

class TestOnStopHelpers(unittest.TestCase):
    """Tests for on_stop.py helper functions."""

    def test_get_timestamp_format(self):
        """Test that timestamp is in ISO 8601 format with timezone."""
        timestamp = get_timestamp()
        # Should contain date separator and timezone info
        self.assertIn("T", timestamp)
        self.assertIn("+", timestamp)
        # Should start with year (4 digits)
        self.assertTrue(timestamp[:4].isdigit())

    def test_get_timestamp_utc(self):
        """Test that timestamp uses UTC timezone."""
        timestamp = get_timestamp()
        # UTC offset should be +00:00
        self.assertTrue(timestamp.endswith("+00:00"))

    def test_extract_keywords_basic(self):
        """Test basic keyword extraction from English text."""
        text = "The function calculates the maximum value from the array"
        keywords = extract_keywords(text, max_keywords=3)
        # Should extract meaningful words, not stop words
        self.assertIn("function", keywords)
        self.assertIn("calculates", keywords)
        self.assertNotIn("the", keywords)
        self.assertNotIn("from", keywords)

    def test_extract_keywords_filters_stopwords(self):
        """Test that common stop words are filtered out."""
        text = "The is a an are was were be been being have has had do does did"
        keywords = extract_keywords(text)
        # All words are stop words, should return empty or very few
        self.assertEqual(len(keywords), 0)

    def test_extract_keywords_chinese(self):
        """Test keyword extraction from Chinese text."""
        text = "我们决定使用 Python 编写这个函数来计算数组的最大值"
        keywords = extract_keywords(text, max_keywords=5)
        # Should filter Chinese stop words
        self.assertNotIn("的", keywords)
        self.assertNotIn("我们", keywords)
        # Should include meaningful words
        self.assertTrue(len(keywords) > 0)

    def test_extract_keywords_frequency(self):
        """Test that keywords are sorted by frequency."""
        text = "python python python java java rust"
        keywords = extract_keywords(text, max_keywords=3)
        # python appears most, then java, then rust
        self.assertEqual(keywords[0], "python")
        self.assertEqual(keywords[1], "java")
        self.assertEqual(keywords[2], "rust")

    def test_extract_keywords_max_limit(self):
        """Test that max_keywords limit is respected."""
        text = "apple banana cherry date elderberry fig grape honeydew"
        keywords = extract_keywords(text, max_keywords=3)
        self.assertLessEqual(len(keywords), 3)

    def test_extract_keywords_short_words_filtered(self):
        """Test that single-character words are filtered."""
        text = "a b c d e function method class"
        keywords = extract_keywords(text)
        # Single chars should be filtered
        self.assertNotIn("a", keywords)
        self.assertNotIn("b", keywords)


class TestAnchorExtraction(unittest.TestCase):
    """Tests for anchor candidate extraction."""

    def test_extract_decision_pattern_chinese(self):
        """Test Chinese decision pattern extraction."""
        text = "我们决定: 使用 React 框架来构建前端应用，因为它有良好的生态系统"
        candidates = extract_anchor_candidates(text)
        # Should find at least one decision anchor
        decision_anchors = [c for c in candidates if c["type"] == "decision"]
        self.assertGreater(len(decision_anchors), 0)
        # Check content is captured
        self.assertIn("React", decision_anchors[0]["content"])

    def test_extract_decision_pattern_english(self):
        """Test English decision pattern extraction."""
        text = "We decided to use PostgreSQL for the database because it supports JSON well."
        candidates = extract_anchor_candidates(text)
        decision_anchors = [c for c in candidates if c["type"] == "decision"]
        self.assertGreater(len(decision_anchors), 0)
        self.assertIn("PostgreSQL", decision_anchors[0]["content"])

    def test_extract_decision_with_chose(self):
        """Test 'chose' pattern extraction."""
        text = "We chose to use Redis for caching because of its performance."
        candidates = extract_anchor_candidates(text)
        decision_anchors = [c for c in candidates if c["type"] == "decision"]
        self.assertGreater(len(decision_anchors), 0)

    def test_extract_constraint_pattern_chinese(self):
        """Test Chinese constraint pattern extraction."""
        text = "必须: 所有的 API 调用必须在 5 秒内返回响应，否则会触发超时机制"
        candidates = extract_anchor_candidates(text)
        constraint_anchors = [c for c in candidates if c["type"] == "constraint"]
        self.assertGreater(len(constraint_anchors), 0)
        self.assertIn("API", constraint_anchors[0]["content"])

    def test_extract_constraint_pattern_english(self):
        """Test English constraint pattern extraction."""
        text = "The system must validate all user inputs before processing them."
        candidates = extract_anchor_candidates(text)
        constraint_anchors = [c for c in candidates if c["type"] == "constraint"]
        self.assertGreater(len(constraint_anchors), 0)

    def test_extract_constraint_cannot(self):
        """Test 'cannot' constraint pattern."""
        text = "不能: 直接修改生产数据库，所有变更必须通过迁移脚本执行"
        candidates = extract_anchor_candidates(text)
        constraint_anchors = [c for c in candidates if c["type"] == "constraint"]
        self.assertGreater(len(constraint_anchors), 0)

    def test_extract_lesson_pattern_chinese(self):
        """Test Chinese lesson pattern extraction."""
        text = "教训: 不要在没有备份的情况下执行数据库迁移，这次差点丢失重要数据"
        candidates = extract_anchor_candidates(text)
        lesson_anchors = [c for c in candidates if c["type"] == "lesson"]
        self.assertGreater(len(lesson_anchors), 0)

    def test_extract_lesson_pattern_english(self):
        """Test English lesson pattern extraction."""
        text = "We learned that caching can significantly improve response times in high-traffic scenarios."
        candidates = extract_anchor_candidates(text)
        lesson_anchors = [c for c in candidates if c["type"] == "lesson"]
        self.assertGreater(len(lesson_anchors), 0)

    def test_extract_lesson_gotcha(self):
        """Test 'gotcha' pattern extraction."""
        text = "Gotcha: The default timeout value is too short for batch operations processing large datasets."
        candidates = extract_anchor_candidates(text)
        lesson_anchors = [c for c in candidates if c["type"] == "lesson"]
        self.assertGreater(len(lesson_anchors), 0)

    def test_extract_interface_pattern_chinese(self):
        """Test Chinese interface pattern extraction."""
        text = "定义了 用户认证 接口，包含登录、注册和密码重置三个端点"
        candidates = extract_anchor_candidates(text)
        interface_anchors = [c for c in candidates if c["type"] == "interface"]
        self.assertGreater(len(interface_anchors), 0)

    def test_extract_interface_pattern_english(self):
        """Test English API pattern extraction."""
        text = "API: /users/{id}/profile returns user profile information including name, email, and avatar."
        candidates = extract_anchor_candidates(text)
        interface_anchors = [c for c in candidates if c["type"] == "interface"]
        self.assertGreater(len(interface_anchors), 0)

    def test_deduplication(self):
        """Test that duplicate anchors are deduplicated."""
        # Same content twice should only appear once
        text = """
        我们决定: 使用 TypeScript 来保证类型安全和代码质量
        我们决定: 使用 TypeScript 来保证类型安全和代码质量
        """
        candidates = extract_anchor_candidates(text)
        decision_anchors = [c for c in candidates if c["type"] == "decision"]
        # Should be deduplicated to one
        self.assertEqual(len(decision_anchors), 1)

    def test_length_limits_short(self):
        """Test that very short content is filtered out."""
        text = "我们决定: 用 A"  # Too short (< 10 chars)
        candidates = extract_anchor_candidates(text)
        self.assertEqual(len(candidates), 0)

    def test_length_limits_long(self):
        """Test that very long content is filtered out."""
        long_content = "x" * 600  # > 500 chars
        text = f"我们决定: {long_content}"
        candidates = extract_anchor_candidates(text)
        self.assertEqual(len(candidates), 0)

    def test_title_truncation(self):
        """Test that titles are truncated for long content."""
        content = "a" * 100
        text = f"我们决定: {content}"
        candidates = extract_anchor_candidates(text)
        if candidates:
            # Title should be truncated to 50 chars + "..."
            self.assertLessEqual(len(candidates[0]["title"]), 53)

    def test_source_attribution(self):
        """Test that source is properly attached to candidates."""
        text = "我们决定: 使用 Docker 容器化部署以确保环境一致性"
        source = {"graph_id": "tg_123", "node_id": "node_abc"}
        candidates = extract_anchor_candidates(text, source=source)
        if candidates:
            self.assertEqual(candidates[0]["source"], source)


class TestNodeAggregation(unittest.TestCase):
    """Tests for node output aggregation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.artifacts_dir = Path(self.temp_dir) / "artifacts"
        self.artifacts_dir.mkdir(parents=True)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_aggregate_empty_directory(self):
        """Test aggregation with non-existent graph directory."""
        result = aggregate_node_outputs("nonexistent_graph", self.artifacts_dir)
        self.assertEqual(result["graph_id"], "nonexistent_graph")
        self.assertEqual(len(result["nodes"]), 0)
        self.assertEqual(result["all_text"], "")

    def test_aggregate_with_outputs(self):
        """Test aggregation with actual node outputs."""
        # Create graph directory
        graph_dir = self.artifacts_dir / "tg_test123"
        graph_dir.mkdir(parents=True)

        # Create node output
        node_dir = graph_dir / "eye_explore"
        node_dir.mkdir()
        output_file = node_dir / "output.json"
        output_data = {
            "output": {
                "summary": "Found 5 relevant files in the codebase",
                "files": ["file1.py", "file2.py"]
            }
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f)

        # Aggregate
        result = aggregate_node_outputs("tg_test123", self.artifacts_dir)
        self.assertEqual(result["graph_id"], "tg_test123")
        self.assertIn("eye_explore", result["nodes"])
        self.assertIn("Found 5 relevant files", result["all_text"])

    def test_aggregate_multiple_nodes(self):
        """Test aggregation with multiple nodes."""
        graph_dir = self.artifacts_dir / "tg_multi"
        graph_dir.mkdir(parents=True)

        # Create multiple node outputs
        for node_name, summary in [("eye_1", "Eye found files"), ("nose_1", "Nose reviewed code")]:
            node_dir = graph_dir / node_name
            node_dir.mkdir()
            with open(node_dir / "output.json", "w", encoding="utf-8") as f:
                json.dump({"output": {"summary": summary}}, f)

        result = aggregate_node_outputs("tg_multi", self.artifacts_dir)
        self.assertEqual(len(result["nodes"]), 2)
        self.assertIn("Eye found files", result["all_text"])
        self.assertIn("Nose reviewed code", result["all_text"])

    def test_aggregate_with_summary_file(self):
        """Test aggregation includes summary.md content."""
        graph_dir = self.artifacts_dir / "tg_summary"
        node_dir = graph_dir / "body_impl"
        node_dir.mkdir(parents=True)

        # Create summary.md
        with open(node_dir / "summary.md", "w", encoding="utf-8") as f:
            f.write("# Implementation Summary\nSuccessfully implemented feature X")

        result = aggregate_node_outputs("tg_summary", self.artifacts_dir)
        self.assertIn("Implementation Summary", result["all_text"])

    def test_aggregate_handles_invalid_json(self):
        """Test that invalid JSON files are handled gracefully."""
        graph_dir = self.artifacts_dir / "tg_invalid"
        node_dir = graph_dir / "bad_node"
        node_dir.mkdir(parents=True)

        # Create invalid JSON
        with open(node_dir / "output.json", "w") as f:
            f.write("{ invalid json }")

        # Should not raise, just skip invalid file
        result = aggregate_node_outputs("tg_invalid", self.artifacts_dir)
        self.assertEqual(len(result["nodes"]), 0)


class TestWriteAnchorCandidates(unittest.TestCase):
    """Tests for writing anchor candidates."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.anchors_dir = Path(self.temp_dir) / "anchors"

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_write_creates_directory(self):
        """Test that anchors directory is created if missing."""
        candidates = [{"type": "decision", "title": "Test", "content": "Test content"}]
        write_anchor_candidates(candidates, self.anchors_dir)
        self.assertTrue(self.anchors_dir.exists())

    def test_write_generates_ids(self):
        """Test that candidate IDs are generated."""
        candidates = [{"type": "decision", "title": "Test", "content": "Test content"}]
        ids = write_anchor_candidates(candidates, self.anchors_dir)
        self.assertEqual(len(ids), 1)
        self.assertTrue(ids[0].startswith("cand_"))

    def test_write_persists_candidates(self):
        """Test that candidates are persisted to file."""
        candidates = [{"type": "decision", "title": "Test", "content": "Test content with enough length here"}]
        write_anchor_candidates(candidates, self.anchors_dir)

        # Read back
        candidates_file = self.anchors_dir / "candidates.json"
        self.assertTrue(candidates_file.exists())
        with open(candidates_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("candidates", data)
        self.assertEqual(len(data["candidates"]), 1)


class TestGenerateCompletionSummary(unittest.TestCase):
    """Tests for completion summary generation."""

    def test_summary_contains_graph_id(self):
        """Test that summary contains the graph ID."""
        summary = generate_completion_summary(
            "tg_test123",
            {"nodes": {}, "summaries": []},
            []
        )
        self.assertIn("tg_test123", summary)

    def test_summary_contains_node_count(self):
        """Test that summary shows node count."""
        aggregated = {
            "nodes": {"node1": {}, "node2": {}},
            "summaries": []
        }
        summary = generate_completion_summary("tg_test", aggregated, [])
        self.assertIn("2", summary)

    def test_summary_includes_node_summaries(self):
        """Test that node summaries are included."""
        aggregated = {
            "nodes": {"eye_1": {}},
            "summaries": [{"node_id": "eye_1", "summary": "Found important files"}]
        }
        summary = generate_completion_summary("tg_test", aggregated, [])
        self.assertIn("Found important files", summary)

    def test_summary_includes_candidates(self):
        """Test that anchor candidates are included."""
        candidates = [{
            "type": "decision",
            "title": "Use TypeScript",
            "content": "We chose TypeScript for type safety",
            "keywords": ["typescript", "type"],
            "id": "cand_123"
        }]
        summary = generate_completion_summary("tg_test", {"nodes": {}, "summaries": []}, candidates)
        self.assertIn("DECISION", summary)
        self.assertIn("TypeScript", summary)


class TestProcessStopEvent(unittest.TestCase):
    """Tests for complete stop event processing."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.artifacts_dir = Path(self.temp_dir) / "artifacts"
        self.anchors_dir = Path(self.temp_dir) / "anchors"
        self.artifacts_dir.mkdir(parents=True)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_process_complete_flow(self):
        """Test complete stop event processing flow."""
        # Create test artifacts
        graph_dir = self.artifacts_dir / "tg_flow"
        node_dir = graph_dir / "eye_explore"
        node_dir.mkdir(parents=True)

        output_data = {
            "output": {
                "summary": "我们决定: 使用 FastAPI 构建后端服务因为它性能好且易于使用"
            }
        }
        with open(node_dir / "output.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f)

        # Process
        result = process_stop_event(
            graph_id="tg_flow",
            artifacts_dir=self.artifacts_dir,
            anchors_dir=self.anchors_dir
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["aggregation"]["nodes_processed"], 1)
        self.assertIn("summary", result)

    def test_process_writes_summary_file(self):
        """Test that summary file is written to artifacts."""
        # Create minimal graph
        graph_dir = self.artifacts_dir / "tg_summary_write"
        graph_dir.mkdir(parents=True)

        result = process_stop_event(
            graph_id="tg_summary_write",
            artifacts_dir=self.artifacts_dir,
            anchors_dir=self.anchors_dir
        )

        summary_file = self.artifacts_dir / "tg_summary_write" / "completion_summary.md"
        self.assertTrue(summary_file.exists())


# =============================================================================
# Tests for on_subagent_stop.py
# =============================================================================

class TestL0Detection(unittest.TestCase):
    """Tests for L0 (speculation) signal detection."""

    def test_detect_chinese_speculation(self):
        """Test detection of Chinese speculation phrases."""
        text = "这个方法应该可以解决问题"
        signals = detect_l0_signals(text)
        self.assertGreater(len(signals), 0)
        self.assertIn("应该可以", signals)

    def test_detect_chinese_i_think(self):
        """Test '我觉得' pattern detection."""
        text = "我觉得这样实现应该没问题"
        signals = detect_l0_signals(text)
        self.assertIn("我觉得", signals)

    def test_detect_english_speculation(self):
        """Test detection of English speculation phrases."""
        text = "I think this approach should work fine"
        signals = detect_l0_signals(text)
        self.assertGreater(len(signals), 0)
        self.assertIn("i think", signals)

    def test_detect_probably(self):
        """Test 'probably' pattern detection."""
        text = "This will probably fix the issue"
        signals = detect_l0_signals(text)
        self.assertIn("probably", signals)

    def test_detect_obviously(self):
        """Test 'obviously' pattern detection."""
        text = "Obviously, this is the right approach"
        signals = detect_l0_signals(text)
        self.assertIn("obviously", signals)

    def test_no_false_positives(self):
        """Test that concrete statements don't trigger L0."""
        text = "The test passed with 5 assertions. Build succeeded."
        signals = detect_l0_signals(text)
        self.assertEqual(len(signals), 0)

    def test_no_false_positives_code(self):
        """Test that code snippets don't trigger L0."""
        text = "def calculate(x): return x * 2  # Returns the doubled value"
        signals = detect_l0_signals(text)
        self.assertEqual(len(signals), 0)


class TestHealthySignalDetection(unittest.TestCase):
    """Tests for healthy evidence signal detection."""

    def test_detect_file_reference(self):
        """Test detection of file:line references."""
        text = "根据 src/main.py:42 这里有一个bug"
        signals = detect_healthy_signals(text)
        self.assertGreater(len(signals), 0)

    def test_detect_command_output(self):
        """Test detection of command execution patterns."""
        text = "执行 pytest 输出显示所有测试通过"
        signals = detect_healthy_signals(text)
        self.assertGreater(len(signals), 0)

    def test_detect_test_result(self):
        """Test detection of test result patterns."""
        text = "测试 test_user_auth 通过"
        signals = detect_healthy_signals(text)
        self.assertGreater(len(signals), 0)

    def test_detect_pytest_output(self):
        """Test detection of pytest output pattern."""
        text = "10 passed in 0.5s"
        signals = detect_healthy_signals(text)
        self.assertGreater(len(signals), 0)

    def test_detect_build_succeeded(self):
        """Test detection of build success pattern."""
        text = "Build succeeded with no warnings"
        signals = detect_healthy_signals(text)
        self.assertGreater(len(signals), 0)

    def test_detect_chinese_build_success(self):
        """Test detection of Chinese build success."""
        text = "项目构建成功，生成了 dist 目录"
        signals = detect_healthy_signals(text)
        self.assertGreater(len(signals), 0)

    def test_detect_file_created(self):
        """Test detection of file creation patterns."""
        text = "文件 output.txt 已创建"
        signals = detect_healthy_signals(text)
        self.assertGreater(len(signals), 0)


class TestEvidenceLevel(unittest.TestCase):
    """Tests for evidence level evaluation."""

    def test_l0_speculation(self):
        """Test L0 level for speculative content."""
        output = {"summary": "我觉得这样应该可以解决问题"}
        level, reasons = evaluate_evidence_level(output)
        self.assertEqual(level, "L0")
        self.assertTrue(any("Speculation" in r for r in reasons))

    def test_l1_reference_only(self):
        """Test L1 level for reference-only content."""
        output = {"summary": "The function is defined in utils.py module"}
        level, reasons = evaluate_evidence_level(output)
        self.assertEqual(level, "L1")
        self.assertTrue(any("Reference only" in r for r in reasons))

    def test_l2_local_verification(self):
        """Test L2 level for local verification evidence."""
        output = {
            "summary": "根据 src/auth.py:15 验证了用户认证逻辑",
            "commands_executed": ["python -m pytest tests/"]
        }
        level, reasons = evaluate_evidence_level(output)
        self.assertEqual(level, "L2")

    def test_l2_with_healthy_signals(self):
        """Test L2 level with healthy evidence patterns."""
        output = {"summary": "Build succeeded. 10 passed in 0.3s"}
        level, reasons = evaluate_evidence_level(output)
        self.assertEqual(level, "L2")

    def test_l3_end_to_end(self):
        """Test L3 level for end-to-end testing."""
        output = {
            "summary": "端到端测试全部通过",
            "test_results": {"passed": 10, "failed": 0}
        }
        level, reasons = evaluate_evidence_level(output)
        self.assertEqual(level, "L3")

    def test_l3_with_test_results(self):
        """Test L3 level when test_results are present."""
        output = {
            "summary": "All tests passed",
            "test_results": {"total": 5, "passed": 5}
        }
        level, reasons = evaluate_evidence_level(output)
        self.assertEqual(level, "L3")

    def test_evidence_from_findings(self):
        """Test evidence extraction from findings field."""
        output = {
            "summary": "Analysis complete",
            "findings": ["应该可以正常工作"]
        }
        level, reasons = evaluate_evidence_level(output)
        self.assertEqual(level, "L0")

    def test_evidence_from_claims(self):
        """Test evidence extraction from claims field."""
        output = {
            "summary": "Review complete",
            "claims": ["I think this is correct"]
        }
        level, reasons = evaluate_evidence_level(output)
        self.assertEqual(level, "L0")


class TestOutputValidation(unittest.TestCase):
    """Tests for output format validation."""

    def test_eye_format_valid(self):
        """Test valid eye/explorer output format."""
        output = {"summary": "Found 5 files", "files": ["a.py", "b.py"]}
        valid, issues = validate_output_format(output, "eye")
        self.assertTrue(valid)
        self.assertEqual(len(issues), 0)

    def test_eye_format_with_findings(self):
        """Test eye format with findings instead of files."""
        output = {"summary": "Analysis done", "findings": ["Found issue X"]}
        valid, issues = validate_output_format(output, "explorer")
        self.assertTrue(valid)

    def test_eye_format_missing_files(self):
        """Test invalid eye output missing files/findings."""
        output = {"summary": "Done"}
        valid, issues = validate_output_format(output, "eye")
        self.assertFalse(valid)
        self.assertTrue(any("files" in i or "findings" in i for i in issues))

    def test_nose_format_valid(self):
        """Test valid nose/reviewer output format."""
        output = {"summary": "Review complete", "issues": ["Minor style issue"]}
        valid, issues = validate_output_format(output, "nose")
        self.assertTrue(valid)

    def test_nose_format_with_verdict(self):
        """Test nose format with verdict instead of issues."""
        output = {"summary": "Code looks good", "verdict": "APPROVED"}
        valid, issues = validate_output_format(output, "reviewer")
        self.assertTrue(valid)

    def test_nose_format_missing_issues(self):
        """Test invalid nose output missing issues/verdict."""
        output = {"summary": "Review done"}
        valid, issues = validate_output_format(output, "nose")
        self.assertFalse(valid)

    def test_body_format_valid(self):
        """Test valid body/impl output format."""
        output = {"summary": "Implemented feature", "changes": ["Added function X"]}
        valid, issues = validate_output_format(output, "body")
        self.assertTrue(valid)

    def test_body_format_with_files_modified(self):
        """Test body format with files_modified."""
        output = {"summary": "Done", "files_modified": ["src/main.py"]}
        valid, issues = validate_output_format(output, "impl")
        self.assertTrue(valid)

    def test_body_format_missing_changes(self):
        """Test invalid body output missing changes."""
        output = {"summary": "Implemented"}
        valid, issues = validate_output_format(output, "body")
        self.assertFalse(valid)

    def test_tongue_format_valid(self):
        """Test valid tongue/tester output format."""
        output = {"summary": "Tests passed", "test_results": {"passed": 5}}
        valid, issues = validate_output_format(output, "tongue")
        self.assertTrue(valid)

    def test_tongue_format_with_tests(self):
        """Test tongue format with tests field."""
        output = {"summary": "Testing done", "tests": ["test1", "test2"]}
        valid, issues = validate_output_format(output, "tester")
        self.assertTrue(valid)

    def test_tongue_format_missing_results(self):
        """Test invalid tongue output missing test_results."""
        output = {"summary": "Tested"}
        valid, issues = validate_output_format(output, "tongue")
        self.assertFalse(valid)

    def test_missing_summary(self):
        """Test that missing summary is flagged."""
        output = {"files": ["a.py"]}
        valid, issues = validate_output_format(output, "eye")
        self.assertFalse(valid)
        self.assertTrue(any("summary" in i for i in issues))

    def test_unknown_role(self):
        """Test validation with unknown role."""
        output = {"summary": "Done"}
        valid, issues = validate_output_format(output, "unknown")
        # Only summary check applies
        self.assertTrue(valid)


class TestTrackThreshold(unittest.TestCase):
    """Tests for track threshold checking."""

    def test_fix_track_threshold_l2(self):
        """Test fix track requires L2."""
        meets, msg = check_track_threshold("L2", "fix")
        self.assertTrue(meets)
        self.assertIn("meets", msg.lower())

    def test_fix_track_threshold_l1_fails(self):
        """Test fix track rejects L1."""
        meets, msg = check_track_threshold("L1", "fix")
        self.assertFalse(meets)
        self.assertIn("below", msg.lower())

    def test_feature_track_threshold(self):
        """Test feature track threshold."""
        meets, msg = check_track_threshold("L2", "feature")
        self.assertTrue(meets)

    def test_refactor_track_threshold(self):
        """Test refactor track threshold."""
        meets, msg = check_track_threshold("L3", "refactor")
        self.assertTrue(meets)

    def test_direct_track_threshold(self):
        """Test direct track only requires L1."""
        meets, msg = check_track_threshold("L1", "direct")
        self.assertTrue(meets)

    def test_l0_never_meets_threshold(self):
        """Test L0 never meets any threshold."""
        for track in ["fix", "feature", "refactor", "direct"]:
            meets, msg = check_track_threshold("L0", track)
            self.assertFalse(meets)

    def test_l3_always_meets_threshold(self):
        """Test L3 always meets all thresholds."""
        for track in ["fix", "feature", "refactor", "direct"]:
            meets, msg = check_track_threshold("L3", track)
            self.assertTrue(meets)

    def test_unknown_track_defaults_to_l2(self):
        """Test unknown track defaults to L2 threshold."""
        meets, msg = check_track_threshold("L1", "unknown_track")
        self.assertFalse(meets)  # L1 < L2

        meets, msg = check_track_threshold("L2", "unknown_track")
        self.assertTrue(meets)


class TestProcessSubagentStop(unittest.TestCase):
    """Tests for complete subagent stop processing."""

    def test_successful_processing(self):
        """Test successful subagent stop processing."""
        output = {
            "summary": "Found relevant files",
            "files": ["src/main.py", "src/utils.py"],
            "commands_executed": ["find . -name '*.py'"]
        }
        result = process_subagent_stop(
            node_id="eye_explore",
            graph_id="tg_123",
            output=output,
            track="direct"
        )
        self.assertTrue(result["success"])
        self.assertIn("evidence", result)
        self.assertIn("validation", result)

    def test_l0_rejection(self):
        """Test that L0 evidence causes rejection."""
        output = {"summary": "我觉得应该可以工作", "findings": []}
        result = process_subagent_stop(
            node_id="eye_explore",
            graph_id="tg_123",
            output=output,
            track="fix"
        )
        self.assertFalse(result["success"])
        self.assertEqual(result["evidence"]["level"], "L0")
        self.assertIn("error", result)

    def test_threshold_rejection(self):
        """Test that insufficient evidence level causes rejection."""
        output = {"summary": "Code looks reasonable", "files": ["a.py"]}
        result = process_subagent_stop(
            node_id="eye_explore",
            graph_id="tg_123",
            output=output,
            track="fix"  # Requires L2
        )
        # L1 evidence should fail for fix track
        self.assertFalse(result["success"])

    def test_role_inference_from_node_id(self):
        """Test that role is inferred from node_id."""
        output = {"summary": "Done", "issues": ["Issue 1"]}
        result = process_subagent_stop(
            node_id="nose_review_code",
            graph_id="tg_123",
            output=output,
            track="direct"
        )
        # Should infer nose role and validate accordingly
        self.assertTrue(result["validation"]["format_valid"])

    def test_format_warnings(self):
        """Test that format issues generate warnings."""
        output = {
            "summary": "Explored the codebase",
            # Missing 'files' or 'findings' for eye role
            "commands_executed": ["ls"]
        }
        result = process_subagent_stop(
            node_id="eye_explore",
            graph_id="tg_123",
            output=output,
            track="direct"
        )
        # Should still succeed but have warnings
        if not result["validation"]["format_valid"]:
            self.assertIn("warnings", result)

    def test_next_actions_on_success(self):
        """Test that successful processing includes next actions."""
        output = {
            "summary": "Build succeeded. 5 passed tests.",
            "test_results": {"passed": 5},
            "tests": ["test1", "test2"]
        }
        result = process_subagent_stop(
            node_id="tongue_test",
            graph_id="tg_123",
            output=output,
            track="direct"
        )
        self.assertTrue(result["success"])
        self.assertGreater(len(result["next_actions"]), 0)
        actions = [a["action"] for a in result["next_actions"]]
        self.assertIn("trigger_downstream", actions)

    def test_anchor_candidate_suggestion(self):
        """Test that high evidence level suggests anchor check."""
        output = {
            "summary": "端到端测试通过",
            "test_results": {"passed": 10}
        }
        result = process_subagent_stop(
            node_id="tongue_test",
            graph_id="tg_123",
            output=output,
            track="direct"
        )
        self.assertTrue(result["success"])
        # L3 should suggest anchor candidate check
        if result["evidence"]["level"] in ("L2", "L3"):
            actions = [a["action"] for a in result["next_actions"]]
            self.assertIn("check_anchor_candidate", actions)


if __name__ == "__main__":
    unittest.main()
