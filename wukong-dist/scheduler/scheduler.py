#!/usr/bin/env python3
"""
Wukong Lightweight Scheduler (悟空轻量级调度器)

在 Claude Code 限制下实现分身调度:
- 无外部队列依赖
- 内存状态 + TodoWrite 追踪
- Task 工具并发控制
- 文件领地冲突检测
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
from datetime import datetime
import json
import re


# ============== 枚举定义 ==============

class AvatarType(Enum):
    """六根分身类型"""
    EYE = "眼"      # 探索·搜索 (CHEAP)
    EAR = "耳"      # 需求·理解 (CHEAP)
    NOSE = "鼻"     # 审查·检测 (CHEAP)
    TONGUE = "舌"   # 测试·文档 (MEDIUM)
    BODY = "身"     # 实现·行动 (EXPENSIVE)
    MIND = "意"     # 设计·决策 (EXPENSIVE)


class CostTier(Enum):
    """成本层级"""
    CHEAP = "cheap"         # 10+ 并发，必须后台
    MEDIUM = "medium"       # 2-3 并发，可选后台
    EXPENSIVE = "expensive" # 1 并发，禁止后台


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TrackType(Enum):
    """轨道类型"""
    FEATURE = "feature"     # Add/Create/New
    FIX = "fix"             # Fix/Bug/Error
    REFACTOR = "refactor"   # Refactor/Clean
    DIRECT = "direct"       # 直接执行


# ============== 配置 ==============

AVATAR_CONFIG: Dict[AvatarType, dict] = {
    AvatarType.EYE:    {"cost": CostTier.CHEAP,     "model": "haiku",  "max_concurrent": 10, "background": "必须"},
    AvatarType.EAR:    {"cost": CostTier.CHEAP,     "model": "haiku",  "max_concurrent": 10, "background": "可选"},
    AvatarType.NOSE:   {"cost": CostTier.CHEAP,     "model": "haiku",  "max_concurrent": 5,  "background": "必须"},
    AvatarType.TONGUE: {"cost": CostTier.MEDIUM,    "model": "sonnet", "max_concurrent": 3,  "background": "可选"},
    AvatarType.BODY:   {"cost": CostTier.EXPENSIVE, "model": "opus",   "max_concurrent": 1,  "background": "禁止"},
    AvatarType.MIND:   {"cost": CostTier.EXPENSIVE, "model": "opus",   "max_concurrent": 1,  "background": "禁止"},
}

TRACK_DAG: Dict[TrackType, List[List[AvatarType]]] = {
    TrackType.FEATURE: [
        [AvatarType.EAR, AvatarType.EYE],
        [AvatarType.MIND],
        [AvatarType.BODY],
        [AvatarType.TONGUE, AvatarType.NOSE],
    ],
    TrackType.FIX: [
        [AvatarType.EYE, AvatarType.NOSE],
        [AvatarType.BODY],
        [AvatarType.TONGUE],
    ],
    TrackType.REFACTOR: [
        [AvatarType.EYE],
        [AvatarType.MIND],
        [AvatarType.BODY],
        [AvatarType.NOSE, AvatarType.TONGUE],
    ],
    TrackType.DIRECT: [],
}


# ============== 数据结构 ==============

@dataclass
class Territory:
    """文件领地"""
    file_path: str
    owner: str
    granularity: str = "file"
    function_name: Optional[str] = None
    class_name: Optional[str] = None

    def conflicts_with(self, other: "Territory") -> bool:
        if self.file_path != other.file_path:
            return False
        if self.granularity == "file" or other.granularity == "file":
            return True
        if self.granularity == "function" and other.granularity == "function":
            return self.function_name == other.function_name
        if self.granularity == "class" and other.granularity == "class":
            return self.class_name == other.class_name
        return False


@dataclass
class ScheduledTask:
    """调度任务"""
    task_id: str
    avatar: AvatarType
    description: str
    prompt: str
    status: TaskStatus = TaskStatus.PENDING
    territories: List[Territory] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    background: bool = False


# ============== 调度器核心 ==============

class WukongScheduler:
    """悟空轻量级调度器"""

    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.territories: Dict[str, Territory] = {}
        self.active_by_tier: Dict[CostTier, List[str]] = {
            CostTier.CHEAP: [],
            CostTier.MEDIUM: [],
            CostTier.EXPENSIVE: [],
        }
        self._task_counter = 0

    def _generate_task_id(self, avatar: AvatarType) -> str:
        self._task_counter += 1
        return f"{avatar.value}_{self._task_counter:03d}"

    def claim_territory(self, task_id: str, territories: List[Territory]) -> List[str]:
        conflicts = []
        for new_t in territories:
            for existing_path, existing_t in self.territories.items():
                if existing_t.owner != task_id and new_t.conflicts_with(existing_t):
                    conflicts.append(f"{existing_path} (owned by {existing_t.owner})")

        if not conflicts:
            for t in territories:
                key = f"{t.file_path}:{t.granularity}:{t.function_name or t.class_name or 'full'}"
                self.territories[key] = t
        return conflicts

    def release_territory(self, task_id: str):
        to_remove = [k for k, v in self.territories.items() if v.owner == task_id]
        for k in to_remove:
            del self.territories[k]

    def can_start(self, task: ScheduledTask) -> tuple:
        config = AVATAR_CONFIG[task.avatar]
        tier = config["cost"]
        max_concurrent = config["max_concurrent"]

        for dep_id in task.depends_on:
            dep_task = self.tasks.get(dep_id)
            if dep_task and dep_task.status != TaskStatus.COMPLETED:
                return False, f"Blocked by dependency: {dep_id}"

        active_count = len(self.active_by_tier[tier])
        if active_count >= max_concurrent:
            return False, f"Max concurrent {tier.value} tasks reached ({active_count}/{max_concurrent})"

        conflicts = self.claim_territory(task.task_id, task.territories)
        if conflicts:
            return False, f"Territory conflicts: {conflicts}"

        return True, "Ready"

    def get_execution_mode(self, avatar: AvatarType) -> dict:
        config = AVATAR_CONFIG[avatar]
        bg = config["background"]
        return {
            "model": config["model"],
            "run_in_background": bg == "必须" or (bg == "可选" and config["cost"] == CostTier.CHEAP),
            "background_required": bg == "必须",
            "background_forbidden": bg == "禁止",
        }

    def add_task(self, avatar: AvatarType, description: str, prompt: str,
                 territories: Optional[List[Territory]] = None,
                 depends_on: Optional[List[str]] = None) -> ScheduledTask:
        task_id = self._generate_task_id(avatar)
        task = ScheduledTask(
            task_id=task_id,
            avatar=avatar,
            description=description,
            prompt=prompt,
            territories=territories or [],
            depends_on=depends_on or [],
        )
        self.tasks[task_id] = task
        return task

    def start_task(self, task_id: str) -> bool:
        task = self.tasks.get(task_id)
        if not task:
            return False

        can, reason = self.can_start(task)
        if not can:
            task.status = TaskStatus.BLOCKED
            return False

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now().isoformat()
        config = AVATAR_CONFIG[task.avatar]
        self.active_by_tier[config["cost"]].append(task_id)
        return True

    def complete_task(self, task_id: str, result: Optional[str] = None, success: bool = True):
        task = self.tasks.get(task_id)
        if not task:
            return

        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = datetime.now().isoformat()
        task.result = result

        config = AVATAR_CONFIG[task.avatar]
        if task_id in self.active_by_tier[config["cost"]]:
            self.active_by_tier[config["cost"]].remove(task_id)
        self.release_territory(task_id)

    def get_ready_tasks(self) -> List[ScheduledTask]:
        ready = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                can, _ = self.can_start(task)
                if can:
                    ready.append(task)
        return ready

    def schedule_next_batch(self) -> List[ScheduledTask]:
        ready = self.get_ready_tasks()
        if not ready:
            return []

        by_tier: Dict[CostTier, List[ScheduledTask]] = {
            CostTier.CHEAP: [], CostTier.MEDIUM: [], CostTier.EXPENSIVE: [],
        }

        for task in ready:
            tier = AVATAR_CONFIG[task.avatar]["cost"]
            by_tier[tier].append(task)

        batch = []
        for tier in [CostTier.CHEAP, CostTier.MEDIUM, CostTier.EXPENSIVE]:
            max_concurrent = {CostTier.CHEAP: 10, CostTier.MEDIUM: 3, CostTier.EXPENSIVE: 1}[tier]
            current_active = len(self.active_by_tier[tier])
            slots = max_concurrent - current_active
            for task in by_tier[tier][:slots]:
                batch.append(task)
        return batch

    @staticmethod
    def detect_track(user_input: str) -> TrackType:
        input_lower = user_input.lower()
        if any(kw in input_lower for kw in ["add", "create", "new", "implement feature", "功能"]):
            return TrackType.FEATURE
        if any(kw in input_lower for kw in ["fix", "bug", "error", "crash", "issue", "修复"]):
            return TrackType.FIX
        if any(kw in input_lower for kw in ["refactor", "clean", "optimize", "重构"]):
            return TrackType.REFACTOR
        return TrackType.DIRECT

    def plan_track(self, track: TrackType, task_description: str) -> List[List[ScheduledTask]]:
        dag = TRACK_DAG.get(track, [])
        if not dag:
            return []

        phases = []
        prev_task_ids = []

        for phase_idx, avatars in enumerate(dag):
            phase_tasks = []
            for avatar in avatars:
                task = self.add_task(
                    avatar=avatar,
                    description=f"[Phase {phase_idx + 1}] {avatar.value}分身: {task_description}",
                    prompt=f"## TASK\n{task_description}\n\n## AVATAR\n{avatar.value}",
                    depends_on=prev_task_ids.copy(),
                )
                phase_tasks.append(task)
            phases.append(phase_tasks)
            prev_task_ids = [t.task_id for t in phase_tasks]
        return phases

    def to_dict(self) -> dict:
        return {
            "tasks": {
                tid: {
                    "task_id": t.task_id,
                    "avatar": t.avatar.value,
                    "description": t.description,
                    "status": t.status.value,
                    "depends_on": t.depends_on,
                }
                for tid, t in self.tasks.items()
            },
            "active_by_tier": {tier.value: ids for tier, ids in self.active_by_tier.items()},
        }

    def to_todo_list(self) -> List[dict]:
        todos = []
        for task in self.tasks.values():
            status_map = {
                TaskStatus.PENDING: "pending",
                TaskStatus.IN_PROGRESS: "in_progress",
                TaskStatus.COMPLETED: "completed",
                TaskStatus.FAILED: "pending",
                TaskStatus.BLOCKED: "pending",
            }
            todos.append({
                "content": f"[{task.avatar.value}] {task.description}",
                "status": status_map[task.status],
                "activeForm": f"执行 {task.avatar.value}分身任务",
            })
        return todos


def parse_territory_declaration(text: str) -> List[Territory]:
    """
    解析领地声明文本
    示例:
    - main.py
    - utils.py (全文件)
    - utils.py (函数: process_data)
    - models.py (类: User)
    """
    territories = []
    # 匹配: - file.py 或 - file.py (类型) 或 - file.py (类型: 名称)
    pattern = r"[-*]\s*([\w./]+\.[\w]+)(?:\s*\(?\s*(全文件|函数|类|file|function|class)?[:\s]*(\w+)?\s*\)?)?"

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            file_path = match.group(1)
            granularity_raw = match.group(2) or "file"
            name = match.group(3)

            gran_map = {"全文件": "file", "file": "file", "函数": "function",
                       "function": "function", "类": "class", "class": "class"}
            granularity = gran_map.get(granularity_raw.lower(), "file")

            t = Territory(
                file_path=file_path, owner="",
                granularity=granularity,
                function_name=name if granularity == "function" else None,
                class_name=name if granularity == "class" else None,
            )
            territories.append(t)
    return territories


def generate_task_prompt(avatar: AvatarType, task: str, expected_outcome: str,
                        context: str, must_do: List[str], must_not: List[str]) -> str:
    config = AVATAR_CONFIG[avatar]
    prefix = "ultrathink\n\n" if avatar == AvatarType.MIND else ""

    return f"""{prefix}## 1. TASK
{task}

## 2. EXPECTED OUTCOME
{expected_outcome}

## 3. REQUIRED SKILLS
{avatar.value}分身核心能力

## 4. REQUIRED TOOLS
根据分身类型自动配置

## 5. MUST DO
{chr(10).join(f'- [ ] {item}' for item in must_do)}

## 6. MUST NOT DO
{chr(10).join(f'- [ ] {item}' for item in must_not)}

## 7. CONTEXT
{context}

---
**执行配置**: model={config['model']}, background={config['background']}
"""
