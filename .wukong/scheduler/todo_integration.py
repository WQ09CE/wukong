#!/usr/bin/env python3
"""TodoWrite 集成模块"""

from typing import List, Dict, Any

try:
    from .scheduler import WukongScheduler, ScheduledTask, TaskStatus, AvatarType, AVATAR_CONFIG
except ImportError:
    from scheduler import WukongScheduler, ScheduledTask, TaskStatus, AvatarType, AVATAR_CONFIG


class TodoWriteIntegration:
    """TodoWrite 集成器"""

    def __init__(self, scheduler: WukongScheduler):
        self.scheduler = scheduler

    def generate_todo_call(self) -> Dict[str, Any]:
        todos = []
        sorted_tasks = sorted(self.scheduler.tasks.values(), key=lambda t: t.created_at)

        for task in sorted_tasks:
            status_map = {
                TaskStatus.PENDING: "pending",
                TaskStatus.IN_PROGRESS: "in_progress",
                TaskStatus.COMPLETED: "completed",
                TaskStatus.FAILED: "pending",
                TaskStatus.BLOCKED: "pending",
            }

            avatar_emoji = {
                AvatarType.EYE: "👁️", AvatarType.EAR: "👂", AvatarType.NOSE: "👃",
                AvatarType.TONGUE: "👅", AvatarType.BODY: "⚔️", AvatarType.MIND: "🧠",
            }

            emoji = avatar_emoji.get(task.avatar, "")
            todos.append({
                "content": f"{emoji} [{task.avatar.value}分身] {task.description}",
                "status": status_map[task.status],
                "activeForm": f"正在执行 {task.avatar.value}分身任务: {task.description[:30]}...",
            })

        return {"todos": todos}

    def sync_from_todo_status(self, todo_updates: List[Dict[str, str]]):
        for update in todo_updates:
            content = update.get("content", "")
            status = update.get("status", "")

            for task in self.scheduler.tasks.values():
                if task.avatar.value in content and task.description[:20] in content:
                    if status == "completed":
                        self.scheduler.complete_task(task.task_id, success=True)
                    elif status == "in_progress":
                        self.scheduler.start_task(task.task_id)
                    break


def generate_summoning_declaration(task: ScheduledTask) -> str:
    config = AVATAR_CONFIG[task.avatar]
    return f"""我将召唤分身:
- **分身**: {task.avatar.value} - {task.avatar.name}分身
- **原因**: 执行 {task.description}
- **技能**: {task.avatar.value}分身核心能力
- **预期**: 任务完成后返回符合 Output Contract 的结果

**执行模式**:
- 模型: {config['model']}
- 后台: {config['background']}
- 成本: {config['cost'].value}
"""


def generate_task_invocation(task: ScheduledTask) -> str:
    config = AVATAR_CONFIG[task.avatar]
    bg = config["background"] == "必须"
    return f'''Task(
    prompt="""{task.prompt}""",
    model="{config['model']}",
    run_in_background={bg}
)'''
