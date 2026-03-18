"""
WorkflowContext — 在所有 Agent 之间传递的共享状态对象
"""

from dataclasses import dataclass, field
from typing import Any
import uuid
import time


@dataclass
class WorkflowContext:
    """全局工作流上下文，贯穿所有 Agent"""

    product_brief: str                          # 用户原始需求
    project_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: float = field(default_factory=time.time)

    phase_outputs: dict[str, Any] = field(default_factory=lambda: {
        "requirements": {},     # PM Agent + Market Agent 输出
        "design": {},           # UX Agent + Design System Agent 输出
        "architecture": {},     # Architect Agent 输出
        "development": {},      # Developer + Code Review Agent 输出
        "qa": {},               # QA Agent 输出
        "launch": {},           # Launch Agent 输出
    })

    workflow_status: dict[str, Any] = field(default_factory=lambda: {
        "current_phase": "not_started",
        "completed_agents": [],
        "errors": [],
    })

    def mark_agent_done(self, agent_name: str):
        self.workflow_status["completed_agents"].append(agent_name)

    def set_phase(self, phase: str):
        self.workflow_status["current_phase"] = phase

    def to_summary(self) -> str:
        """输出工作流进度摘要"""
        completed = self.workflow_status["completed_agents"]
        phase = self.workflow_status["current_phase"]
        elapsed = round(time.time() - self.created_at, 1)
        return (
            f"项目 ID: {self.project_id} | "
            f"当前阶段: {phase} | "
            f"已完成 Agent: {len(completed)} | "
            f"耗时: {elapsed}s"
        )
