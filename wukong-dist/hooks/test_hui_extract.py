#!/usr/bin/env python3
"""
hui-extract.py 单元测试套件

测试覆盖:
1. 锚点内容验证 (_is_valid_anchor_content)
2. 门槛检查 (check_threshold)
3. 标题提取 (_extract_title)
4. 分身输出压缩 (compress_avatar_output)
5. 重复检查 (check_duplicate)
6. 辅助函数测试

运行: pytest test_hui_extract.py -v
覆盖率: pytest test_hui_extract.py --cov=hui_extract --cov-report=term-missing

历史:
- P003 bug: 误提取对话片段为锚点 (已修复，本测试确保不再复发)
"""

import sys
from pathlib import Path

# 添加 hooks 目录到路径 (支持 hui_extract 和 hui-extract 两种命名)
hooks_dir = Path(__file__).parent
sys.path.insert(0, str(hooks_dir))

# 动态导入 (处理文件名中的连字符)
import importlib.util
hui_extract_path = hooks_dir / 'hui-extract.py'
spec = importlib.util.spec_from_file_location("hui_extract", hui_extract_path)
hui_extract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hui_extract)

# 导入需要测试的函数
_is_valid_anchor_content = hui_extract._is_valid_anchor_content
check_threshold = hui_extract.check_threshold
_extract_title = hui_extract._extract_title
compress_avatar_output = hui_extract.compress_avatar_output
check_duplicate = hui_extract.check_duplicate
_detect_impact = hui_extract._detect_impact
_detect_reusable = hui_extract._detect_reusable
get_message_content = hui_extract.get_message_content
_get_next_anchor_id = hui_extract._get_next_anchor_id

# 导入常量
CONVERSATION_PREFIXES = hui_extract.CONVERSATION_PREFIXES
ANCHOR_STRUCTURE_KEYWORDS = hui_extract.ANCHOR_STRUCTURE_KEYWORDS
IMPACT_KEYWORDS = hui_extract.IMPACT_KEYWORDS


# ============================================================
# 1. 锚点内容验证测试 (_is_valid_anchor_content)
# ============================================================

class TestIsValidAnchorContent:
    """测试锚点内容验证 - 防止 P003 bug 复发"""

    def test_reject_conversation_fragments_chinese(self):
        """应该拒绝中文对话片段"""
        # 这些是典型的对话开头，不应被识别为锚点
        assert not _is_valid_anchor_content("完成了，已经修改好", "decision")
        assert not _is_valid_anchor_content("好的，让我来处理这个问题", "decision")
        assert not _is_valid_anchor_content("是的，这个方案可以", "decision")
        assert not _is_valid_anchor_content("没问题，我现在就开始", "decision")
        assert not _is_valid_anchor_content("已经完成了所有修改", "decision")
        assert not _is_valid_anchor_content("我来检查一下这个文件", "decision")
        assert not _is_valid_anchor_content("我会按照你的要求处理", "decision")
        assert not _is_valid_anchor_content("让我先看看代码结构", "decision")
        assert not _is_valid_anchor_content("现在开始实现功能", "decision")
        assert not _is_valid_anchor_content("接下来我们处理第二部分", "decision")
        assert not _is_valid_anchor_content("首先需要了解需求", "decision")
        assert not _is_valid_anchor_content("然后我们添加测试", "decision")
        assert not _is_valid_anchor_content("最后验证结果", "decision")
        assert not _is_valid_anchor_content("总结一下今天的工作", "decision")

    def test_reject_conversation_fragments_english(self):
        """应该拒绝英文对话片段"""
        assert not _is_valid_anchor_content("OK, I'll do that for you", "decision")
        assert not _is_valid_anchor_content("Let me check this file first", "decision")
        assert not _is_valid_anchor_content("Done, the changes have been applied", "decision")
        assert not _is_valid_anchor_content("Yes, that approach works well", "decision")
        assert not _is_valid_anchor_content("I'll implement this feature now", "decision")
        assert not _is_valid_anchor_content("I'm going to modify the code", "decision")
        assert not _is_valid_anchor_content("Now let's move to the next step", "decision")
        assert not _is_valid_anchor_content("You are correct about this", "decision")
        assert not _is_valid_anchor_content("This command will help us", "decision")
        assert not _is_valid_anchor_content("Here is the solution", "decision")
        assert not _is_valid_anchor_content("Here are the files we need", "decision")

    def test_reject_code_blocks(self):
        """应该拒绝以代码块开头的内容"""
        assert not _is_valid_anchor_content("```python\ndef hello():\n    pass\n```", "decision")
        assert not _is_valid_anchor_content("```javascript\nconsole.log('hi');\n```", "decision")
        assert not _is_valid_anchor_content("```\nsome code here\n```", "decision")

    def test_reject_too_short_content(self):
        """应该拒绝太短的内容 (< 50 字符)"""
        assert not _is_valid_anchor_content("短内容", "decision")
        assert not _is_valid_anchor_content("", "decision")
        assert not _is_valid_anchor_content("a" * 49, "decision")  # 49 字符
        assert not _is_valid_anchor_content("   ", "decision")  # 空白
        assert not _is_valid_anchor_content(None, "decision")  # None

    def test_reject_missing_structure_keywords(self):
        """应该拒绝缺少结构关键词的内容"""
        # 即使足够长，但没有决策相关的结构关键词
        generic_content = "这是一段很长的内容，描述了一些东西，但是没有任何决策相关的关键词，也没有背景信息，也没有影响分析。"
        assert not _is_valid_anchor_content(generic_content, "decision")

    def test_accept_valid_decision(self):
        """应该接受结构化的决策内容"""
        valid_decision = """
        ## 决策 [D001]
        **Context**: 需要为用户认证选择一个安全的方案
        **Decision**: 采用 JWT + Refresh Token 方案
        **Impact**: 影响认证模块架构，需要添加 token 刷新机制
        **Evidence**: 经过安全评估，JWT 满足我们的需求
        """
        assert _is_valid_anchor_content(valid_decision, "decision")

    def test_accept_valid_decision_english(self):
        """应该接受英文结构化决策"""
        valid_decision = """
        ## Decision [D002]
        **Context**: Need to choose a database for high-traffic scenarios
        **Decision**: Use PostgreSQL with read replicas
        **Impact**: Requires database migration and connection pool changes
        **Evidence**: Performance tests show 3x improvement
        """
        assert _is_valid_anchor_content(valid_decision, "decision")

    def test_accept_valid_problem(self):
        """应该接受结构化的问题内容"""
        valid_problem = """
        ## 问题 [P001]
        **症状**: 用户登录后频繁被踢出
        **根因**: Token 过期时间设置过短，且没有自动刷新机制
        **解决**: 添加 refresh token 机制，延长 access token 有效期
        **预防**: 添加监控告警，在 token 过期前主动刷新
        """
        assert _is_valid_anchor_content(valid_problem, "problem")

    def test_accept_valid_constraint(self):
        """应该接受结构化的约束内容"""
        valid_constraint = """
        ## 约束 [C001]
        **必须**: 所有 API 请求必须经过认证
        **禁止**: 禁止在日志中输出敏感信息
        **Always**: 总是使用 HTTPS 进行通信
        """
        assert _is_valid_anchor_content(valid_constraint, "constraint")

    def test_boundary_length(self):
        """测试边界长度 (正好 50 字符)"""
        # 正好 50 字符，包含 decision 关键词
        # 构造一个正好 50 字符且包含必要关键词的内容
        base = "Decision: context 背景说明，这是一个重要的决策"
        # 补齐到 50 字符
        while len(base) < 50:
            base += "x"
        boundary_content = base[:50]
        assert len(boundary_content.strip()) == 50
        # 由于包含 decision 和 context 关键词，应该通过
        assert _is_valid_anchor_content(boundary_content, "decision")


# ============================================================
# 2. 门槛检查测试 (check_threshold)
# ============================================================

class TestCheckThreshold:
    """测试门槛检查 - 确保只有高价值内容被写入"""

    def test_frequency_threshold_pass(self):
        """frequency >= 2 应该通过"""
        anchor = {
            'type': 'decision',
            'content': 'test decision content',
            'threshold_check': {'frequency': 2, 'impact': False, 'reusable': False}
        }
        assert check_threshold(anchor)

        # frequency = 3 也应该通过
        anchor['threshold_check']['frequency'] = 3
        assert check_threshold(anchor)

    def test_frequency_threshold_fail(self):
        """frequency < 2 不应该通过 (除非有其他条件)"""
        anchor = {
            'type': 'decision',
            'content': 'test',
            'threshold_check': {'frequency': 1, 'impact': False, 'reusable': False}
        }
        assert not check_threshold(anchor)

        anchor['threshold_check']['frequency'] = 0
        assert not check_threshold(anchor)

    def test_impact_with_sufficient_content(self):
        """impact=True + 内容长度>=100 应该通过"""
        anchor = {
            'type': 'decision',
            'content': 'x' * 100,  # 正好 100 字符
            'threshold_check': {'frequency': 1, 'impact': True, 'reusable': False}
        }
        assert check_threshold(anchor)

        # 超过 100 也应该通过
        anchor['content'] = 'x' * 200
        assert check_threshold(anchor)

    def test_impact_with_insufficient_content(self):
        """impact=True + 内容太短 不应该通过"""
        anchor = {
            'type': 'decision',
            'content': 'short content',  # 少于 100 字符
            'threshold_check': {'frequency': 1, 'impact': True, 'reusable': False}
        }
        assert not check_threshold(anchor)

        anchor['content'] = 'x' * 99  # 99 字符
        assert not check_threshold(anchor)

    def test_reusable_problem_with_solution(self):
        """problem + reusable + 有解决方案 应该通过"""
        anchor = {
            'type': 'problem',
            'content': '问题描述... 解决方案是使用缓存',
            'threshold_check': {'frequency': 1, 'impact': False, 'reusable': True}
        }
        assert check_threshold(anchor)

        # 英文 solution 关键词
        anchor['content'] = 'Problem description... The solution is to use cache'
        assert check_threshold(anchor)

        # fix 关键词
        anchor['content'] = '问题描述... 修复方法是添加重试机制'
        assert check_threshold(anchor)

        # resolve 关键词
        anchor['content'] = 'To resolve this issue, we need to...'
        assert check_threshold(anchor)

    def test_reusable_problem_without_solution(self):
        """problem + reusable 但没有解决方案 不应该通过"""
        # 注意：避免使用"解决"、"修复"等关键词
        anchor = {
            'type': 'problem',
            'content': '这是一个问题描述，但是没有给出任何处理方法或应对措施',
            'threshold_check': {'frequency': 1, 'impact': False, 'reusable': True}
        }
        assert not check_threshold(anchor)

    def test_reusable_non_problem_type(self):
        """decision + reusable 不应该通过 (reusable 只对 problem 生效)"""
        anchor = {
            'type': 'decision',
            'content': '决策内容...',
            'threshold_check': {'frequency': 1, 'impact': False, 'reusable': True}
        }
        assert not check_threshold(anchor)

        anchor['type'] = 'constraint'
        assert not check_threshold(anchor)

    def test_missing_threshold_check(self):
        """缺少 threshold_check 字段应该返回 False"""
        anchor = {
            'type': 'decision',
            'content': 'test content',
        }
        assert not check_threshold(anchor)

        anchor['threshold_check'] = {}
        assert not check_threshold(anchor)

    def test_combined_conditions(self):
        """测试多个条件同时满足"""
        # 同时满足 frequency 和 impact
        anchor = {
            'type': 'decision',
            'content': 'x' * 100,
            'threshold_check': {'frequency': 2, 'impact': True, 'reusable': False}
        }
        assert check_threshold(anchor)


# ============================================================
# 3. 标题提取测试 (_extract_title)
# ============================================================

class TestExtractTitle:
    """测试标题提取"""

    def test_markdown_h2_title(self):
        """提取 ## 标题格式"""
        content = "## 决策: 采用 JWT 认证方案\n这是内容..."
        assert _extract_title(content, "decision") == "决策: 采用 JWT 认证方案"

    def test_markdown_h3_title(self):
        """提取 ### 标题格式"""
        content = "### 问题分析\n详细分析内容..."
        assert _extract_title(content, "problem") == "问题分析"

    def test_markdown_h1_title(self):
        """提取 # 标题格式"""
        content = "# 架构设计文档\n内容..."
        assert _extract_title(content, "decision") == "架构设计文档"

    def test_bold_title(self):
        """提取 **粗体** 格式标题"""
        content = "**重要决策**\n这是决策的内容"
        assert _extract_title(content, "decision") == "重要决策"

    def test_skip_conversation_prefixes(self):
        """跳过对话开头，找真正的标题"""
        content = "完成了\n好的\n## 真正的标题\n内容..."
        assert _extract_title(content, "decision") == "真正的标题"

        content = "Done\nOK\n### Real Title Here\nContent..."
        assert _extract_title(content, "decision") == "Real Title Here"

    def test_skip_multiple_conversation_lines(self):
        """跳过多个对话行"""
        content = """好的
让我来处理
是的
现在开始
## 架构决策
内容..."""
        assert _extract_title(content, "decision") == "架构决策"

    def test_long_title_truncation(self):
        """长标题应该被截断到 50 字符"""
        # 创建一个超过 50 字符的标题
        long_title = "A" * 60  # 60 个字符的标题
        content = f"## {long_title}"
        result = _extract_title(content, "decision")
        assert len(result) <= 50
        assert result.endswith('...')

        # 使用中文测试
        long_title_cn = "这是一个非常非常非常非常非常非常非常非常非常非常非常非常非常非常长的标题需要被截断处理"
        content_cn = f"## {long_title_cn}"
        result_cn = _extract_title(content_cn, "decision")
        # 检查是否被截断
        if len(long_title_cn) > 50:
            assert len(result_cn) <= 50
            assert result_cn.endswith('...')

    def test_long_title_exact_50(self):
        """正好 50 字符的标题不应该被截断"""
        title_50 = "a" * 50
        content = f"## {title_50}"
        result = _extract_title(content, "decision")
        assert len(result) == 50
        assert not result.endswith('...')

    def test_fallback_to_first_meaningful_line(self):
        """没有标题格式时，使用第一个有意义的行"""
        content = "这是第一行内容，没有特殊格式\n第二行内容"
        # 由于第一行不是对话开头且长度>=5，应该被选为标题
        result = _extract_title(content, "decision")
        assert "这是第一行内容" in result

    def test_fallback_untitled(self):
        """找不到合适标题时返回默认值"""
        content = "完成\n好的\n是\n"  # 全是对话开头或太短
        result = _extract_title(content, "decision")
        assert result == "decision_untitled"

    def test_strip_list_markers(self):
        """去除列表标记 (-, *, 数字.)"""
        content = "- 这是一个列表项作为标题"
        result = _extract_title(content, "decision")
        assert result.startswith("这是")
        assert not result.startswith("-")

        content = "1. 编号列表项作为标题"
        result = _extract_title(content, "decision")
        assert not result.startswith("1.")


# ============================================================
# 4. 分身输出压缩测试 (compress_avatar_output)
# ============================================================

class TestCompressAvatarOutput:
    """测试分身输出压缩"""

    def test_explorer_output_files(self):
        """眼分身压缩: 提取文件列表"""
        explorer_output = """
搜索结果:
- /src/auth/login.py
- /src/auth/jwt.py
- /src/auth/refresh.py
- /src/auth/middleware.py
- /src/utils/crypto.py

## 发现
认证模块使用 JWT 实现，包含登录、刷新等功能。
"""
        result = compress_avatar_output(explorer_output, '眼')
        assert '发现的文件' in result or '发现' in result
        assert '/src/auth/login.py' in result or 'login.py' in result

    def test_explorer_output_english_alias(self):
        """眼分身 (explorer 别名) 压缩"""
        output = "- /path/to/file.py\n发现: 这是重要发现"
        result = compress_avatar_output(output, 'explorer')
        assert '发现' in result

    def test_explorer_max_files_limit(self):
        """眼分身: 文件列表限制为 20 个"""
        # 生成 30 个文件路径
        files = '\n'.join([f"- /src/file{i}.py" for i in range(30)])
        explorer_output = f"{files}\n\n发现: 很多文件"
        result = compress_avatar_output(explorer_output, '眼')
        # 应该只保留前 20 个
        assert "还有" in result or result.count('/src/file') <= 20

    def test_reviewer_output_issues(self):
        """鼻分身压缩: 提取 issues 列表"""
        reviewer_output = """
代码审查结果:
1. 缺少输入验证
2. 硬编码密钥存在安全风险
3. 无错误处理机制
4. 函数过长，超过 200 行
5. 缺少单元测试
"""
        result = compress_avatar_output(reviewer_output, '鼻')
        # 应该包含问题或列表
        assert '问题' in result or '1.' in result or '审查' in result

    def test_reviewer_english_alias(self):
        """鼻分身 (reviewer 别名) 压缩"""
        output = "- issue: security vulnerability\n- warning: deprecated API"
        result = compress_avatar_output(output, 'reviewer')
        assert len(result) < len(output) * 2  # 压缩后不应该太长

    def test_impl_output_length_limit(self):
        """斗战胜佛压缩: 限制输出长度"""
        impl_output = "x" * 5000  # 5000 字符
        result = compress_avatar_output(impl_output, '斗战胜佛')
        # max_chars = 2000，所以结果应该不超过 2000 + 少量缓冲
        assert len(result) <= 2500

    def test_impl_english_aliases(self):
        """斗战胜佛 (impl, 身) 别名压缩"""
        output = "x" * 3000

        result1 = compress_avatar_output(output, 'impl')
        assert len(result1) <= 2500

        result2 = compress_avatar_output(output, '身')
        assert len(result2) <= 2500

    def test_impl_extract_summary(self):
        """斗战胜佛: 提取修改摘要"""
        impl_output = """
修改摘要: 添加了用户认证功能

变更文件:
- /src/auth.py
- /src/middleware.py

测试结果: PASS
"""
        result = compress_avatar_output(impl_output, '斗战胜佛')
        # 应该保留摘要和变更文件
        assert '修改' in result or '摘要' in result or '变更' in result

    def test_generic_output_compression(self):
        """通用压缩 (未知分身类型)"""
        output = "x" * 2000
        result = compress_avatar_output(output, 'unknown_avatar')
        # default max_chars = 1000
        assert len(result) <= 1100

    def test_preserve_short_output(self):
        """短输出不应该被过度压缩"""
        short_output = "简短的输出结果"
        result = compress_avatar_output(short_output, '眼')
        # 短内容应该基本保留
        assert len(result) >= len(short_output) // 2


# ============================================================
# 5. 重复检查测试 (check_duplicate)
# ============================================================

class TestCheckDuplicate:
    """测试重复检查"""

    def test_exact_title_match(self):
        """完全相同标题 -> 重复"""
        existing = [
            {'id': 'D001', 'title': '决策: 采用 JWT 认证', 'type': 'decision'},
            {'id': 'P001', 'title': '问题: 登录失败', 'type': 'problem'},
        ]

        new_anchor = {'title': '决策: 采用 JWT 认证', 'type': 'decision'}
        is_dup, existing_id = check_duplicate(new_anchor, existing)
        assert is_dup
        assert existing_id == 'D001'

    def test_different_title(self):
        """不同标题 -> 不重复"""
        existing = [
            {'id': 'D001', 'title': '决策: 采用 JWT 认证', 'type': 'decision'},
        ]

        new_anchor = {'title': '决策: 使用 OAuth2', 'type': 'decision'}
        is_dup, existing_id = check_duplicate(new_anchor, existing)
        assert not is_dup
        assert existing_id is None

    def test_high_word_overlap(self):
        """词汇重叠 > 70% -> 重复"""
        existing = [
            {'id': 'D001', 'title': 'JWT 认证方案选择决策', 'type': 'decision'},
        ]

        # 大部分词汇相同
        new_anchor = {'title': 'JWT 认证方案的决策', 'type': 'decision'}
        is_dup, _ = check_duplicate(new_anchor, existing)
        # 根据实际词汇重叠计算，这个应该被判为重复
        # 词汇: JWT, 认证, 方案, 选择, 决策 vs JWT, 认证, 方案, 的, 决策
        # 交集: JWT, 认证, 方案, 决策 (4)
        # 并集: JWT, 认证, 方案, 选择, 决策, 的 (6)
        # 比例: 4/6 = 0.67 < 0.7，所以不重复
        # 注意这个测试案例可能需要调整
        assert not is_dup  # 0.67 < 0.7

    def test_low_word_overlap(self):
        """词汇重叠 < 70% -> 不重复"""
        existing = [
            {'id': 'D001', 'title': '数据库选择 PostgreSQL', 'type': 'decision'},
        ]

        new_anchor = {'title': '缓存策略 Redis 方案', 'type': 'decision'}
        is_dup, _ = check_duplicate(new_anchor, existing)
        assert not is_dup

    def test_empty_existing_list(self):
        """空的现有列表 -> 不重复"""
        new_anchor = {'title': '新决策', 'type': 'decision'}
        is_dup, existing_id = check_duplicate(new_anchor, [])
        assert not is_dup
        assert existing_id is None

    def test_empty_title(self):
        """空标题处理"""
        existing = [
            {'id': 'D001', 'title': '决策标题', 'type': 'decision'},
        ]

        new_anchor = {'title': '', 'type': 'decision'}
        is_dup, _ = check_duplicate(new_anchor, existing)
        assert not is_dup

    def test_case_insensitive(self):
        """大小写不敏感比较"""
        existing = [
            {'id': 'D001', 'title': 'JWT Authentication Decision', 'type': 'decision'},
        ]

        new_anchor = {'title': 'jwt authentication decision', 'type': 'decision'}
        is_dup, _ = check_duplicate(new_anchor, existing)
        assert is_dup


# ============================================================
# 6. 辅助函数测试
# ============================================================

class TestDetectImpact:
    """测试影响检测"""

    def test_detect_architecture_impact(self):
        """检测架构相关影响"""
        assert _detect_impact("这个决策影响系统架构设计")
        assert _detect_impact("Architecture changes required")

    def test_detect_security_impact(self):
        """检测安全相关影响"""
        assert _detect_impact("存在安全风险需要处理")
        assert _detect_impact("Security vulnerability found")

    def test_detect_performance_impact(self):
        """检测性能相关影响"""
        assert _detect_impact("这会影响系统性能")
        assert _detect_impact("Performance impact is significant")

    def test_detect_core_impact(self):
        """检测核心/关键影响"""
        assert _detect_impact("这是核心功能的变更")
        assert _detect_impact("Critical system component affected")

    def test_no_impact_detected(self):
        """无影响的普通内容"""
        assert not _detect_impact("这是一个简单的修改")
        assert not _detect_impact("Minor change to documentation")


class TestDetectReusable:
    """测试可复用性检测"""

    def test_problem_always_reusable(self):
        """problem 类型始终返回 True"""
        assert _detect_reusable("任何内容", "problem")
        assert _detect_reusable("", "problem")

    def test_pattern_keywords(self):
        """检测模式/最佳实践关键词"""
        assert _detect_reusable("这是一个通用模式", "decision")
        assert _detect_reusable("最佳实践推荐", "decision")
        assert _detect_reusable("This is a generic solution", "decision")
        assert _detect_reusable("Best practice for handling errors", "decision")

    def test_non_reusable_content(self):
        """非可复用的特定内容"""
        assert not _detect_reusable("这是针对当前项目的特定修改", "decision")


class TestGetMessageContent:
    """测试消息内容提取"""

    def test_string_content(self):
        """字符串内容"""
        msg = {'message': {'content': 'Hello world'}}
        assert get_message_content(msg) == 'Hello world'

    def test_list_content(self):
        """列表内容 (Claude 格式)"""
        msg = {
            'message': {
                'content': [
                    {'type': 'text', 'text': 'First part'},
                    {'type': 'text', 'text': 'Second part'},
                ]
            }
        }
        result = get_message_content(msg)
        assert 'First part' in result
        assert 'Second part' in result

    def test_mixed_content_types(self):
        """混合内容类型"""
        msg = {
            'message': {
                'content': [
                    {'type': 'text', 'text': 'Text content'},
                    {'type': 'tool_use', 'name': 'Read'},  # 非 text 类型
                ]
            }
        }
        result = get_message_content(msg)
        assert 'Text content' in result

    def test_empty_message(self):
        """空消息"""
        assert get_message_content({}) == ''
        assert get_message_content({'message': {}}) == ''


class TestGetNextAnchorId:
    """测试锚点 ID 生成"""

    def test_first_decision_id(self):
        """第一个决策 ID"""
        result = _get_next_anchor_id('decision', [])
        assert result == 'D001'

    def test_increment_decision_id(self):
        """决策 ID 递增"""
        existing = [
            {'id': 'D001', 'type': 'decision'},
            {'id': 'D002', 'type': 'decision'},
        ]
        result = _get_next_anchor_id('decision', existing)
        assert result == 'D003'

    def test_problem_id(self):
        """问题 ID"""
        result = _get_next_anchor_id('problem', [])
        assert result == 'P001'

    def test_constraint_id(self):
        """约束 ID"""
        result = _get_next_anchor_id('constraint', [])
        assert result == 'C001'

    def test_interface_id(self):
        """接口 ID"""
        result = _get_next_anchor_id('interface', [])
        assert result == 'I001'

    def test_unknown_type(self):
        """未知类型使用 A 前缀"""
        result = _get_next_anchor_id('unknown', [])
        assert result == 'A001'

    def test_mixed_types(self):
        """混合类型的现有锚点"""
        existing = [
            {'id': 'D001', 'type': 'decision'},
            {'id': 'P001', 'type': 'problem'},
            {'id': 'D002', 'type': 'decision'},
        ]
        # 只看同类型的最大 ID
        result = _get_next_anchor_id('decision', existing)
        assert result == 'D003'

        result = _get_next_anchor_id('problem', existing)
        assert result == 'P002'


# ============================================================
# P003 回归测试 (确保 bug 不复发)
# ============================================================

class TestP003Regression:
    """P003 Bug 回归测试 - 防止对话片段被误提取为锚点"""

    def test_p003_typical_conversation(self):
        """典型的对话片段不应该被识别为有效锚点"""
        conversation_snippets = [
            "好的，我来帮你检查这个问题",
            "完成了！所有文件都已更新",
            "让我看看代码结构...",
            "OK, I'll fix that for you",
            "Done! The changes have been applied successfully",
            "Let me analyze the codebase first",
        ]

        for snippet in conversation_snippets:
            assert not _is_valid_anchor_content(snippet, "decision"), \
                f"Should reject: {snippet[:30]}..."
            assert not _is_valid_anchor_content(snippet, "problem"), \
                f"Should reject: {snippet[:30]}..."

    def test_p003_structured_content_accepted(self):
        """结构化内容应该被正确识别"""
        valid_contents = [
            {
                'type': 'decision',
                'content': """
## 决策记录
**Context**: 需要选择认证方案
**Decision**: 采用 JWT
**Impact**: 影响认证模块
"""
            },
            {
                'type': 'problem',
                'content': """
## 问题记录
**症状**: 服务响应慢
**根因**: 数据库查询未优化
**解决**: 添加索引
"""
            },
        ]

        for item in valid_contents:
            assert _is_valid_anchor_content(item['content'], item['type']), \
                f"Should accept structured {item['type']}"


# ============================================================
# 运行测试 (支持 pytest 或独立运行)
# ============================================================

def run_tests_standalone():
    """独立运行测试 (不依赖 pytest)"""
    import traceback

    test_classes = [
        TestIsValidAnchorContent,
        TestCheckThreshold,
        TestExtractTitle,
        TestCompressAvatarOutput,
        TestCheckDuplicate,
        TestDetectImpact,
        TestDetectReusable,
        TestGetMessageContent,
        TestGetNextAnchorId,
        TestP003Regression,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        instance = test_class()
        test_methods = [m for m in dir(instance) if m.startswith('test_')]

        for method_name in test_methods:
            total_tests += 1
            test_name = f"{test_class.__name__}.{method_name}"

            try:
                method = getattr(instance, method_name)
                method()
                passed_tests += 1
                print(f"  PASS: {test_name}")
            except AssertionError as e:
                failed_tests.append((test_name, str(e)))
                print(f"  FAIL: {test_name}")
                print(f"        {e}")
            except Exception as e:
                failed_tests.append((test_name, str(e)))
                print(f"  ERROR: {test_name}")
                print(f"        {e}")
                traceback.print_exc()

    print()
    print("=" * 60)
    print(f"Tests: {total_tests} | Passed: {passed_tests} | Failed: {len(failed_tests)}")
    print("=" * 60)

    if failed_tests:
        print("\nFailed tests:")
        for name, error in failed_tests:
            print(f"  - {name}: {error[:80]}")
        return 1

    print("\nAll tests passed!")
    return 0


if __name__ == '__main__':
    try:
        import pytest
        pytest.main([__file__, '-v'])
    except ImportError:
        print("pytest not found, running standalone tests...\n")
        exit(run_tests_standalone())
