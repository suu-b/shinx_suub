from shinx.core.agent import BaseAgent
from shinx.prompts.optimizer_prompt import OPTIMIZER_SYSTEM_PROMPT

class OptimizerAgent(BaseAgent):
    def get_name(self) -> str:
        return "optimizer"

    def get_system_prompt(self) -> str:
        return OPTIMIZER_SYSTEM_PROMPT

    def get_required_tools(self) -> list[str]:
        return [
            "explain_query",
            "inspect_table",
            "table_stats",
            "list_tables",
            "database_info"
        ]