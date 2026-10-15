from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from shinx.core.agent import BaseAgent
from shinx.orchestration.state import State
from shinx.prompts.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT

class SupervisorAgent(BaseAgent):
    """Supervisor agent that routes between specialized database agents."""
    
    def get_name(self) -> str:
        return "supervisor"
    
    def get_system_prompt(self) -> str:
        return SUPERVISOR_SYSTEM_PROMPT
    
    def get_required_tools(self) -> list[str]:
        """Supervisor doesn't need tools - only makes routing decisions."""
        return []
    
    def create_node(self, tools: dict[str, Any], agents: dict[str, Any] = None):
        """
        Create a LangGraph node for the supervisor.
        
        Args:
            tools: Dictionary of available tools (not used by supervisor)
            agents: Dictionary of available agents for routing
        
        Returns:
            Supervisor node function
        """
        if agents is None:
            agents = {}
        
        agent_names = list(agents.keys())
        
        def supervisor_node(state: State) -> dict[str, Any]:
            """
            Supervisor that decides which agent to call next.
            """
            # Create messages for supervisor
            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=f"Current task: {state.get('task_type', 'optimize')}")
            ]
            
            # Add context from previous agent if available
            if state["messages"]:
                last_message = state["messages"][-1]
                if isinstance(last_message, AIMessage):
                    messages.append(last_message)
            
            # Add current agent info if available
            if state.get("current_agent"):
                messages.append(
                    HumanMessage(content=f"Previous agent: {state['current_agent']}")
                )
            
            # Get supervisor decision
            response = self.llm.invoke(messages)
            
            # Handle different response content formats
            content = response.content
            if isinstance(content, list):
                # Extract text from content blocks
                content = " ".join(str(block) for block in content)
            else:
                content = str(content)
            
            decision = content.strip().lower()
            
            # Normalize decision
            if decision == "end" or decision == "END":
                return {"current_agent": "END"}
            elif decision in agent_names:
                return {"current_agent": decision}
            else:
                # Default to optimizer if unclear
                return {"current_agent": "optimizer"}
        
        return supervisor_node
