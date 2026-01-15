#!/usr/bin/env python3
"""
验证 Markdown 文件中的路径引用是否存在对应的源文件

这个测试防止类似 ~/.wukong/skills/ vs ~/.claude/skills/ 的路径错误。
"""
import os
import re
import unittest
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SOURCE_DIR = PROJECT_ROOT / "wukong-dist"

# 路径映射: 文档中的引用路径 -> 源文件目录
PATH_MAPPING = {
    # ~/.claude/ 开头的路径 (正确的安装目标)
    "~/.claude/skills/": SOURCE_DIR / "skills",
    "~/.claude/rules/": SOURCE_DIR / "rules",
    "~/.claude/commands/": SOURCE_DIR / "commands",
    # ~/.wukong/ 开头的路径 (运行时数据)
    "~/.wukong/hooks/": SOURCE_DIR / "hooks",
    "~/.wukong/context/": SOURCE_DIR / "context",
    "~/.wukong/templates/": SOURCE_DIR / "templates",
    "~/.wukong/scheduler/": SOURCE_DIR / "scheduler",
    # 相对路径引用
    ".claude/skills/": SOURCE_DIR / "skills",
    ".claude/rules/": SOURCE_DIR / "rules",
    # 兼容旧路径 (应该被迁移)
    ".wukong/skills/": SOURCE_DIR / "skills",
    "~/.wukong/skills/": SOURCE_DIR / "skills",  # 这是错误路径，但需要检测
}

# 忽略的路径模式 (模板变量等)
IGNORE_PATTERNS = [
    r"\{[^}]+\}",  # {skill_file}.md 等模板变量
    r"\$\{[^}]+\}",  # ${var} 模板变量
    r"<[^>]+>",  # <placeholder> 占位符
]

# 忽略的文件 (测试文件本身、缓存等)
IGNORE_FILES = [
    ".pytest_cache",
    "__pycache__",
    ".git",
    "node_modules",
]


def should_ignore_path(path_ref: str) -> bool:
    """检查路径是否应该被忽略 (模板变量等)"""
    for pattern in IGNORE_PATTERNS:
        if re.search(pattern, path_ref):
            return True
    return False


def find_md_files() -> list:
    """查找所有需要检查的 Markdown 文件"""
    md_files = []
    for md_file in PROJECT_ROOT.glob("**/*.md"):
        # 跳过忽略的目录
        if any(ignore in str(md_file) for ignore in IGNORE_FILES):
            continue
        md_files.append(md_file)
    return md_files


def extract_path_references(content: str) -> list:
    """
    提取文件中的路径引用
    返回: [(路径, 行号), ...]
    """
    refs = []
    lines = content.split('\n')

    # 匹配模式
    patterns = [
        # 反引号中的 .md 或 .py 路径
        r'`(~?/?\.?[a-zA-Z_\-/]+\.(?:md|py))`',
        # Read("path") 或 Read('path') 调用
        r'Read\(["\']([^"\']+\.(?:md|py))["\']',
        # 引用形式 `~/.xxx/yyy/zzz.md`
        r'`(~/\.[a-zA-Z_\-]+/[a-zA-Z_\-/]+\.(?:md|py))`',
    ]

    for line_num, line in enumerate(lines, 1):
        for pattern in patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                if not should_ignore_path(match):
                    refs.append((match, line_num))

    return refs


def resolve_path(ref: str):
    """
    解析引用路径到源文件路径
    返回 None 表示路径不在映射范围内
    """
    for prefix, source_dir in PATH_MAPPING.items():
        if ref.startswith(prefix):
            relative = ref[len(prefix):]
            return source_dir / relative
    return None


def check_file_exists(resolved_path: Path) -> bool:
    """检查文件是否存在 (包括 deprecated 目录)"""
    if resolved_path.exists():
        return True
    # 检查 deprecated 目录
    deprecated_path = resolved_path.parent / "deprecated" / resolved_path.name
    if deprecated_path.exists():
        return True
    return False


class TestPathReferences(unittest.TestCase):
    """路径引用测试"""

    @classmethod
    def setUpClass(cls):
        cls.md_files = find_md_files()

    def test_path_references_exist(self):
        """验证 Markdown 文件中的路径引用对应的源文件存在"""
        all_missing = []

        for md_file in self.md_files:
            content = md_file.read_text(encoding='utf-8')
            refs = extract_path_references(content)

            for ref, line_num in refs:
                resolved = resolve_path(ref)
                if resolved and not check_file_exists(resolved):
                    all_missing.append(
                        f"  {md_file.relative_to(PROJECT_ROOT)}:{line_num}: "
                        f"{ref} -> {resolved}"
                    )

        if all_missing:
            self.fail(
                f"Missing files referenced in markdown files:\n"
                + "\n".join(all_missing)
            )

    def test_no_wrong_skills_path(self):
        """
        确保没有使用错误的 ~/.wukong/skills/ 路径
        正确路径应该是 ~/.claude/skills/

        例外: CLAUDE.md 中的 "Common Pitfalls" 部分故意展示错误路径作为警示
        """
        wrong_pattern = r'~/.wukong/skills/'
        violations = []

        # 允许的例外 (故意展示错误路径的文件)
        allowed_exceptions = {
            "CLAUDE.md": [
                "| `~/.wukong/skills/`",  # 表格中的错误示例
                "Wrong paths like `~/.wukong/skills/`",  # What tests catch 部分
            ],
            "CHANGELOG.md": [
                "from `~/.wukong/skills/`",  # 记录历史修复
                "mv ~/.wukong/skills/",  # 迁移指南命令
                "Skills path changed from `~/.wukong/skills/`",  # 迁移说明
            ],
            "CONTRIBUTING.md": [
                "wrong paths like `~/.wukong/skills/`",  # 说明测试覆盖内容
                "Never use `~/.wukong/skills/`",  # 路径约定警告
            ],
        }

        for md_file in self.md_files:
            content = md_file.read_text(encoding='utf-8')
            lines = content.split('\n')
            file_name = md_file.name

            for line_num, line in enumerate(lines, 1):
                if re.search(wrong_pattern, line):
                    # 检查是否在允许的例外列表中
                    if file_name in allowed_exceptions:
                        is_exception = any(
                            exc in line for exc in allowed_exceptions[file_name]
                        )
                        if is_exception:
                            continue

                    violations.append(
                        f"{md_file.relative_to(PROJECT_ROOT)}:{line_num}: "
                        f"使用了错误路径 ~/.wukong/skills/ (应该是 ~/.claude/skills/)"
                    )

        if violations:
            self.fail(
                "发现错误的 skills 路径引用:\n" + "\n".join(violations)
            )

    def test_path_mapping_consistency(self):
        """验证路径映射目录都存在"""
        for prefix, source_dir in PATH_MAPPING.items():
            if "skills" in prefix or "rules" in prefix or "commands" in prefix:
                # 这些是核心目录，必须存在
                self.assertTrue(
                    source_dir.exists(),
                    f"源目录不存在: {source_dir} (映射自 {prefix})"
                )


if __name__ == "__main__":
    unittest.main()
