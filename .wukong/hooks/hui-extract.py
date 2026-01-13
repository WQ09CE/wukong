#!/usr/bin/env python3
"""
慧 (Hui) - PreCompact Hook 脚本
在 Claude Code 自动压缩上下文前触发，提取并保存关键信息。

使用方法:
1. 将此脚本放到 ~/.wukong/hooks/hui-extract.py
2. 在 .claude/settings.json 中配置:
   {
     "hooks": {
       "PreCompact": [{
         "matcher": "auto",
         "hooks": [{
           "type": "command",
           "command": "python3 ~/.wukong/hooks/hui-extract.py"
         }]
       }]
     }
   }
"""

import json
import os
import sys
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any


# ============================================================
# 分身输出压缩 (Avatar Output Compression)
# ============================================================

# 分身类型对应的压缩配置
AVATAR_COMPRESS_CONFIG = {
    '眼': {'max_files': 20, 'max_summary': 500},
    'explorer': {'max_files': 20, 'max_summary': 500},
    '鼻': {'max_issues': 10, 'max_chars': 800},
    'reviewer': {'max_issues': 10, 'max_chars': 800},
    '斗战胜佛': {'max_chars': 2000, 'keep_diff_only': True},
    'impl': {'max_chars': 2000, 'keep_diff_only': True},
    '身': {'max_chars': 2000, 'keep_diff_only': True},
    'default': {'max_chars': 1000},
}


def compress_avatar_output(output: str, avatar_type: str) -> str:
    """
    根据分身类型压缩输出内容。

    压缩策略:
    - 眼分身: 最多 20 个文件 + 500 字摘要
    - 鼻分身: 最多 10 个 issues
    - 斗战胜佛: 最多 2000 字，只保留 diff 摘要
    - 其他分身: 最多 1000 字

    Args:
        output: 分身的原始输出
        avatar_type: 分身类型 (眼/耳/鼻/舌/身/意 或英文别名)

    Returns:
        压缩后的输出
    """
    config = AVATAR_COMPRESS_CONFIG.get(avatar_type, AVATAR_COMPRESS_CONFIG['default'])

    if avatar_type in ('眼', 'explorer'):
        return _compress_explorer_output(output, config)
    elif avatar_type in ('鼻', 'reviewer'):
        return _compress_reviewer_output(output, config)
    elif avatar_type in ('斗战胜佛', 'impl', '身'):
        return _compress_impl_output(output, config)
    else:
        return _compress_generic_output(output, config)


def _compress_explorer_output(output: str, config: dict) -> str:
    """压缩眼分身输出: 保留文件列表 + 发现摘要"""
    max_files = config.get('max_files', 20)
    max_summary = config.get('max_summary', 500)

    lines = output.split('\n')
    compressed_lines = []

    # 提取文件路径
    file_paths = []
    file_pattern = re.compile(r'^[\s\-\*]*(/[^\s]+|\.{1,2}/[^\s]+|\w+/[^\s]+)')

    for line in lines:
        match = file_pattern.match(line.strip())
        if match:
            file_paths.append(match.group(1))

    # 限制文件数量
    if file_paths:
        compressed_lines.append("### 发现的文件")
        for fp in file_paths[:max_files]:
            compressed_lines.append(f"- {fp}")
        if len(file_paths) > max_files:
            compressed_lines.append(f"- ... 还有 {len(file_paths) - max_files} 个文件")

    # 提取结论/发现部分
    findings = _extract_findings(output)
    if findings:
        compressed_lines.append("")
        compressed_lines.append("### 发现摘要")
        compressed_lines.append(findings[:max_summary])
        if len(findings) > max_summary:
            compressed_lines.append("...")

    return '\n'.join(compressed_lines) if compressed_lines else output[:max_summary]


def _compress_reviewer_output(output: str, config: dict) -> str:
    """压缩鼻分身输出: 保留 issues 列表"""
    max_issues = config.get('max_issues', 10)
    max_chars = config.get('max_chars', 800)

    # 尝试提取 issues
    issues = []
    issue_patterns = [
        r'(?:^|\n)[\s\-\*]*(?:issue|问题|warning|error|bug)[:\s]*(.+?)(?=\n[\s\-\*]*(?:issue|问题|warning|error|bug)|$)',
        r'(?:^|\n)\d+\.\s*(.+?)(?=\n\d+\.|$)',
        r'(?:^|\n)[\-\*]\s*(.+?)(?=\n[\-\*]|$)',
    ]

    for pattern in issue_patterns:
        matches = re.findall(pattern, output, re.IGNORECASE | re.DOTALL)
        if matches:
            issues.extend(matches)
            break

    if issues:
        compressed_lines = ["### 审查问题"]
        for i, issue in enumerate(issues[:max_issues]):
            issue_text = issue.strip()[:150]
            compressed_lines.append(f"{i+1}. {issue_text}")
        if len(issues) > max_issues:
            compressed_lines.append(f"... 还有 {len(issues) - max_issues} 个问题")
        return '\n'.join(compressed_lines)

    # 如果无法提取 issues，直接截断
    return _compress_generic_output(output, config)


def _compress_impl_output(output: str, config: dict) -> str:
    """压缩斗战胜佛输出: 保留 diff 摘要，移除完整代码"""
    max_chars = config.get('max_chars', 2000)

    compressed_parts = []

    # 1. 提取修改摘要
    summary = _extract_change_summary(output)
    if summary:
        compressed_parts.append("### 修改摘要")
        compressed_parts.append(summary)

    # 2. 提取文件变更列表
    files_changed = _extract_files_changed(output)
    if files_changed:
        compressed_parts.append("")
        compressed_parts.append("### 变更文件")
        for f in files_changed[:10]:
            compressed_parts.append(f"- {f}")

    # 3. 提取 diff 概要 (不保留完整代码)
    diff_summary = _extract_diff_summary(output)
    if diff_summary:
        compressed_parts.append("")
        compressed_parts.append("### Diff 概要")
        compressed_parts.append(diff_summary[:800])

    # 4. 提取构建/测试结果
    test_result = _extract_test_result(output)
    if test_result:
        compressed_parts.append("")
        compressed_parts.append("### 验证结果")
        compressed_parts.append(test_result)

    result = '\n'.join(compressed_parts)
    return result[:max_chars] if result else output[:max_chars]


def _compress_generic_output(output: str, config: dict) -> str:
    """通用压缩: 提取结论，限制字数"""
    max_chars = config.get('max_chars', 1000)

    # 尝试提取结论部分
    conclusion = _extract_conclusion(output)
    if conclusion:
        return conclusion[:max_chars]

    # 直接截断
    if len(output) > max_chars:
        return output[:max_chars] + "\n... [已截断]"
    return output


def _extract_findings(text: str) -> str:
    """提取探索发现"""
    patterns = [
        r'(?:发现|findings?|结论|conclusion)[:\s]*(.+?)(?=\n\n|\Z)',
        r'(?:总结|summary)[:\s]*(.+?)(?=\n\n|\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

    return ""


def _extract_change_summary(text: str) -> str:
    """提取修改摘要"""
    patterns = [
        r'(?:修改摘要|changes?|summary)[:\s]*(.+?)(?=\n\n|\n###|\Z)',
        r'(?:完成|done|finished)[:\s]*(.+?)(?=\n\n|\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()[:500]

    return ""


def _extract_files_changed(text: str) -> list[str]:
    """提取变更的文件列表"""
    files = []

    # 匹配常见的文件路径模式
    file_patterns = [
        r'(?:modified|changed|created|deleted|edited)[:\s]*([^\n]+\.(?:py|js|ts|md|json|yaml|yml|toml))',
        r'(?:files?_changed|变更文件)[:\s\[]*([^\]]+)',
        r'(?:^|\n)[\s\-\*]+(/[^\s]+\.[a-z]+)',
    ]

    for pattern in file_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        files.extend(matches)

    # 去重
    return list(dict.fromkeys(files))


def _extract_diff_summary(text: str) -> str:
    """提取 diff 概要，移除完整代码块"""
    # 移除代码块
    text_no_code = re.sub(r'```[\s\S]*?```', '[代码块已省略]', text)

    # 提取 +/- 行的统计
    plus_lines = len(re.findall(r'^\+[^+]', text, re.MULTILINE))
    minus_lines = len(re.findall(r'^-[^-]', text, re.MULTILINE))

    summary_parts = []
    if plus_lines or minus_lines:
        summary_parts.append(f"+{plus_lines} -{minus_lines} 行变更")

    # 提取函数/类变更
    func_changes = re.findall(r'(?:def|class|function)\s+(\w+)', text_no_code)
    if func_changes:
        summary_parts.append(f"涉及: {', '.join(set(func_changes)[:5])}")

    return ' | '.join(summary_parts) if summary_parts else ""


def _extract_test_result(text: str) -> str:
    """提取测试/构建结果"""
    patterns = [
        r'((?:tests?\s+)?(?:passed|failed|success|error)[^\n]*)',
        r'((?:build|构建)\s*(?:成功|失败|passed|failed)[^\n]*)',
        r'(✓|✗|PASS|FAIL)[^\n]*',
    ]

    results = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        results.extend(matches[:3])

    return ' | '.join(results) if results else ""


def _extract_conclusion(text: str) -> str:
    """提取结论部分"""
    patterns = [
        r'(?:结论|conclusion|总结|summary|结果|result)[:\s]*(.+?)(?=\n\n|\Z)',
        r'(?:完成|done|完毕)[:\s]*(.+?)(?=\n\n|\Z)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

    return ""


def compress_avatar_output_from_env(output: str) -> str:
    """
    从环境变量读取分身类型并压缩输出。

    环境变量:
    - WUKONG_COMPRESS_AVATAR: 设为 1 启用压缩
    - WUKONG_AVATAR_TYPE: 分身类型
    """
    if os.environ.get('WUKONG_COMPRESS_AVATAR') != '1':
        return output

    avatar_type = os.environ.get('WUKONG_AVATAR_TYPE', 'default')
    return compress_avatar_output(output, avatar_type)


def read_hook_input() -> dict[str, Any]:
    """从 stdin 读取 hook 输入"""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def read_transcript(transcript_path: str) -> list[dict]:
    """读取对话记录"""
    messages = []
    if not transcript_path:
        return messages

    path = Path(transcript_path).expanduser()
    if not path.exists() or not path.is_file():
        return messages

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return messages


def extract_decisions(messages: list[dict]) -> list[dict]:
    """提取决策信息"""
    decisions = []
    decision_patterns = [
        r'\[D\d+\]',  # [D001] 格式的决策引用
        r'决定|决策|选择|采用|使用',  # 决策关键词
        r'Decision|Decided|Choose|Use',
    ]

    for msg in messages:
        content = get_message_content(msg)
        for pattern in decision_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                # 提取包含决策的段落
                decisions.append({
                    'type': 'decision',
                    'content': content[:500],  # 限制长度
                    'timestamp': msg.get('timestamp', '')
                })
                break

    return decisions[-5:]  # 只保留最近5个


def extract_constraints(messages: list[dict]) -> list[dict]:
    """提取约束信息"""
    constraints = []
    constraint_patterns = [
        r'\[C\d+\]',  # [C001] 格式的约束引用
        r'必须|禁止|不能|不允许|约束|限制',
        r'MUST|NEVER|ALWAYS|constraint',
    ]

    for msg in messages:
        content = get_message_content(msg)
        for pattern in constraint_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                constraints.append({
                    'type': 'constraint',
                    'content': content[:300],
                    'timestamp': msg.get('timestamp', '')
                })
                break

    return constraints[-3:]


def extract_interfaces(messages: list[dict]) -> list[dict]:
    """提取接口定义"""
    interfaces = []
    interface_patterns = [
        r'\[I\d+\]',  # [I001] 格式的接口引用
        r'def \w+\(.*\)',  # Python 函数定义
        r'class \w+',  # 类定义
        r'interface|API|endpoint',
    ]

    for msg in messages:
        content = get_message_content(msg)
        for pattern in interface_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                interfaces.append({
                    'type': 'interface',
                    'content': content[:400],
                    'timestamp': msg.get('timestamp', '')
                })
                break

    return interfaces[-3:]


def extract_problems(messages: list[dict]) -> list[dict]:
    """提取问题/陷阱"""
    problems = []
    problem_patterns = [
        r'\[P\d+\]',  # [P001] 格式的问题引用
        r'问题|bug|错误|失败|警告',
        r'error|fail|warning|issue|problem',
    ]

    for msg in messages:
        content = get_message_content(msg)
        for pattern in problem_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                problems.append({
                    'type': 'problem',
                    'content': content[:300],
                    'timestamp': msg.get('timestamp', '')
                })
                break

    return problems[-3:]


def get_message_content(msg: dict) -> str:
    """获取消息内容"""
    if 'message' in msg and 'content' in msg['message']:
        content = msg['message']['content']
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            return ' '.join(
                item.get('text', '')
                for item in content
                if isinstance(item, dict) and item.get('type') == 'text'
            )
    return ''


def extract_current_task(messages: list[dict]) -> str:
    """提取当前任务描述"""
    # 查找用户的初始请求
    for msg in messages[:5]:  # 只看前几条
        if msg.get('type') == 'user':
            content = get_message_content(msg)
            if content:
                return content[:200]
    return "未知任务"


def extract_progress(messages: list[dict]) -> dict:
    """提取进度信息"""
    # 简单统计
    total_messages = len(messages)
    user_messages = sum(1 for m in messages if m.get('type') == 'user')
    assistant_messages = sum(1 for m in messages if m.get('type') == 'assistant')

    return {
        'total_turns': total_messages // 2,
        'user_messages': user_messages,
        'assistant_messages': assistant_messages,
    }


def generate_compact_context(
    task: str,
    decisions: list[dict],
    constraints: list[dict],
    interfaces: list[dict],
    problems: list[dict],
    progress: dict
) -> str:
    """生成缩形态上下文"""
    lines = [
        "## 🔸 缩形态上下文",
        "",
        f"【任务】{task}",
        "",
        "【已决策】",
    ]

    if decisions:
        for d in decisions[:3]:
            content = d['content'][:100].replace('\n', ' ')
            lines.append(f"- {content}...")
    else:
        lines.append("- (暂无)")

    lines.extend([
        "",
        "【约束】",
    ])

    if constraints:
        for c in constraints[:2]:
            content = c['content'][:80].replace('\n', ' ')
            lines.append(f"- {content}...")
    else:
        lines.append("- (暂无)")

    lines.extend([
        "",
        "【当前进度】",
        f"- 对话轮次: {progress.get('total_turns', 0)}",
    ])

    if problems:
        lines.extend([
            "",
            "【注意事项】",
        ])
        for p in problems[:2]:
            content = p['content'][:60].replace('\n', ' ')
            lines.append(f"- {content}...")

    lines.extend([
        "",
        f"【生成时间】{datetime.now().isoformat()}",
    ])

    return '\n'.join(lines)


def generate_anchor_candidates(
    decisions: list[dict],
    constraints: list[dict],
    problems: list[dict]
) -> list[dict]:
    """生成候选锚点（带内容验证）"""
    candidates = []

    # 决策锚点
    for i, d in enumerate(decisions):
        content = d['content']
        if not _is_valid_anchor_content(content, 'decision'):
            continue
        candidates.append({
            'id': f'D_candidate_{i}',
            'type': 'decision',
            'title': _extract_title(content, 'decision'),
            'content': content[:300],
            'threshold_check': {
                'frequency': 1,
                'impact': _detect_impact(content),
                'reusable': _detect_reusable(content, 'decision'),
            }
        })

    # 问题锚点
    for i, p in enumerate(problems):
        content = p['content']
        if not _is_valid_anchor_content(content, 'problem'):
            continue
        candidates.append({
            'id': f'P_candidate_{i}',
            'type': 'problem',
            'title': _extract_title(content, 'problem'),
            'content': content[:300],
            'threshold_check': {
                'frequency': 1,
                'impact': _detect_impact(content),
                'reusable': _detect_reusable(content, 'problem'),
            }
        })

    # 约束锚点
    for i, c in enumerate(constraints):
        content = c['content']
        if not _is_valid_anchor_content(content, 'constraint'):
            continue
        candidates.append({
            'id': f'C_candidate_{i}',
            'type': 'constraint',
            'title': _extract_title(content, 'constraint'),
            'content': content[:300],
            'threshold_check': {
                'frequency': 1,
                'impact': _detect_impact(content),
                'reusable': _detect_reusable(content, 'constraint'),
            }
        })

    return candidates


def _extract_title(content: str, anchor_type: str) -> str:
    """从内容中提取标题"""
    lines = content.split('\n')

    # 1. 优先查找 markdown 标题格式
    for line in lines[:5]:
        line = line.strip()
        md_title = re.match(r'^#{1,3}\s+(.+)$', line)
        if md_title:
            title = md_title.group(1).strip()
            return title[:50] if len(title) <= 50 else title[:47] + '...'

        bold_title = re.match(r'^\*\*(.+?)\*\*', line)
        if bold_title:
            title = bold_title.group(1).strip()
            return title[:50] if len(title) <= 50 else title[:47] + '...'

    # 2. 排除对话开头，找第一个有意义的行
    skip_prefixes = (
        '完成', '好的', '好，', '是的', '没问题', '已', '我',
        'Done', 'OK', 'Yes', 'I\'ll', 'I will', 'Let me', 'You are',
        'This', 'The ', 'Here', '```',
    )

    for line in lines[:10]:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        if any(line.startswith(p) for p in skip_prefixes):
            continue
        line = re.sub(r'^[\-\*\d\.]+\s*', '', line)
        return line[:50] if len(line) <= 50 else line[:47] + '...'

    return f'{anchor_type}_untitled'


# ============================================================
# 锚点内容验证 (Anchor Content Validation)
# ============================================================

CONVERSATION_PREFIXES = (
    '完成', '好的', '好，', '是的', '没问题', '已经', '我来', '我会', '让我',
    '现在', '接下来', '首先', '然后', '最后', '总结',
    'Done', 'OK', 'Yes', 'I\'ll', 'I will', 'I\'m', 'Let me', 'Now',
    'You are', 'This command', 'Here is', 'Here are', '```',
)

ANCHOR_STRUCTURE_KEYWORDS = {
    'decision': ['context', 'decision', 'impact', 'evidence', '背景', '决策', '影响', '原因'],
    'problem': ['症状', '根因', '解决', '预防', 'symptom', 'root cause', 'solution', 'prevention'],
    'constraint': ['约束', '必须', '禁止', 'must', 'never', 'always', 'constraint'],
}

IMPACT_KEYWORDS = [
    '架构', '安全', '性能', '多模块', '全局', '核心', '关键',
    'architecture', 'security', 'performance', 'global', 'core', 'critical',
]


def _is_valid_anchor_content(content: str, anchor_type: str) -> bool:
    """验证内容是否适合作为锚点"""
    if not content or len(content.strip()) < 50:
        return False

    first_line = content.strip().split('\n')[0].strip()
    if any(first_line.startswith(p) for p in CONVERSATION_PREFIXES):
        return False

    keywords = ANCHOR_STRUCTURE_KEYWORDS.get(anchor_type, [])
    if keywords:
        content_lower = content.lower()
        if not any(kw.lower() in content_lower for kw in keywords):
            return False

    return True


def _detect_impact(content: str) -> bool:
    """检测内容是否涉及重大影响"""
    content_lower = content.lower()
    return any(kw.lower() in content_lower for kw in IMPACT_KEYWORDS)


def _detect_reusable(content: str, anchor_type: str) -> bool:
    """检测内容是否可复用"""
    if anchor_type == 'problem':
        return True
    reusable_keywords = ['模式', '通用', '最佳实践', 'pattern', 'generic', 'best practice']
    return any(kw.lower() in content.lower() for kw in reusable_keywords)


# ============================================================
# 慧→识 交接协议 (Hui -> Shi Handoff Protocol)
# ============================================================

def generate_hui_output(
    session_id: str,
    project_path: str,
    task: str,
    decisions: list[dict],
    constraints: list[dict],
    interfaces: list[dict],
    problems: list[dict],
    progress: dict,
    compact_context: str,
    candidates: list[dict]
) -> dict:
    """
    生成慧模块的标准化输出（JSON 格式）。

    这是慧→识的交接协议，定义了两个模块之间的数据契约。

    Args:
        session_id: 会话ID
        project_path: 项目路径
        task: 当前任务描述
        decisions: 决策列表
        constraints: 约束列表
        interfaces: 接口列表
        problems: 问题列表
        progress: 进度信息
        compact_context: 缩形态上下文 (markdown)
        candidates: 候选锚点列表

    Returns:
        标准化的慧模块输出 (dict)
    """
    return {
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "project_path": project_path,

        "context": {
            "task": task,
            "decisions": decisions,
            "constraints": constraints,
            "interfaces": interfaces,
            "problems": problems,
            "progress": progress,
            "compact_md": compact_context,
        },

        "anchors": candidates,  # 候选锚点列表
    }


# ============================================================
# 识模块 - 写入逻辑 (Shi Module - Write Logic)
# ============================================================

def check_threshold(anchor: dict) -> bool:
    """
    检查锚点是否通过写入门槛（严格版）。

    门槛条件 (至少满足一项):
    - frequency >= 2: 类似问题/决策出现两次以上
    - impact = True AND 内容长度 >= 100
    - reusable = True AND anchor_type == 'problem' AND 有解决方案

    Args:
        anchor: 锚点字典，包含 threshold_check 字段

    Returns:
        bool: 是否通过门槛
    """
    threshold = anchor.get('threshold_check', {})
    anchor_type = anchor.get('type', '')
    content = anchor.get('content', '')

    # 1. 频率检查 (最可靠)
    frequency = threshold.get('frequency', 0)
    if isinstance(frequency, int) and frequency >= 2:
        return True

    # 2. 影响检查 (需配合内容长度)
    if threshold.get('impact', False) and len(content) >= 100:
        return True

    # 3. 可复用检查 (只对 problem 类型 + 有解决方案生效)
    if threshold.get('reusable', False) and anchor_type == 'problem':
        content_lower = content.lower()
        has_solution = any(kw in content_lower for kw in ['解决', '修复', '预防', 'fix', 'solution', 'resolve'])
        if has_solution:
            return True

    return False


def check_duplicate(anchor: dict, existing_anchors: list[dict]) -> tuple[bool, str | None]:
    """
    检查锚点是否与现有锚点重复。

    使用简单的标题相似度检查:
    - 标题完全相同 -> 重复
    - 标题词汇重叠 > 70% -> 重复

    Args:
        anchor: 待检查的锚点
        existing_anchors: 现有锚点列表

    Returns:
        (is_duplicate, existing_id): 是否重复及重复锚点的ID
    """
    new_title = anchor.get('title', '').lower()
    new_words = set(re.findall(r'\w+', new_title))

    if not new_words:
        return False, None

    for existing in existing_anchors:
        existing_title = existing.get('title', '').lower()
        existing_words = set(re.findall(r'\w+', existing_title))

        if not existing_words:
            continue

        # 完全相同
        if new_title == existing_title:
            return True, existing.get('id')

        # 词汇重叠检查
        intersection = new_words & existing_words
        union = new_words | existing_words

        if union and len(intersection) / len(union) > 0.7:
            return True, existing.get('id')

    return False, None


def _get_next_anchor_id(anchor_type: str, existing_anchors: list[dict]) -> str:
    """
    获取下一个可用的锚点ID。

    ID格式: {type_prefix}{3位数字}
    - 决策: D001, D002, ...
    - 问题: P001, P002, ...
    - 约束: C001, C002, ...
    - 接口: I001, I002, ...

    Args:
        anchor_type: 锚点类型 (decision, problem, constraint, interface)
        existing_anchors: 现有锚点列表

    Returns:
        新的锚点ID
    """
    type_prefix_map = {
        'decision': 'D',
        'problem': 'P',
        'constraint': 'C',
        'interface': 'I',
    }
    prefix = type_prefix_map.get(anchor_type, 'A')

    # 找出同类型的最大ID
    max_num = 0
    pattern = re.compile(rf'^{prefix}(\d+)$')

    for anchor in existing_anchors:
        anchor_id = anchor.get('id', '')
        match = pattern.match(anchor_id)
        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)

    return f'{prefix}{max_num + 1:03d}'


def _load_existing_anchors(anchors_path: Path) -> list[dict]:
    """
    从 anchors.md 文件加载现有锚点。

    解析格式:
    ## [D001] 决策标题
    内容...

    Args:
        anchors_path: anchors.md 文件路径

    Returns:
        锚点列表
    """
    if not anchors_path.exists():
        return []

    anchors = []
    content = anchors_path.read_text(encoding='utf-8')

    # 匹配 ## [ID] 标题 格式
    anchor_pattern = re.compile(
        r'^## \[([A-Z]\d+)\] (.+?)$\n(.*?)(?=^## \[|$)',
        re.MULTILINE | re.DOTALL
    )

    for match in anchor_pattern.finditer(content):
        anchor_id = match.group(1)
        title = match.group(2).strip()
        body = match.group(3).strip()

        # 推断类型
        anchor_type = 'unknown'
        if anchor_id.startswith('D'):
            anchor_type = 'decision'
        elif anchor_id.startswith('P'):
            anchor_type = 'problem'
        elif anchor_id.startswith('C'):
            anchor_type = 'constraint'
        elif anchor_id.startswith('I'):
            anchor_type = 'interface'

        anchors.append({
            'id': anchor_id,
            'type': anchor_type,
            'title': title,
            'content': body,
        })

    return anchors


def write_to_anchors(anchor: dict, anchors_path: Path) -> str:
    """
    将锚点追加到 anchors.md 文件。

    Args:
        anchor: 锚点字典
        anchors_path: anchors.md 文件路径

    Returns:
        新分配的锚点ID
    """
    # 确保目录存在
    anchors_path.parent.mkdir(parents=True, exist_ok=True)

    # 加载现有锚点
    existing_anchors = _load_existing_anchors(anchors_path)

    # 分配新ID
    new_id = _get_next_anchor_id(anchor.get('type', 'unknown'), existing_anchors)

    # 构建锚点内容
    title = anchor.get('title', 'Untitled')
    content = anchor.get('content', '')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

    anchor_entry = f"""
## [{new_id}] {title}

**创建时间**: {timestamp}
**类型**: {anchor.get('type', 'unknown')}

{content}

---
"""

    # 如果文件不存在，创建头部
    if not anchors_path.exists():
        header = """# 锚点记录 (Anchors)

> 此文件由识模块自动维护，记录跨会话的重要决策、问题和约束。

"""
        with open(anchors_path, 'w', encoding='utf-8') as f:
            f.write(header)

    # 追加锚点
    with open(anchors_path, 'a', encoding='utf-8') as f:
        f.write(anchor_entry)

    return new_id


def _get_project_hash(project_path: str) -> str:
    """计算项目路径的哈希值（用于索引）"""
    return hashlib.md5(project_path.encode()).hexdigest()[:8]


def _get_project_name(project_path: str) -> str:
    """从项目路径提取项目名"""
    return Path(project_path).name or 'unknown'


def update_session_index(session_info: dict, index_path: Path):
    """
    更新会话索引文件 (index.json)。

    索引结构:
    {
        "version": "1.0",
        "sessions": [...],
        "projects": {...}
    }

    Args:
        session_info: 会话信息字典
        index_path: index.json 文件路径
    """
    # 确保目录存在
    index_path.parent.mkdir(parents=True, exist_ok=True)

    # 加载现有索引
    index = {
        "version": "1.0",
        "sessions": [],
        "projects": {}
    }

    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # 确保结构完整
    if "sessions" not in index:
        index["sessions"] = []
    if "projects" not in index:
        index["projects"] = {}

    session_id = session_info.get('session_id', 'unknown')
    project_path = session_info.get('project_path', '.')
    project_hash = _get_project_hash(project_path)
    project_name = _get_project_name(project_path)
    now = datetime.now().isoformat()

    # 查找是否已存在该会话
    existing_session = None
    for i, s in enumerate(index["sessions"]):
        if s.get('session_id') == session_id:
            existing_session = i
            break

    session_entry = {
        "session_id": session_id,
        "project_path": project_path,
        "project_hash": project_hash,
        "created_at": session_info.get('created_at', now),
        "updated_at": now,
        "task_summary": session_info.get('task_summary', '')[:200],
        "anchor_count": session_info.get('anchor_count', 0),
        "status": session_info.get('status', 'active')
    }

    if existing_session is not None:
        # 更新现有会话
        session_entry["created_at"] = index["sessions"][existing_session].get('created_at', now)
        index["sessions"][existing_session] = session_entry
    else:
        # 添加新会话
        index["sessions"].append(session_entry)

    # 更新项目信息
    if project_hash not in index["projects"]:
        index["projects"][project_hash] = {
            "path": project_path,
            "name": project_name,
            "session_count": 0
        }

    # 统计该项目的会话数
    project_sessions = sum(
        1 for s in index["sessions"]
        if s.get('project_hash') == project_hash
    )
    index["projects"][project_hash]["session_count"] = project_sessions

    # 保存索引
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def shi_write(hui_output: dict, cwd: str) -> dict:
    """
    识模块的主写入函数。

    接收慧模块的 JSON 输出，执行:
    1. 门槛检查
    2. 去重检查
    3. 写入通过的锚点
    4. 更新索引

    Args:
        hui_output: 慧模块的标准化输出
        cwd: 当前工作目录

    Returns:
        写入结果摘要
    """
    result = {
        "anchors_written": [],
        "anchors_skipped": [],
        "anchors_duplicated": [],
        "errors": []
    }

    # 准备路径
    wukong_dir = Path(cwd) / '.wukong'
    anchors_path = wukong_dir / 'context' / 'anchors.md'
    index_path = wukong_dir / 'context' / 'index.json'

    # 加载现有锚点
    existing_anchors = _load_existing_anchors(anchors_path)

    # 处理候选锚点
    candidates = hui_output.get('anchors', [])

    for candidate in candidates:
        try:
            # 1. 门槛检查
            if not check_threshold(candidate):
                result["anchors_skipped"].append({
                    "id": candidate.get('id'),
                    "reason": "threshold_not_met"
                })
                continue

            # 2. 去重检查
            is_dup, existing_id = check_duplicate(candidate, existing_anchors)
            if is_dup:
                result["anchors_duplicated"].append({
                    "id": candidate.get('id'),
                    "existing_id": existing_id
                })
                continue

            # 3. 写入锚点
            new_id = write_to_anchors(candidate, anchors_path)
            result["anchors_written"].append({
                "candidate_id": candidate.get('id'),
                "new_id": new_id,
                "type": candidate.get('type'),
                "title": candidate.get('title')
            })

            # 更新现有锚点列表（用于后续去重）
            existing_anchors.append({
                'id': new_id,
                'type': candidate.get('type'),
                'title': candidate.get('title'),
                'content': candidate.get('content')
            })

        except Exception as e:
            result["errors"].append({
                "id": candidate.get('id'),
                "error": str(e)
            })

    # 4. 更新会话索引
    try:
        session_info = {
            "session_id": hui_output.get('session_id', 'unknown'),
            "project_path": hui_output.get('project_path', cwd),
            "task_summary": hui_output.get('context', {}).get('task', ''),
            "anchor_count": len(result["anchors_written"]),
            "status": "active"
        }
        update_session_index(session_info, index_path)
    except Exception as e:
        result["errors"].append({
            "id": "session_index",
            "error": str(e)
        })

    return result


def save_context(cwd: str, compact_context: str, session_id: str):
    """保存上下文到文件"""
    context_dir = Path(cwd) / '.wukong' / 'context' / 'current'
    context_dir.mkdir(parents=True, exist_ok=True)

    compact_path = context_dir / 'compact.md'
    with open(compact_path, 'w', encoding='utf-8') as f:
        f.write(compact_context)

    # 同时保存一个带时间戳的备份
    sessions_dir = Path(cwd) / '.wukong' / 'context' / 'sessions'
    sessions_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    session_dir = sessions_dir / f'{timestamp}-{session_id[:8]}'
    session_dir.mkdir(parents=True, exist_ok=True)

    backup_path = session_dir / 'compact.md'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(compact_context)


def output_to_claude(compact_context: str, candidates: list[dict]):
    """输出给 Claude (会被注入到压缩后的上下文)"""
    print("## [慧] PreCompact 提取完成")
    print()
    print("已保存关键上下文到 `.wukong/context/current/compact.md`")
    print()
    if candidates:
        print(f"识别到 {len(candidates)} 个候选锚点，待后续门槛检查。")
    print()
    print("如需恢复详细信息，读取 `.wukong/context/sessions/` 下对应文件。")


def main():
    """
    主入口函数。

    支持两种模式:
    1. PreCompact Hook 模式: 从 stdin 读取 hook 输入，提取上下文
    2. 分身输出压缩模式: 通过环境变量 WUKONG_COMPRESS_AVATAR=1 触发

    环境变量:
    - WUKONG_COMPRESS_AVATAR: 设为 1 启用分身输出压缩模式
    - WUKONG_AVATAR_TYPE: 分身类型 (眼/耳/鼻/舌/身/意 或英文别名)
    - WUKONG_AVATAR_OUTPUT: 要压缩的输出内容 (或从 stdin 读取)
    """
    # 检查是否为分身输出压缩模式
    if os.environ.get('WUKONG_COMPRESS_AVATAR') == '1':
        _run_avatar_compress_mode()
        return

    # 原有的 PreCompact Hook 模式
    _run_precompact_mode()


def _run_avatar_compress_mode():
    """分身输出压缩模式"""
    avatar_type = os.environ.get('WUKONG_AVATAR_TYPE', 'default')

    # 从环境变量或 stdin 读取输出内容
    avatar_output = os.environ.get('WUKONG_AVATAR_OUTPUT', '')
    if not avatar_output:
        avatar_output = sys.stdin.read()

    if not avatar_output:
        print("## [慧] 无分身输出可压缩", file=sys.stderr)
        return

    # 压缩输出
    compressed = compress_avatar_output(avatar_output, avatar_type)

    # 输出压缩结果
    print(compressed)

    # 记录日志
    log_path = Path.home() / '.wukong' / 'hooks' / 'hui-compress.log'
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"\n--- {datetime.now().isoformat()} ---\n")
        log.write(f"Avatar: {avatar_type}\n")
        log.write(f"Original: {len(avatar_output)} chars\n")
        log.write(f"Compressed: {len(compressed)} chars\n")
        log.write(f"Ratio: {len(compressed)/len(avatar_output)*100:.1f}%\n")


def _run_precompact_mode():
    """PreCompact Hook 模式"""
    # 1. 读取 hook 输入
    hook_input = read_hook_input()

    # Debug: 记录到日志文件
    log_path = Path.home() / '.wukong' / 'hooks' / 'hui-extract.log'
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"\n--- {datetime.now().isoformat()} ---\n")
        log.write(f"Input keys: {list(hook_input.keys())}\n")
        log.write(f"Full input: {json.dumps(hook_input, ensure_ascii=False)[:500]}\n")

    print(f"## [慧] Hook 触发 - 输入: {list(hook_input.keys())}", file=sys.stderr)

    transcript_path = hook_input.get('transcript_path', '')
    session_id = hook_input.get('session_id', 'unknown')
    cwd = hook_input.get('cwd', '.')
    trigger = hook_input.get('trigger', 'unknown')

    print(f"## [慧] trigger={trigger}, session={session_id[:8] if session_id else 'none'}", file=sys.stderr)

    # 2. 读取对话记录
    messages = read_transcript(transcript_path)

    if not messages:
        print("## [慧] 无对话记录可提取")
        return

    # 3. 提取关键信息
    task = extract_current_task(messages)
    decisions = extract_decisions(messages)
    constraints = extract_constraints(messages)
    interfaces = extract_interfaces(messages)
    problems = extract_problems(messages)
    progress = extract_progress(messages)

    # 4. 生成缩形态上下文
    compact_context = generate_compact_context(
        task=task,
        decisions=decisions,
        constraints=constraints,
        interfaces=interfaces,
        problems=problems,
        progress=progress
    )

    # 5. 生成候选锚点
    candidates = generate_anchor_candidates(decisions, constraints, problems)

    # 6. 保存到文件
    save_context(cwd, compact_context, session_id)

    # 7. 生成慧模块标准输出 (慧→识交接协议)
    hui_output = generate_hui_output(
        session_id=session_id,
        project_path=cwd,
        task=task,
        decisions=decisions,
        constraints=constraints,
        interfaces=interfaces,
        problems=problems,
        progress=progress,
        compact_context=compact_context,
        candidates=candidates
    )

    # 8. 保存慧输出 JSON (供调试和识模块使用)
    sessions_dir = Path(cwd) / '.wukong' / 'context' / 'sessions'
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    session_dir = sessions_dir / f'{timestamp}-{session_id[:8]}'
    session_dir.mkdir(parents=True, exist_ok=True)

    hui_output_path = session_dir / 'hui-output.json'
    with open(hui_output_path, 'w', encoding='utf-8') as f:
        json.dump(hui_output, f, ensure_ascii=False, indent=2)

    # 9. 调用识模块写入
    shi_result = shi_write(hui_output, cwd)

    # 记录识模块结果
    shi_result_path = session_dir / 'shi-result.json'
    with open(shi_result_path, 'w', encoding='utf-8') as f:
        json.dump(shi_result, f, ensure_ascii=False, indent=2)

    # 记录日志
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"Shi result: written={len(shi_result['anchors_written'])}, ")
        log.write(f"skipped={len(shi_result['anchors_skipped'])}, ")
        log.write(f"duplicated={len(shi_result['anchors_duplicated'])}\n")

    # 10. 输出给 Claude
    output_to_claude_with_shi_result(compact_context, candidates, shi_result)


def output_to_claude_with_shi_result(
    compact_context: str,
    candidates: list[dict],
    shi_result: dict
):
    """输出给 Claude，包含识模块的写入结果"""
    print("## [慧] PreCompact 提取完成")
    print()
    print("已保存关键上下文到 `.wukong/context/current/compact.md`")
    print()

    if candidates:
        print(f"识别到 {len(candidates)} 个候选锚点。")

    # 显示识模块写入结果
    written = shi_result.get('anchors_written', [])
    skipped = shi_result.get('anchors_skipped', [])
    duplicated = shi_result.get('anchors_duplicated', [])

    if written:
        print(f"\n### [识] 已写入 {len(written)} 个锚点:")
        for w in written[:5]:  # 最多显示5个
            print(f"  - [{w['new_id']}] {w.get('title', '')[:40]}")

    if skipped:
        print(f"\n### [识] 跳过 {len(skipped)} 个锚点 (未达门槛)")

    if duplicated:
        print(f"\n### [识] 去重 {len(duplicated)} 个锚点 (已存在)")

    errors = shi_result.get('errors', [])
    if errors:
        print(f"\n### [识] 错误: {len(errors)} 个")
        for e in errors[:3]:
            print(f"  - {e.get('id')}: {e.get('error')}")

    print()
    print("如需恢复详细信息，读取 `.wukong/context/sessions/` 下对应文件。")


if __name__ == '__main__':
    main()
