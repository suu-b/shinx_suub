from pydantic import BaseModel, Field
from typing import Literal


class OrchestratorDecision(BaseModel):
    """Structured output for the orchestrator's routing decision."""

    reasoning: str = Field(
        description="Brief explanation of why this routing decision was made"
    )
    next_agent: Literal["optimizer", "END"] = Field(
        description="Which agent to dispatch next. Use END when the task is complete."
    )
    task_type: Literal["optimize", "generate", "implement"] | None = Field(
        default=None,
        description="Type of task. Set on first call, leave None to keep existing."
    )
