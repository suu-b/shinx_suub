from typing import Any, Literal
from langgraph.types import Command
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models import BaseChatModel

from shinx.core.state import BaseState
from shinx.prompts import OPTIMIZER_SYSTEM_PROMPT
from shinx.logger_config import get_logger

logger = get_logger(__name__)

class OptimizerAgent:
    """Optimizer agent that analyzes SQL queries and provides optimization recommendations."""

    def __init__(self, llm: BaseChatModel):
        logger.info("Creating optimizer agent instance")
        self.llm = llm

    def get_name(self) -> str:
        return "optimizer"

    def get_system_prompt(self) -> str:
        return OPTIMIZER_SYSTEM_PROMPT

    def create_agent_node(self, tools: dict[str, Any]):
        # Filter tools to only the ones optimizer needs
        required_tool_names = [
            "explain_query",
            "inspect_table",
            "table_stats",
            "list_tables",
            "database_info"
        ]
        optimizer_tools = [tools[name] for name in required_tool_names if name in tools]

        agent = create_agent(
            model=self.llm,
            tools=optimizer_tools,
            system_prompt=self.get_system_prompt(),
        )

        def agent_node(state: BaseState) -> Command[Literal["orchestrator"]]:
            messages = list(state["messages"])

            # Gemini does not support model prefilling — the last message
            # must be a user message or a function response, never an AIMessage.
            if messages and isinstance(messages[-1], AIMessage):
                messages.append(HumanMessage(content="Please continue with the task."))

            result = agent.invoke({"messages": messages})

            # Only return messages added by this agent invocation (avoid
            # double-appending with the add_messages reducer in BaseState)
            prior_count = len(state["messages"])
            new_messages = result["messages"][prior_count:]

            # Extract result from final message content (optimizer always outputs JSON summary)
            result_str = ""
            if new_messages:
                final_msg = new_messages[-1]
                if hasattr(final_msg, 'content'):
                    result_str = final_msg.content

            return Command(
                goto="orchestrator",
                update={
                    "messages": new_messages,
                    "agent_results": {"output": result_str},
                    "agent_status": {"optimizer": "completed"},
                    "iterations": state["iterations"] + 1,
                }
            )

        return agent_node