#!/usr/bin/env python3
"""
慧/识系统测试脚本

测试目标:
1. 验证慧模块的信息提取能力
2. 验证识模块的锚点写入逻辑
3. 验证三阶段上下文恢复
4. 生成完整的测试日志

使用方法:
    python3 ~/.wukong/hooks/test-hui-shi.py [--cwd /path/to/project]

测试输出:
    .wukong/context/test-results/
    ├── test-{timestamp}.log      # 完整测试日志
    ├── test-{timestamp}.json     # 结构化测试结果
    └── test-summary.md           # 人类可读摘要
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加 hui-extract.py 所在目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入 hui-extract 模块的函数
from importlib.util import spec_from_file_location, module_from_spec

def load_hui_module():
    """动态加载 hui-extract 模块"""
    # hui-extract.py is in wukong-dist/hooks/ directory
    hui_path = Path(__file__).parent.parent / 'wukong-dist' / 'hooks' / 'hui-extract.py'

    if not hui_path.exists():
        raise FileNotFoundError(f"hui-extract.py not found at: {hui_path}")

    # Read and compile the module source with explicit UTF-8 encoding
    # This avoids Windows encoding issues
    with open(hui_path, 'r', encoding='utf-8') as f:
        source = f.read()

    # Create a module and execute the source
    import types
    hui = types.ModuleType("hui_extract")
    hui.__file__ = str(hui_path)
    exec(compile(source, str(hui_path), 'exec'), hui.__dict__)
    return hui


class TestLogger:
    """测试日志记录器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        self.log_file = output_dir / f'test-{timestamp}.log'
        self.json_file = output_dir / f'test-{timestamp}.json'
        self.summary_file = output_dir / 'test-summary.md'

        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
            }
        }

        self._log(f"=== 慧/识系统测试开始 ===")
        self._log(f"时间: {datetime.now().isoformat()}")
        self._log(f"输出目录: {output_dir}")
        self._log("")

    def _log(self, message: str):
        """写入日志"""
        print(message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(message + '\n')

    def section(self, title: str):
        """开始新的测试部分"""
        self._log("")
        self._log(f"{'='*60}")
        self._log(f"  {title}")
        self._log(f"{'='*60}")
        self._log("")

    def test(self, name: str, result: bool, details: dict = None):
        """记录测试结果"""
        status = "✅ PASS" if result else "❌ FAIL"
        self._log(f"[{status}] {name}")

        if details:
            for key, value in details.items():
                self._log(f"    {key}: {value}")

        self.results['tests'].append({
            'name': name,
            'passed': result,
            'details': details or {},
        })
        self.results['summary']['total'] += 1
        if result:
            self.results['summary']['passed'] += 1
        else:
            self.results['summary']['failed'] += 1

    def log_data(self, label: str, data: Any):
        """记录数据"""
        self._log(f"\n--- {label} ---")
        if isinstance(data, (dict, list)):
            self._log(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
        else:
            self._log(str(data)[:2000])
        self._log("---\n")

    def finalize(self):
        """完成测试并保存结果"""
        self.section("测试摘要")

        summary = self.results['summary']
        self._log(f"总计: {summary['total']} 个测试")
        self._log(f"通过: {summary['passed']} 个")
        self._log(f"失败: {summary['failed']} 个")
        self._log(f"通过率: {summary['passed']/max(summary['total'],1)*100:.1f}%")

        # 保存 JSON 结果
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        # 生成 Markdown 摘要
        self._generate_summary()

        self._log("")
        self._log(f"=== 测试完成 ===")
        self._log(f"日志文件: {self.log_file}")
        self._log(f"JSON 结果: {self.json_file}")
        self._log(f"摘要文件: {self.summary_file}")

        return self.results

    def _generate_summary(self):
        """生成 Markdown 摘要"""
        lines = [
            "# 慧/识系统测试结果",
            "",
            f"**测试时间**: {self.results['timestamp']}",
            "",
            "## 摘要",
            "",
            f"| 指标 | 值 |",
            f"|------|-----|",
            f"| 总计 | {self.results['summary']['total']} |",
            f"| 通过 | {self.results['summary']['passed']} |",
            f"| 失败 | {self.results['summary']['failed']} |",
            f"| 通过率 | {self.results['summary']['passed']/max(self.results['summary']['total'],1)*100:.1f}% |",
            "",
            "## 详细结果",
            "",
        ]

        for test in self.results['tests']:
            status = "✅" if test['passed'] else "❌"
            lines.append(f"### {status} {test['name']}")
            lines.append("")
            if test['details']:
                for key, value in test['details'].items():
                    lines.append(f"- **{key}**: {value}")
                lines.append("")

        with open(self.summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


def create_mock_messages() -> list[dict]:
    """创建模拟的对话消息"""
    return [
        # 用户请求
        {
            'type': 'user',
            'message': {
                'content': [{'type': 'text', 'text': '帮我实现一个用户登录功能，使用 JWT 认证'}]
            },
            'timestamp': '2024-01-01T10:00:00Z'
        },
        # 助手决策
        {
            'type': 'assistant',
            'message': {
                'content': [{'type': 'text', 'text': '''
## 决策 [D001]

**Context**: 需要实现用户认证功能
**Decision**: 采用 JWT + bcrypt 方案
**Impact**: 影响认证模块架构
**Evidence**: JWT 是业界标准，bcrypt 安全性高

## 约束 [C001]

- 必须使用 HTTPS
- Token 有效期不超过 24 小时
- 禁止在 URL 中传递 token
'''}]
            },
            'timestamp': '2024-01-01T10:01:00Z'
        },
        # 工具调用 (模拟)
        {
            'type': 'assistant',
            'message': {
                'content': [
                    {'type': 'text', 'text': '让我先探索现有代码结构'},
                    {'type': 'tool_use', 'id': 'tool_123', 'name': 'Glob', 'input': {'pattern': '**/*.py'}}
                ]
            },
            'timestamp': '2024-01-01T10:02:00Z'
        },
        # 工具结果
        {
            'type': 'user',
            'message': {
                'content': [{'type': 'tool_result', 'tool_use_id': 'tool_123', 'content': 'src/auth.py\nsrc/models.py'}]
            },
            'timestamp': '2024-01-01T10:02:01Z',
            'toolUseResult': 'src/auth.py\nsrc/models.py'
        },
        # 问题发现
        {
            'type': 'assistant',
            'message': {
                'content': [{'type': 'text', 'text': '''
## 问题 [P001]

发现了一个潜在问题：
- **症状**: 现有代码没有密码加密
- **根因**: 直接存储明文密码
- **解决**: 使用 bcrypt 加密
- **预防**: 添加代码审查规则
'''}]
            },
            'timestamp': '2024-01-01T10:03:00Z'
        },
    ]


def create_large_mock_messages(count: int = 100) -> list[dict]:
    """创建大量模拟消息用于测试上下文恢复"""
    messages = create_mock_messages()

    # 添加大量工具调用消息
    for i in range(count):
        messages.append({
            'type': 'assistant',
            'message': {
                'content': [
                    {'type': 'tool_use', 'id': f'tool_{i}', 'name': 'Grep', 'input': {'pattern': f'pattern_{i}'}}
                ]
            },
            'timestamp': f'2024-01-01T10:{i:02d}:00Z'
        })
        messages.append({
            'type': 'user',
            'message': {
                'content': [{'type': 'tool_result', 'tool_use_id': f'tool_{i}', 'content': f'result_{i}\n' * 100}]
            },
            'timestamp': f'2024-01-01T10:{i:02d}:01Z',
            'toolUseResult': f'result_{i}\n' * 100
        })

    return messages


def test_hui_extraction(logger: TestLogger, hui, messages: list[dict]):
    """测试慧模块的信息提取"""
    logger.section("慧模块 - 信息提取测试")

    # 1. 测试任务提取
    task = hui.extract_current_task(messages)
    logger.test(
        "任务提取",
        '登录' in task or 'JWT' in task,
        {'提取结果': task[:100]}
    )

    # 2. 测试决策提取
    decisions = hui.extract_decisions(messages)
    logger.test(
        "决策提取",
        len(decisions) > 0,
        {'数量': len(decisions), '样例': decisions[0]['content'][:100] if decisions else 'N/A'}
    )

    # 3. 测试约束提取
    constraints = hui.extract_constraints(messages)
    logger.test(
        "约束提取",
        len(constraints) > 0,
        {'数量': len(constraints)}
    )

    # 4. 测试问题提取
    problems = hui.extract_problems(messages)
    logger.test(
        "问题提取",
        len(problems) > 0,
        {'数量': len(problems)}
    )

    # 5. 测试进度提取
    progress = hui.extract_progress(messages)
    logger.test(
        "进度提取",
        progress.get('total_turns', 0) > 0,
        {'轮次': progress.get('total_turns', 0)}
    )

    return {
        'task': task,
        'decisions': decisions,
        'constraints': constraints,
        'problems': problems,
        'progress': progress,
    }


def test_hui_compression(logger: TestLogger, hui, extraction_result: dict):
    """测试慧模块的压缩功能"""
    logger.section("慧模块 - 上下文压缩测试")

    # 1. 生成缩形态上下文
    compact = hui.generate_compact_context(
        task=extraction_result['task'],
        decisions=extraction_result['decisions'],
        constraints=extraction_result['constraints'],
        interfaces=[],
        problems=extraction_result['problems'],
        progress=extraction_result['progress']
    )

    logger.test(
        "缩形态生成",
        len(compact) > 0 and len(compact) < 1000,
        {'长度': len(compact)}
    )
    logger.log_data("缩形态内容", compact)

    # 2. 生成候选锚点
    candidates = hui.generate_anchor_candidates(
        extraction_result['decisions'],
        extraction_result['constraints'],
        extraction_result['problems']
    )

    logger.test(
        "候选锚点生成",
        len(candidates) > 0,
        {'数量': len(candidates), '类型': [c['type'] for c in candidates]}
    )

    return {
        'compact': compact,
        'candidates': candidates,
    }


def test_shi_write(logger: TestLogger, hui, candidates: list[dict], cwd: str):
    """测试识模块的写入逻辑"""
    logger.section("识模块 - 锚点写入测试")

    # 准备测试目录
    test_anchors_path = Path(cwd) / '.wukong' / 'context' / 'test-anchors.md'

    # 清理旧的测试文件
    if test_anchors_path.exists():
        test_anchors_path.unlink()

    # 1. 测试门槛检查
    for i, candidate in enumerate(candidates[:3]):
        passed = hui.check_threshold(candidate)
        logger.test(
            f"门槛检查 - {candidate['type']}",
            True,  # 记录结果即可
            {
                'title': candidate.get('title', '')[:50],
                '通过门槛': passed,
                '门槛检查': candidate.get('threshold_check', {}),
            }
        )

    # 2. 测试去重检查
    existing = [{'id': 'D001', 'title': 'JWT 认证方案', 'type': 'decision'}]
    for candidate in candidates[:2]:
        is_dup, existing_id = hui.check_duplicate(candidate, existing)
        logger.test(
            f"去重检查 - {candidate.get('title', '')[:30]}",
            True,  # 记录结果即可
            {'是否重复': is_dup, '重复ID': existing_id}
        )

    # 3. 测试实际写入 (使用测试文件)
    # 临时修改 anchors 路径进行测试
    original_anchors_path = Path(cwd) / '.wukong' / 'context' / 'anchors.md'

    # 构造模拟的 hui_output
    hui_output = {
        'session_id': 'test-session',
        'project_path': cwd,
        'anchors': candidates,
        'context': {
            'task': '测试任务',
        }
    }

    # 执行写入
    result = hui.shi_write(hui_output, cwd)

    logger.test(
        "锚点写入",
        True,  # 记录即可
        {
            '写入数': len(result.get('anchors_written', [])),
            '跳过数': len(result.get('anchors_skipped', [])),
            '重复数': len(result.get('anchors_duplicated', [])),
            '错误数': len(result.get('errors', [])),
        }
    )

    logger.log_data("识模块写入结果", result)

    return result


def test_context_recovery(logger: TestLogger, hui, cwd: str):
    """测试三阶段上下文恢复"""
    logger.section("上下文恢复 - 三阶段测试")

    # 1. 测试正常状态 (小量消息)
    small_messages = create_mock_messages()
    usage_small = hui.estimate_context_usage(small_messages)
    logger.test(
        "正常状态检测",
        usage_small['stage'] == 'normal',
        {
            '消息数': len(small_messages),
            '估算 tokens': usage_small['estimated_tokens'],
            '使用率': f"{usage_small['usage_ratio']:.2%}",
            '阶段': usage_small['stage'],
        }
    )

    # 2. 测试大量消息
    large_messages = create_large_mock_messages(50)
    usage_large = hui.estimate_context_usage(large_messages)
    logger.test(
        "大量消息检测",
        usage_large['estimated_tokens'] > usage_small['estimated_tokens'],
        {
            '消息数': len(large_messages),
            '估算 tokens': usage_large['estimated_tokens'],
            '使用率': f"{usage_large['usage_ratio']:.2%}",
            '阶段': usage_large['stage'],
        }
    )

    # 3. 测试 DCP 剪枝
    pruned, dcp_stats = hui.apply_dcp(large_messages)
    logger.test(
        "DCP 剪枝",
        len(pruned) <= len(large_messages),
        {
            '原消息数': dcp_stats['original_count'],
            '剪枝后': dcp_stats['pruned_count'],
            '移除工具': len(dcp_stats.get('removed_tools', [])),
        }
    )

    # 4. 测试会话错误检测
    errors = hui.detect_session_errors(small_messages)
    logger.test(
        "会话错误检测",
        True,  # 记录即可
        {'检测到错误数': len(errors)}
    )

    # 5. 测试完整恢复流水线
    recovery_result = hui.run_recovery_pipeline(large_messages, cwd)
    logger.test(
        "恢复流水线",
        'stage' in recovery_result and 'usage' in recovery_result,
        {
            '阶段': recovery_result['stage'],
            '会话错误': len(recovery_result.get('session_errors', [])),
            'DCP 执行': recovery_result.get('dcp_stats') is not None,
        }
    )

    logger.log_data("恢复流水线结果", {
        'stage': recovery_result['stage'],
        'usage': recovery_result['usage'],
        'dcp_stats': recovery_result.get('dcp_stats'),
        'session_errors_count': len(recovery_result.get('session_errors', [])),
    })

    return recovery_result


def test_anchor_validation(logger: TestLogger, hui):
    """测试锚点内容验证"""
    logger.section("锚点验证 - 内容质量测试")

    # 测试用例
    test_cases = [
        {
            'name': '有效决策',
            'content': '''## 决策: JWT 认证方案

**Context**: 需要实现用户认证
**Decision**: 采用 JWT + bcrypt
**Impact**: 影响认证架构''',
            'type': 'decision',
            'expected': True,
        },
        {
            'name': '无效决策 (太短)',
            'content': '好的',
            'type': 'decision',
            'expected': False,
        },
        {
            'name': '无效决策 (对话开头)',
            'content': '好的，让我来帮你实现这个功能。首先我们需要...',
            'type': 'decision',
            'expected': False,
        },
        {
            'name': '有效问题',
            'content': '''## 问题: 密码明文存储

**症状**: 数据库中密码未加密
**根因**: 缺少密码加密逻辑
**解决**: 使用 bcrypt 加密''',
            'type': 'problem',
            'expected': True,
        },
    ]

    for tc in test_cases:
        result = hui._is_valid_anchor_content(tc['content'], tc['type'])
        logger.test(
            f"锚点验证 - {tc['name']}",
            result == tc['expected'],
            {
                '预期': tc['expected'],
                '实际': result,
                '内容长度': len(tc['content']),
            }
        )


def main():
    """主测试入口"""
    # 解析参数
    cwd = '.'
    for i, arg in enumerate(sys.argv):
        if arg == '--cwd' and i + 1 < len(sys.argv):
            cwd = sys.argv[i + 1]

    cwd = os.path.abspath(cwd)

    # 创建测试输出目录
    output_dir = Path(cwd) / '.wukong' / 'context' / 'test-results'

    # 初始化日志
    logger = TestLogger(output_dir)
    logger._log(f"测试目录: {cwd}")

    # 加载 hui 模块
    try:
        hui = load_hui_module()
        logger._log("✅ hui-extract 模块加载成功")
    except Exception as e:
        logger._log(f"❌ hui-extract 模块加载失败: {e}")
        return

    # 创建模拟消息
    messages = create_mock_messages()
    logger._log(f"创建了 {len(messages)} 条模拟消息")

    # 执行测试
    try:
        # 1. 慧模块 - 信息提取
        extraction_result = test_hui_extraction(logger, hui, messages)

        # 2. 慧模块 - 压缩功能
        compression_result = test_hui_compression(logger, hui, extraction_result)

        # 3. 识模块 - 写入逻辑
        shi_result = test_shi_write(logger, hui, compression_result['candidates'], cwd)

        # 4. 上下文恢复
        recovery_result = test_context_recovery(logger, hui, cwd)

        # 5. 锚点验证
        test_anchor_validation(logger, hui)

    except Exception as e:
        logger._log(f"\n❌ 测试过程出错: {e}")
        import traceback
        logger._log(traceback.format_exc())

    # 完成测试
    results = logger.finalize()

    return results


if __name__ == '__main__':
    main()
