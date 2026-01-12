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
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def read_hook_input() -> dict[str, Any]:
    """从 stdin 读取 hook 输入"""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def read_transcript(transcript_path: str) -> list[dict]:
    """读取对话记录"""
    messages = []
    path = Path(transcript_path)
    if not path.exists():
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
    """生成候选锚点"""
    candidates = []

    # 决策锚点
    for i, d in enumerate(decisions):
        candidates.append({
            'id': f'D_candidate_{i}',
            'type': 'decision',
            'content': d['content'][:200],
            'threshold_check': {
                'frequency': False,  # 需要外部检查
                'impact': True,  # 决策默认有影响
                'reusable': False,  # 需要外部检查
            }
        })

    # 问题锚点
    for i, p in enumerate(problems):
        candidates.append({
            'id': f'P_candidate_{i}',
            'type': 'problem',
            'content': p['content'][:200],
            'threshold_check': {
                'frequency': False,
                'impact': True,
                'reusable': True,  # 问题通常可复用
            }
        })

    return candidates


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
    # 1. 读取 hook 输入
    hook_input = read_hook_input()

    transcript_path = hook_input.get('transcript_path', '')
    session_id = hook_input.get('session_id', 'unknown')
    cwd = hook_input.get('cwd', '.')
    trigger = hook_input.get('trigger', 'unknown')

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

    # 7. 输出给 Claude
    output_to_claude(compact_context, candidates)


if __name__ == '__main__':
    main()
