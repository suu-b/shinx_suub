import os
import json
from langchain_core.messages import HumanMessage

from shinx.adapters.postgres_adapter import PostgresAdapter
from shinx.factory.llm_factory import get_chat_model
from shinx.tools import create_db_tools
from shinx.orchestration.graph import build_orchestration_graph
from shinx.logger_config import get_logger

def main():
    logger = get_logger(__name__)
    query = "SELECT * FROM members;"

    logger.info("=" * 60)
    logger.info("SHINX MULTI-AGENT ORCHESTRATOR TEST")
    logger.info("=" * 60)
    logger.info(f"Target Query: {query}")
    logger.info("Connecting to PostgreSQL...")

    try:
        creds = {
            "host": os.getenv("PGHOST", "localhost"),
            "port": int(os.getenv("PGPORT", "5432")),
            "dbname": os.getenv("PGDATABASE", "postgres"),
            "user": os.getenv("PGUSER", "postgres"),
        }
        logger.debug(f"Connecting to PostgreSQL with creds: {creds} + password (hidden)")
        adapter = PostgresAdapter(
            host=os.getenv("PGHOST", "localhost"),
            port=int(os.getenv("PGPORT", "5432")),
            dbname=os.getenv("PGDATABASE", "postgres"),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD", "postgres"),
        )
        logger.info("Connected to PostgreSQL")
    except Exception as e:
        logger.warning("Tip: Make sure your PostgreSQL is running and environment variables are set.")
        logger.exception(f"Error connecting to PostgreSQL database: {e}")
        return

    logger.info("Initializing LLM...")
    llm = get_chat_model()
    logger.info(f"LLM initialized: {llm.__class__.__name__}")

    logger.info("Loading database tools...")
    tools_list = create_db_tools(adapter)
    logger.debug(f"Tools list: {tools_list}")
    tools_dict = {tool.name: tool for tool in tools_list}
    logger.info(f"Loaded {len(tools_dict)} tools: {list(tools_dict.keys())}")

    logger.info("Building orchestration graph...")
    graph = build_orchestration_graph(
        llm=llm,
        tools=tools_dict
    )
    logger.info("Orchestration graph built")

    logger.info("=" * 60)
    logger.info("EXECUTING QUERY")
    logger.info("=" * 60)

    # Run the graph
    initial_state = {
        "messages": [
            HumanMessage(content=query)
        ],
        "query": query,
        "iterations": 0,
        "max_iterations": 5,  # keep low on free tier (15 req/min limit)
        "task_type": None,
        "agent_status": {},
        "agent_results": {},
        "agent_error": None,
    }

    config = {
        "recursion_limit": 20
    }

    logger.debug(f"Initial state: {initial_state}")
    logger.debug(f"Config: {config}")

    try:
        result = graph.invoke(initial_state, config=config)

        logger.info("=" * 60)
        logger.info("EXECUTION COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Total iterations: {result['iterations']}")
        logger.info(f"Agent status: {result.get('agent_status', 'unknown')}")

        if result.get('agent_error'):
            logger.error(f"Agent error: {result['agent_error']}")

        if result.get('agent_results'):
            logger.info("-" * 60)
            logger.info("AGENT RESULTS")
            logger.info("-" * 60)
            logger.info(json.dumps(result['agent_results'], indent=2))

        # Print message history
        logger.info("-" * 60)
        logger.info("MESSAGE HISTORY")
        logger.info("-" * 60)
        for i, msg in enumerate(result.get('messages', [])):
            msg_type = type(msg).__name__
            logger.info(f"[{i}] {msg_type}: {str(msg.content)[:200]}")

    except Exception as e:
        logger.error("Execution failed")
        logger.exception(e)


if __name__ == "__main__":
    main()
