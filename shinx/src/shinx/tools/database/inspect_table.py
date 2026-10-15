from typing import Annotated, Any
from langchain_core.tools import BaseTool, tool
from pydantic import Field

from shinx.db import DatabaseAdapter

def create_inspect_table_tool(adapter: DatabaseAdapter) -> BaseTool:
    @tool
    def inspect_table(
        table_name: Annotated[str, Field(description="The name of the table to inspect.")],
        schema_name: Annotated[str, Field(description="The schema name, defaults to 'public'.")] = "public",
    ) -> dict[str, Any]:
        """Inspects complete context for a specific table: row count, columns, data types, nullability, constraints, and existing indexes."""
        table_meta = adapter.get_table_metadata(table_name, schema_name)
        if table_meta is None:
            return {"error": f"Table '{table_name}' in schema '{schema_name}' was not found."}

        data = table_meta.model_dump() if hasattr(table_meta, "model_dump") else dict(table_meta)
        try:
            stats = adapter.get_table_stats(table_name, schema_name)
            data["stats"] = stats
        except Exception:
            pass

        return data

    return inspect_table
