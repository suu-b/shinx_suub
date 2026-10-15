from shinx.orchestration.state import State

def should_continue(state: State) -> str:
    """
    Determine if we should continue tool calling or end the workflow.

    Args:
        state: Current workflow state

    Returns:
        "tools" if we should execute tools, "end" if we should stop
    """
    if state["turn_count"] >= state["max_turns"]:
        return "end"

    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"

    # If no tool calls, go to END instead of back to supervisor
    return "end"


def route_to_agent(state: State) -> str:
    """
    Route to the appropriate agent based on supervisor's decision.

    Args:
        state: Current workflow state

    Returns:
        The name of the agent to route to, or "END" to stop
    """
    current_agent = state.get("current_agent")
    
    # If supervisor says END, return special marker
    if current_agent == "END":
        return "END"
    
    # Otherwise return the agent name
    return current_agent