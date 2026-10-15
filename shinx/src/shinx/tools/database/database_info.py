from typing import Any
from langchain_core.tools import BaseTool, tool

from shinx.db import DatabaseAdapter


def create_database_info_tool(adapter: DatabaseAdapter) -> BaseTool:
    @tool
    def database_info() -> dict[str, Any]:
        """Fetches database version and installed extensions."""
        return adapter.get_database_info()

    return database_info
