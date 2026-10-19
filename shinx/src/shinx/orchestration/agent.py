from typing import Any, Literal
from langgraph.types import Command
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from shinx.core.state import BaseState
from shinx.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from shinx.models.orchestrator import OrchestratorDecision
from shinx.logger_config import get_logger

logger = get_logger(__name__)

class OrchestratorAgent:
    """Orchestrator agent that coordinates specialized database agents."""

    def __init__(self, llm: BaseChatModel):
        logger.info("Creating orchestrator agent instance")
        self.llm = llm

    def get_name(self) -> str:
        return "orchestrator"

    def get_system_prompt(self) -> str:
        return ORCHESTRATOR_SYSTEM_PROMPT

    def create_agent_node(self, tools: dict[str, Any]):
        def agent_node(state: BaseState) -> Command[Literal["optimizer", "__end__"]]:
            state_context = f"""Current State:
- query: {state.get('query')}
- task_type: {state.get('task_type')}
- iterations: {state.get('iterations')} / {state.get('max_iterations')}
"""
            messages = [
                SystemMessage(content=self.get_system_prompt()),
                SystemMessage(content=state_context),
                *state["messages"],
            ]

            # Gemini does not support model prefilling — the last message
            # must be a user message or a function response, never an AIMessage.
            # When routing from the orchestrator after an agent completes,
            # the history ends with an AIMessage, so we append a continuation prompt.
            if messages and isinstance(messages[-1], AIMessage):
                messages.append(HumanMessage(content="Please continue with the task."))

            # Log messages being sent to LLM for debugging
            logger.debug(f"Sending {len(messages)} messages to LLM:")
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                content_preview = str(msg.content)[:100] if hasattr(msg, 'content') else "N/A"
                logger.debug(f"  [{i}] {msg_type}: {content_preview}...")

            llm_structured = self.llm.with_structured_output(OrchestratorDecision)
            decision: OrchestratorDecision = llm_structured.invoke(messages)

            goto = "__end__" if decision.next_agent == "END" else decision.next_agent

            update = {
                "iterations": state["iterations"] + 1,
            }

            # Only update task_type if explicitly set
            if decision.task_type is not None:
                update["task_type"] = decision.task_type

            # Always update agent_status (merge with existing)
            existing_status = state.get("agent_status", {})
            # Set orchestrator status and target agent status
            status_update = {"orchestrator": "running"}
            if decision.next_agent != "END":
                status_update[decision.next_agent] = "running"
            update["agent_status"] = {**existing_status, **status_update}

            # Append AI explanation message
            ai_message = AIMessage(content=decision.reasoning)
            update["messages"] = [ai_message]

            return Command(goto=goto, update=update)

        return agent_node