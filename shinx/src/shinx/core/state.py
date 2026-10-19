from typing import Annotated, TypedDict, List, Any, NotRequired
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class BaseState(TypedDict):
    """State for the multi-agent orchestration."""
    messages: Annotated[List[BaseMessage], add_messages]
    # can be none for certain agents like creation (not implemented yet)
    query: str | None

    task_type: NotRequired[str]  # optimize/generate/implement (optional, determined by orchestrator)

    # represents output of agent execution
    agent_results: NotRequired[dict[str, Any]]
    # represents status of each agent (for parallel execution support)
    agent_status: NotRequired[dict[str, str]]  # {"agent_name": "pending|running|completed|failed"}

    # to capture errors in case
    agent_error: NotRequired[str | None]

    # important to prevent exhaustion
    iterations: int
    max_iterations: int
