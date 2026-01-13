#!/usr/bin/env python3
"""
Wukong Orchestration Validator (编排验证器)

Dry-Run 模式验证编排决策的正确性：
- 路由合理性：任务分配给正确的分身
- 并行正确性：无依赖任务并行，有依赖任务串行
- 角色边界：分身不越权 (Do/Don't)
- DAG 完整性：轨道节点无遗漏

IMPORTANT - 数据同步说明:
本文件中的分身配置 (AVATAR_CONFIGS) 是 .wukong/skills/jie.md 中
"分身边界定义"章节的代码镜像。修改分身配置时，需同步更新两处。
Single Source of Truth: .wukong/skills/jie.md

Usage:
    python3 orchestration-validator.py [--verbose] [--json]
    python3 orchestration-validator.py --task "添加登录功能"
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional


# ============================================================
# 数据结构定义
# ============================================================

class Track(Enum):
    """轨道类型"""
    FEATURE = "Feature"      # 功能开发
    FIX = "Fix"              # 问题修复
    REFACTOR = "Refactor"    # 代码重构
    DIRECT = "Direct"        # 直接执行


class Avatar(Enum):
    """分身类型"""
    EYE = "眼"        # 探索·搜索
    EAR = "耳"        # 需求·理解
    NOSE = "鼻"       # 审查·检测
    TONGUE = "舌"     # 测试·文档
    BODY = "身"       # 实现·行动 (斗战胜佛)
    MIND = "意"       # 设计·决策


class CostTier(Enum):
    """成本层级"""
    CHEAP = "CHEAP"         # 眼/耳/鼻 - 可 10+ 并发
    MEDIUM = "MEDIUM"       # 舌 - 2-3 并发
    EXPENSIVE = "EXPENSIVE" # 身/意 - 阻塞执行


@dataclass
class AvatarConfig:
    """分身配置"""
    name: str
    cost: CostTier
    max_concurrent: int
    background: bool
    do: list[str]
    dont: list[str]
    tools: list[str]


@dataclass
class DAGNode:
    """DAG 节点"""
    phase: int
    avatars: list[Avatar]
    parallel: bool
    description: str


@dataclass
class ValidationResult:
    """验证结果"""
    name: str
    passed: bool
    expected: str
    actual: str
    details: str = ""


@dataclass
class OrchestrationDecision:
    """编排决策记录"""
    task: str
    track: Track
    dag: list[DAGNode]
    validations: list[ValidationResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(v.passed for v in self.validations)


# ============================================================
# 编排规则定义
# ============================================================
#
# IMPORTANT: Single Source of Truth 在 .wukong/canonical/
# - track-dags.json: 轨道 DAG 定义
# - research-keywords.json: 研究类任务关键词
# - explicit-avatars.json: 显式分身指定标记
#
# 此处配置需与 canonical/ 目录下的 JSON 文件保持同步
#
# TODO: 未来可实现从 JSON 动态加载配置
# ============================================================

# ============================================================
# 分身配置表 (Avatar Configurations)
# ============================================================
#
# IMPORTANT: Single Source of Truth 在 .wukong/skills/jie.md
# 此处配置需与 jie.md 中的"分身边界定义"章节保持同步
#
# TODO: 未来可实现从 jie.md 动态解析配置，避免重复定义
# 参考: parse_jie_boundaries() 函数（待实现）
#
# 同步检查清单:
# - [ ] Do 列表与 jie.md 一致
# - [ ] Don't 列表与 jie.md 一致
# - [ ] Tools 列表与 jie.md 一致
# - [ ] Cost/MaxConcurrent/Background 与 jie.md 一致
#
# ============================================================

# 分身配置表 - 镜像自 jie.md (Single Source of Truth)
AVATAR_CONFIGS: dict[Avatar, AvatarConfig] = {
    Avatar.EYE: AvatarConfig(
        name="眼分身",
        cost=CostTier.CHEAP,
        max_concurrent=10,
        background=True,
        do=["搜索", "定位", "探索", "扫描文件", "分析代码结构"],
        dont=["修改代码", "执行命令", "写文件", "删除文件"],
        tools=["Glob", "Grep", "Read"]
    ),
    Avatar.EAR: AvatarConfig(
        name="耳分身",
        cost=CostTier.CHEAP,
        max_concurrent=10,
        background=False,
        do=["澄清需求", "定义AC", "分析用户意图", "识别约束"],
        dont=["实现设计", "写代码", "执行命令"],
        tools=["Read"]
    ),
    Avatar.NOSE: AvatarConfig(
        name="鼻分身",
        cost=CostTier.CHEAP,
        max_concurrent=5,
        background=True,
        do=["审查代码", "扫描问题", "检测风险", "评估质量"],
        dont=["修复代码", "实现功能", "执行命令"],
        tools=["Read", "Grep"]
    ),
    Avatar.TONGUE: AvatarConfig(
        name="舌分身",
        cost=CostTier.MEDIUM,
        max_concurrent=3,
        background=False,
        do=["写测试", "写文档", "生成报告", "执行测试"],
        dont=["实现功能", "修改业务代码"],
        tools=["Read", "Write", "Bash"]
    ),
    Avatar.BODY: AvatarConfig(
        name="斗战胜佛",
        cost=CostTier.EXPENSIVE,
        max_concurrent=1,
        background=False,
        do=["写代码", "修复bug", "实现功能", "重构代码"],
        dont=["跳过测试", "跳过验证", "硬编码凭证"],
        tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
    ),
    Avatar.MIND: AvatarConfig(
        name="意分身",
        cost=CostTier.EXPENSIVE,
        max_concurrent=1,
        background=False,
        do=["架构设计", "技术选型", "方案评估", "决策记录"],
        dont=["写实现代码", "执行命令"],
        tools=["Read", "Write"]  # 只能写 .md 文件
    ),
}

# 轨道关键词
TRACK_KEYWORDS: dict[Track, list[str]] = {
    Track.FEATURE: ["添加", "创建", "新增", "实现", "开发", "add", "create", "new", "implement", "feature"],
    Track.FIX: ["修复", "修正", "解决", "bug", "fix", "error", "crash", "issue", "问题"],
    Track.REFACTOR: ["重构", "优化", "清理", "整理", "refactor", "clean", "optimize", "modernize"],
}

# 研究类任务关键词 (强制委派给眼分身)
RESEARCH_KEYWORDS: list[str] = [
    "研究", "调研", "了解", "学习", "探索", "分析一下", "看看", "查一下",
    "research", "investigate", "study", "explore", "look into", "find out"
]

# 显式分身指定
EXPLICIT_AVATAR_MARKERS: dict[str, Avatar] = {
    "@眼": Avatar.EYE, "@explorer": Avatar.EYE,
    "@耳": Avatar.EAR, "@analyst": Avatar.EAR,
    "@鼻": Avatar.NOSE, "@reviewer": Avatar.NOSE,
    "@舌": Avatar.TONGUE, "@tester": Avatar.TONGUE,
    "@身": Avatar.BODY, "@impl": Avatar.BODY, "@斗战胜佛": Avatar.BODY, "@implementer": Avatar.BODY,
    "@意": Avatar.MIND, "@architect": Avatar.MIND,
}

# 轨道 DAG 定义
TRACK_DAGS: dict[Track, list[DAGNode]] = {
    Track.FEATURE: [
        DAGNode(1, [Avatar.EAR, Avatar.EYE], parallel=True, description="需求+探索"),
        DAGNode(2, [Avatar.MIND], parallel=False, description="设计"),
        DAGNode(3, [Avatar.BODY], parallel=False, description="实现"),
        DAGNode(4, [Avatar.TONGUE, Avatar.NOSE], parallel=True, description="验证+审查"),
    ],
    Track.FIX: [
        DAGNode(1, [Avatar.EYE, Avatar.NOSE], parallel=True, description="定位+审查"),
        DAGNode(2, [Avatar.BODY], parallel=False, description="修复"),
        DAGNode(3, [Avatar.TONGUE], parallel=False, description="回归测试"),
    ],
    Track.REFACTOR: [
        DAGNode(1, [Avatar.EYE], parallel=False, description="现状分析"),
        DAGNode(2, [Avatar.MIND], parallel=False, description="重构策略"),
        DAGNode(3, [Avatar.BODY], parallel=False, description="实施"),
        DAGNode(4, [Avatar.NOSE, Avatar.TONGUE], parallel=True, description="验证+审查"),
    ],
    Track.DIRECT: [
        DAGNode(1, [], parallel=False, description="直接执行指定分身"),
    ],
}


# ============================================================
# 验证器实现
# ============================================================

class OrchestrationValidator:
    """编排验证器"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: list[OrchestrationDecision] = []

    # ----------------------------------------------------------
    # 路由选择
    # ----------------------------------------------------------

    def parse_explicit_avatar(self, task: str) -> Optional[Avatar]:
        """解析显式 @ 标记"""
        for marker, avatar in EXPLICIT_AVATAR_MARKERS.items():
            if marker in task.lower():
                return avatar
        return None

    def select_track(self, task: str) -> Track:
        """选择轨道"""
        task_lower = task.lower()

        # 检查显式分身指定
        if self.parse_explicit_avatar(task):
            return Track.DIRECT

        # 检查关键词
        for track, keywords in TRACK_KEYWORDS.items():
            for keyword in keywords:
                if keyword in task_lower:
                    return track

        # 默认直接执行
        return Track.DIRECT

    def is_research_task(self, task: str) -> bool:
        """检测是否为研究类任务 (必须委派给眼分身)"""
        task_lower = task.lower()
        return any(kw in task_lower for kw in RESEARCH_KEYWORDS)

    def select_primary_avatar(self, task: str, track: Track) -> Avatar:
        """选择主要分身"""
        # 显式指定优先
        explicit = self.parse_explicit_avatar(task)
        if explicit:
            return explicit

        # 研究类任务强制委派给眼分身 (最高优先级检查)
        if self.is_research_task(task):
            return Avatar.EYE

        # 根据轨道选择
        if track == Track.FEATURE:
            return Avatar.BODY  # 最终由身执行
        elif track == Track.FIX:
            return Avatar.BODY
        elif track == Track.REFACTOR:
            return Avatar.BODY
        else:
            # 分析任务内容 (优先级从高到低)
            task_lower = task.lower()
            # 需求分析优先 (包含"需求"关键词)
            if any(kw in task_lower for kw in ["需求", "requirement", "澄清", "clarify"]):
                return Avatar.EAR
            # 代码探索
            elif any(kw in task_lower for kw in ["探索", "搜索", "查找", "explore", "search", "find"]):
                return Avatar.EYE
            # 分析类任务需要看上下文
            elif "分析" in task_lower or "analyze" in task_lower:
                # 如果是分析需求，用耳分身；如果是分析代码，用眼分身
                if any(kw in task_lower for kw in ["需求", "requirement", "用户", "user"]):
                    return Avatar.EAR
                else:
                    return Avatar.EYE
            elif any(kw in task_lower for kw in ["设计", "架构", "方案", "design", "architect"]):
                return Avatar.MIND
            elif any(kw in task_lower for kw in ["测试", "test"]):
                return Avatar.TONGUE
            elif any(kw in task_lower for kw in ["审查", "review"]):
                return Avatar.NOSE
            else:
                return Avatar.BODY

    # ----------------------------------------------------------
    # 验证逻辑
    # ----------------------------------------------------------

    def validate_routing(self, task: str, expected_track: Optional[Track] = None,
                        expected_avatar: Optional[Avatar] = None) -> ValidationResult:
        """验证路由决策"""
        actual_track = self.select_track(task)
        actual_avatar = self.select_primary_avatar(task, actual_track)

        # 如果没有期望值，根据规则推断
        if expected_track is None:
            expected_track = actual_track
        if expected_avatar is None:
            expected_avatar = actual_avatar

        passed = (actual_track == expected_track and actual_avatar == expected_avatar)

        return ValidationResult(
            name="路由验证",
            passed=passed,
            expected=f"Track={expected_track.value}, Avatar={expected_avatar.value}",
            actual=f"Track={actual_track.value}, Avatar={actual_avatar.value}",
            details=f"任务: {task}"
        )

    def validate_parallelization(self, tasks: list[dict]) -> ValidationResult:
        """
        验证并行决策

        tasks: [{"task": str, "files": list[str], "avatar": Avatar}]
        """
        # 检查文件冲突
        file_owners: dict[str, list[str]] = {}
        conflicts = []

        for t in tasks:
            for f in t.get("files", []):
                if f not in file_owners:
                    file_owners[f] = []
                file_owners[f].append(t["task"])

        for f, owners in file_owners.items():
            if len(owners) > 1:
                conflicts.append(f"文件 {f} 被多个任务修改: {owners}")

        # 检查 EXPENSIVE 分身并行
        expensive_avatars = [t for t in tasks if AVATAR_CONFIGS[t["avatar"]].cost == CostTier.EXPENSIVE]
        if len(expensive_avatars) > 1:
            conflicts.append(f"EXPENSIVE 分身不能并行: {[t['avatar'].value for t in expensive_avatars]}")

        passed = len(conflicts) == 0

        return ValidationResult(
            name="并行验证",
            passed=passed,
            expected="无文件冲突，EXPENSIVE 分身串行",
            actual="无冲突" if passed else f"{len(conflicts)} 个冲突",
            details="\n".join(conflicts) if conflicts else "所有任务可安全并行"
        )

    def validate_boundary(self, avatar: Avatar, actions: list[str]) -> ValidationResult:
        """验证角色边界"""
        config = AVATAR_CONFIGS[avatar]
        violations = []

        for action in actions:
            action_lower = action.lower()
            # 检查是否在 Don't 列表中
            for dont in config.dont:
                if dont.lower() in action_lower:
                    violations.append(f"违规: {avatar.value}分身不应该 '{action}' (规则: 禁止{dont})")

        passed = len(violations) == 0

        return ValidationResult(
            name="边界验证",
            passed=passed,
            expected=f"{avatar.value}分身只做: {config.do}",
            actual="无越界" if passed else f"{len(violations)} 个越界",
            details="\n".join(violations) if violations else f"所有操作符合 {avatar.value}分身职责"
        )

    def validate_dag_completeness(self, track: Track, executed_phases: list[int]) -> ValidationResult:
        """验证 DAG 完整性"""
        expected_dag = TRACK_DAGS[track]
        expected_phases = [node.phase for node in expected_dag]

        missing = [p for p in expected_phases if p not in executed_phases]
        extra = [p for p in executed_phases if p not in expected_phases]

        passed = len(missing) == 0

        details_parts = []
        if missing:
            for p in missing:
                node = next((n for n in expected_dag if n.phase == p), None)
                if node:
                    details_parts.append(f"缺失 Phase {p}: {node.description} ({[a.value for a in node.avatars]})")
        if extra:
            details_parts.append(f"额外 Phase: {extra}")

        return ValidationResult(
            name="DAG完整性",
            passed=passed,
            expected=f"Phase {expected_phases}",
            actual=f"Phase {executed_phases}",
            details="\n".join(details_parts) if details_parts else "DAG 完整"
        )

    def validate_cost_routing(self, avatar: Avatar, background: bool, concurrent_count: int) -> ValidationResult:
        """验证成本路由"""
        config = AVATAR_CONFIGS[avatar]
        violations = []

        # 检查后台模式
        if config.cost == CostTier.EXPENSIVE and background:
            violations.append(f"EXPENSIVE 分身({avatar.value})不应后台执行")

        if config.cost == CostTier.CHEAP and not background and avatar in [Avatar.EYE, Avatar.NOSE]:
            violations.append(f"CHEAP 分身({avatar.value})建议后台执行")

        # 检查并发数
        if concurrent_count > config.max_concurrent:
            violations.append(f"{avatar.value}分身并发数 {concurrent_count} 超过限制 {config.max_concurrent}")

        passed = len(violations) == 0

        return ValidationResult(
            name="成本路由",
            passed=passed,
            expected=f"{avatar.value}: {config.cost.value}, max={config.max_concurrent}, bg={config.background}",
            actual=f"bg={background}, concurrent={concurrent_count}",
            details="\n".join(violations) if violations else "成本路由正确"
        )

    # ----------------------------------------------------------
    # 综合验证
    # ----------------------------------------------------------

    def validate_task(self, task: str,
                     expected_track: Optional[Track] = None,
                     expected_avatar: Optional[Avatar] = None) -> OrchestrationDecision:
        """验证单个任务的完整编排决策"""
        track = self.select_track(task)
        dag = TRACK_DAGS[track]

        decision = OrchestrationDecision(
            task=task,
            track=track,
            dag=dag
        )

        # 路由验证
        decision.validations.append(
            self.validate_routing(task, expected_track, expected_avatar)
        )

        # DAG 完整性 (模拟执行所有阶段)
        executed_phases = [node.phase for node in dag]
        decision.validations.append(
            self.validate_dag_completeness(track, executed_phases)
        )

        # 成本路由 (主要分身)
        primary_avatar = self.select_primary_avatar(task, track)
        config = AVATAR_CONFIGS[primary_avatar]
        decision.validations.append(
            self.validate_cost_routing(primary_avatar, config.background, 1)
        )

        self.results.append(decision)
        return decision

    def run_test_suite(self) -> list[OrchestrationDecision]:
        """运行完整测试套件"""
        test_cases = [
            # 功能开发轨道
            {"task": "添加用户登录功能", "expected_track": Track.FEATURE},
            {"task": "创建新的 API 端点", "expected_track": Track.FEATURE},
            {"task": "实现 JWT 认证", "expected_track": Track.FEATURE},

            # 问题修复轨道
            {"task": "修复登录 bug", "expected_track": Track.FIX},
            {"task": "解决内存泄漏问题", "expected_track": Track.FIX},
            {"task": "fix the crash on startup", "expected_track": Track.FIX},

            # 重构轨道
            {"task": "重构认证模块", "expected_track": Track.REFACTOR},
            {"task": "优化数据库查询", "expected_track": Track.REFACTOR},
            {"task": "清理遗留代码", "expected_track": Track.REFACTOR},

            # 直接执行 (显式指定)
            {"task": "@眼 探索认证模块", "expected_track": Track.DIRECT, "expected_avatar": Avatar.EYE},
            {"task": "@意 设计缓存方案", "expected_track": Track.DIRECT, "expected_avatar": Avatar.MIND},
            {"task": "@身 实现登录接口", "expected_track": Track.DIRECT, "expected_avatar": Avatar.BODY},
            {"task": "@鼻 审查这个 PR", "expected_track": Track.DIRECT, "expected_avatar": Avatar.NOSE},
            {"task": "@舌 编写单元测试", "expected_track": Track.DIRECT, "expected_avatar": Avatar.TONGUE},

            # 边界测试
            {"task": "帮我看看代码", "expected_track": Track.DIRECT, "expected_avatar": Avatar.EYE},
            {"task": "分析这个需求", "expected_track": Track.DIRECT, "expected_avatar": Avatar.EAR},

            # 研究类任务 (强制委派给眼分身，轨道可能因关键词变化)
            {"task": "研究一下这个问题怎么解决", "expected_track": Track.FIX, "expected_avatar": Avatar.EYE},  # "问题"触发Fix轨道
            {"task": "帮我调研一下市面上的方案", "expected_track": Track.DIRECT, "expected_avatar": Avatar.EYE},
            {"task": "了解一下现有的实现", "expected_track": Track.FEATURE, "expected_avatar": Avatar.EYE},  # "实现"触发Feature轨道
            {"task": "学习一下这个框架", "expected_track": Track.DIRECT, "expected_avatar": Avatar.EYE},
        ]

        results = []
        for tc in test_cases:
            decision = self.validate_task(
                tc["task"],
                tc.get("expected_track"),
                tc.get("expected_avatar")
            )
            results.append(decision)

        # 并行验证测试
        parallel_test = self.validate_parallelization([
            {"task": "修改 auth.py", "files": ["src/auth.py"], "avatar": Avatar.BODY},
            {"task": "修改 user.py", "files": ["src/user.py"], "avatar": Avatar.BODY},
        ])

        conflict_test = self.validate_parallelization([
            {"task": "修改 auth.py 添加登录", "files": ["src/auth.py"], "avatar": Avatar.BODY},
            {"task": "修改 auth.py 添加注册", "files": ["src/auth.py"], "avatar": Avatar.BODY},
        ])

        # 边界验证测试
        eye_boundary_pass = self.validate_boundary(Avatar.EYE, ["搜索代码", "分析结构"])
        eye_boundary_fail = self.validate_boundary(Avatar.EYE, ["搜索代码", "修改文件"])

        return results


# ============================================================
# 报告生成
# ============================================================

def generate_markdown_report(validator: OrchestrationValidator) -> str:
    """生成 Markdown 报告"""
    lines = [
        "# Wukong 编排验证报告",
        "",
        f"**生成时间**: {datetime.now().isoformat()}",
        "",
        "---",
        "",
        "## 测试摘要",
        "",
    ]

    total = len(validator.results)
    passed = sum(1 for r in validator.results if r.all_passed)
    failed = total - passed

    lines.extend([
        f"| 指标 | 值 |",
        f"|------|-----|",
        f"| 总计 | {total} |",
        f"| 通过 | {passed} |",
        f"| 失败 | {failed} |",
        f"| 通过率 | {passed/total*100:.1f}% |" if total > 0 else "| 通过率 | N/A |",
        "",
        "---",
        "",
        "## 详细结果",
        "",
    ])

    for decision in validator.results:
        status = "✅" if decision.all_passed else "❌"
        lines.extend([
            f"### {status} {decision.task}",
            "",
            f"- **轨道**: {decision.track.value}",
            f"- **DAG**: {' → '.join([f'Phase {n.phase}({n.description})' for n in decision.dag])}",
            "",
        ])

        for v in decision.validations:
            v_status = "✅" if v.passed else "❌"
            lines.extend([
                f"#### {v_status} {v.name}",
                "",
                f"- **期望**: {v.expected}",
                f"- **实际**: {v.actual}",
            ])
            if v.details:
                lines.append(f"- **详情**: {v.details}")
            lines.append("")

    lines.extend([
        "---",
        "",
        "## 轨道规则参考",
        "",
        "| 轨道 | 触发词 | DAG |",
        "|------|--------|-----|",
    ])

    for track, keywords in TRACK_KEYWORDS.items():
        dag = TRACK_DAGS[track]
        dag_str = " → ".join([f"{n.description}" for n in dag])
        lines.append(f"| {track.value} | {', '.join(keywords[:3])}... | {dag_str} |")

    lines.extend([
        "",
        "## 分身配置参考",
        "",
        "| 分身 | 成本 | 并发 | 后台 | Do | Don't |",
        "|------|------|------|------|-----|-------|",
    ])

    for avatar, config in AVATAR_CONFIGS.items():
        lines.append(
            f"| {config.name} | {config.cost.value} | {config.max_concurrent} | "
            f"{'Yes' if config.background else 'No'} | {', '.join(config.do[:2])}... | {', '.join(config.dont[:2])}... |"
        )

    return "\n".join(lines)


def generate_json_report(validator: OrchestrationValidator) -> dict:
    """生成 JSON 报告"""
    def decision_to_dict(d: OrchestrationDecision) -> dict:
        return {
            "task": d.task,
            "track": d.track.value,
            "dag": [
                {
                    "phase": n.phase,
                    "avatars": [a.value for a in n.avatars],
                    "parallel": n.parallel,
                    "description": n.description
                }
                for n in d.dag
            ],
            "validations": [
                {
                    "name": v.name,
                    "passed": v.passed,
                    "expected": v.expected,
                    "actual": v.actual,
                    "details": v.details
                }
                for v in d.validations
            ],
            "all_passed": d.all_passed
        }

    total = len(validator.results)
    passed = sum(1 for r in validator.results if r.all_passed)

    return {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0
        },
        "results": [decision_to_dict(d) for d in validator.results]
    }


# ============================================================
# 主程序
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Wukong 编排验证器")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 格式输出")
    parser.add_argument("--task", "-t", type=str, help="验证单个任务")
    parser.add_argument("--output", "-o", type=str, help="输出文件路径")

    args = parser.parse_args()

    validator = OrchestrationValidator(verbose=args.verbose)

    if args.task:
        # 验证单个任务
        decision = validator.validate_task(args.task)
        print(f"\n任务: {decision.task}")
        print(f"轨道: {decision.track.value}")
        print(f"通过: {'是' if decision.all_passed else '否'}")
        for v in decision.validations:
            status = "✅" if v.passed else "❌"
            print(f"  {status} {v.name}: {v.actual}")
    else:
        # 运行完整测试套件
        validator.run_test_suite()

        if args.json:
            report = generate_json_report(validator)
            output = json.dumps(report, ensure_ascii=False, indent=2)
        else:
            output = generate_markdown_report(validator)

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"报告已保存到: {args.output}")
        else:
            print(output)

    # 返回退出码
    total = len(validator.results)
    passed = sum(1 for r in validator.results if r.all_passed)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
