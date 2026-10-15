from typing import Annotated, TypedDict, List, Any
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[List, add_messages]
    query: str
    tool_results: List[dict[str, Any]]
    turn_count: int
    max_turns: int
    error: str | None
    current_agent: str
    task_type: str  # optimize/generate/implement
    task_data: dict[str, Any]