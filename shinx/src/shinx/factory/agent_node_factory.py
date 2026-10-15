from typing import Any
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from shinx.orchestration.state import State

def create_agent_node(llm: BaseChatModel, tools: list):
    "Factory method to create agent nodes"
    llm_with_tools = llm.bind_tools(tools)
    
    def agent_node(state: State) -> dict[str, Any]:
        """
        Agent node that calls the LLM.
        
        Args:
            state: Current workflow state
        
        Returns:
            Updated state with LLM response
        """
        messages = state["messages"]
        
        # Filter messages to ensure compatibility with Gemini
        # Gemini requires the last message to be a user message or tool response
        filtered_messages = []
        system_content = None
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                # Store system prompt to prepend later
                system_content = msg.content
            else:
                filtered_messages.append(msg)
        
        # If we have a system prompt, inject it into the first HumanMessage
        if system_content and filtered_messages:
            first_msg = filtered_messages[0]
            if isinstance(first_msg, HumanMessage):
                # Prepend system prompt to first human message
                filtered_messages[0] = HumanMessage(
                    content=f"System instructions: {system_content}\n\nUser request: {first_msg.content}"
                )
        
        # Ensure the last message is not an AIMessage (Gemini requirement)
        # If it is, add a continuation message
        if filtered_messages and isinstance(filtered_messages[-1], AIMessage):
            filtered_messages.append(
                HumanMessage(content="Please continue.")
            )
        
        response = llm_with_tools.invoke(filtered_messages)
        return {
            "messages": [response],
            "turn_count": state["turn_count"] + 1
        }
    
    return agent_node