from langchain_core.tools import BaseTool

from shinx.db import DatabaseAdapter
from shinx.tools.database import create_database_tools

def create_db_tools(adapter: DatabaseAdapter) -> list[BaseTool]:
    return create_database_tools(adapter)

__all__ = [
    "BaseTool",
    "create_db_tools",
]