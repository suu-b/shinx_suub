from typing import Any
from langgraph.graph import StateGraph, END, START
from langchain_core.language_models import BaseChatModel

from shinx.core.state import BaseState
from shinx.orchestration.agent import OrchestratorAgent
from shinx.orchestration.agents.optimizer import OptimizerAgent
from shinx.logger_config import get_logger

logger = get_logger(__name__)

def build_orchestration_graph(llm: BaseChatModel, tools: dict[str, Any]):
    """
    Build a multi-agent orchestration graph with orchestrator.

    Args:
        llm: LLM choice
        tools: Dictionary of tool name to BaseTool instance
    """
    logger.info("Building orchestration graph...")
    logger.debug(f"Tools: {list(tools.keys())}")

    workflow = StateGraph(BaseState)

    orchestrator = OrchestratorAgent(llm=llm)
    optimizer = OptimizerAgent(llm=llm)

    workflow.add_node("orchestrator", orchestrator.create_agent_node(tools=tools))
    workflow.add_node("optimizer", optimizer.create_agent_node(tools=tools))

    workflow.add_edge(START, "orchestrator")
    workflow.add_edge("optimizer", "orchestrator")

    logger.info("Orchestration graph compiled")
    return workflow.compile()