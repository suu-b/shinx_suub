from langchain_core.tools import BaseTool
from shinx.db import DatabaseAdapter
 
from shinx.tools.database.database_info import create_database_info_tool
from shinx.tools.database.explain_query import create_explain_query_tool
from shinx.tools.database.inspect_table import create_inspect_table_tool
from shinx.tools.database.list_tables import create_list_tables_tool
from shinx.tools.database.table_stats import create_table_stats_tool

def create_database_tools(adapter: DatabaseAdapter) -> list[BaseTool]:
    """Creates all database inspection tools"""
    return [
        create_explain_query_tool(adapter),
        create_inspect_table_tool(adapter),
        create_table_stats_tool(adapter),
        create_list_tables_tool(adapter),
        create_database_info_tool(adapter),
    ]

__all__ = [
    "create_database_tools"
]