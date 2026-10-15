from abc import ABC, abstractmethod
from typing import Any
from langchain_core.language_models import BaseChatModel

from shinx.orchestration.state import State
from shinx.factory.agent_node_factory import create_agent_node

class BaseAgent(ABC):
    def __init__(
        self,
        llm: BaseChatModel,
        verbose: bool = True
    ):
        self.llm = llm
        self.verbose = verbose

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the agent's name for routing."""
        pass
 
    @abstractmethod
    def get_required_tools(self) -> list[str]:
        """Return names of tools this agent needs."""
        pass

    def create_node(self, tools: dict[str, Any], **kwargs):
        """
        Creates a LangGraph node for this agent with its required tools.
        
        Args:
            tools: Dictionary of available tools
            **kwargs: Additional context (e.g., agents dict for supervisor)
        
        Returns:
            Node function for LangGraph
        """
        agent_tools = [tools[name] for name in self.get_required_tools()]
        return create_agent_node(self.llm, agent_tools)
