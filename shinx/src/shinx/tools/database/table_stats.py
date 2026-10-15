from typing import Annotated, Any
from langchain_core.tools import BaseTool, tool
from pydantic import Field

from shinx.db import DatabaseAdapter

def create_table_stats_tool(adapter: DatabaseAdapter) -> BaseTool:
    @tool
    def table_stats(
        table_name: Annotated[str, Field(description="The name of the table to check row count and stats for.")],
        schema_name: Annotated[str, Field(description="The schema name, defaults to 'public'.")] = "public",
    ) -> dict[str, Any]:
        """Fetches table-specific statistics including current row count and disk size. Crucial for assessing whether optimization/indexing is warranted based on table volume."""
        return adapter.get_table_stats(table_name, schema_name)

    return table_stats
