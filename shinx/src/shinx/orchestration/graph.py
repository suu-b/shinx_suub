from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import Any
from langchain_core.language_models import BaseChatModel

from shinx.core.agent import BaseAgent
from shinx.orchestration.state import State
from shinx.orchestration.routing import route_to_agent, should_continue
from shinx.orchestration.agents.supervisor import SupervisorAgent

def build_orchestration_graph(
    agents: dict[str, BaseAgent],
    tools: dict[str, Any],
    supervisor_llm: BaseChatModel
):
    """
    Build a multi-agent orchestration graph with supervisor.
    
    Args:
        agents: Dictionary of agent name to BaseAgent instance (excluding supervisor)
        tools: Dictionary of tool name to BaseTool instance
        supervisor_llm: LLM for the supervisor agent
    
    Returns:
        Compiled LangGraph
    """
    workflow = StateGraph(State)
    
    # Add other agent nodes first
    for name, agent in agents.items():
        workflow.add_node(name, agent.create_node(tools))
    
    # Create supervisor agent (needs to know about other agents)
    supervisor = SupervisorAgent(llm=supervisor_llm)
    
    # Add supervisor node (it needs to know about other agents for routing)
    workflow.add_node("supervisor", supervisor.create_node(tools, agents=agents))
    
    # Add shared tools node
    all_tools = list(tools.values())
    workflow.add_node("tools", ToolNode(all_tools))
    
    # Set entry point to supervisor
    workflow.set_entry_point("supervisor")
    
    # Supervisor routes to agents or END
    agent_mapping = {name: name for name in agents.keys()}
    agent_mapping["END"] = END
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        agent_mapping
    )
    
    # Each agent routes to tools or END
    for name in agents.keys():
        workflow.add_conditional_edges(
            name,
            should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
    
    # Tools always go back to supervisor
    workflow.add_edge("tools", "supervisor")
    
    return workflow.compile()