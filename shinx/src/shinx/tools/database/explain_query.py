import re
from typing import Annotated, Any
from langchain_core.tools import BaseTool, tool
from pydantic import Field

from shinx.db import DatabaseAdapter

FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|CREATE)\b",
    re.IGNORECASE,
)

def create_explain_query_tool(adapter: DatabaseAdapter) -> BaseTool:
    @tool
    def explain_query(
        query: Annotated[str, Field(description="The exact SQL SELECT query to explain.")],
    ) -> dict[str, Any]:
        """Explains a SQL query to retrieve its execution plan (costs, scan types, rows, filters, join conditions)."""
        cleaned = query.strip()
        if FORBIDDEN_SQL_PATTERN.search(cleaned):
            return {"error": "Only read-only SELECT queries can be explained for security reasons."}

        plan = adapter.explain(cleaned)
        if plan is None:
            return {"error": "Failed to generate query execution plan."}
        return plan.model_dump() if hasattr(plan, "model_dump") else plan

    return explain_query
