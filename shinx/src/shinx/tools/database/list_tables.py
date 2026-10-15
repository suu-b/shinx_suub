from typing import Annotated, Any
from langchain_core.tools import BaseTool, tool
from pydantic import Field

from shinx.db import DatabaseAdapter

def create_list_tables_tool(adapter: DatabaseAdapter) -> BaseTool:
    @tool
    def list_tables(
        schema_name: Annotated[str, Field(description="The schema name, defaults to 'public'.")] = "public",
    ) -> dict[str, Any]:
        """Lists all user tables present in the database schema."""
        tables = adapter.list_table_names(schema_name)
        return {"schema": schema_name, "tables": tables}

    return list_tables
