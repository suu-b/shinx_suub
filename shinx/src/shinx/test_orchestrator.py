import os
import pprint
from langchain_core.messages import SystemMessage, HumanMessage

from shinx.adapters.postgres_adapter import PostgresAdapter
from shinx.factory.llm_factory import get_chat_model
from shinx.tools import create_db_tools
from shinx.orchestration.agents.optimizer import OptimizerAgent
from shinx.orchestration.graph import build_orchestration_graph
from shinx.prompts.optimizer_prompt import OPTIMIZER_SYSTEM_PROMPT


def main():
    query = "SELECT * FROM members"

    print("Connecting to PostgreSQL...")
    try:
        adapter = PostgresAdapter(
            host=os.getenv("PGHOST", "localhost"),
            port=int(os.getenv("PGPORT", "5432")),
            dbname=os.getenv("PGDATABASE", "postgres"),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD", "postgres"),
        )
    except Exception as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        print("Make sure your PostgreSQL is running and environment variables are set.")
        return

    # Get LangChain-compatible LLM
    print("Initializing LLM...")
    llm = get_chat_model()
    
    # Get tools as list of BaseTool instances
    print("Loading database tools...")
    tools_list = create_db_tools(adapter)
    tools_dict = {tool.name: tool for tool in tools_list}
    
    # Create agents
    print("Creating agents...")
    optimizer = OptimizerAgent(llm=llm)
    agents = {"optimizer": optimizer}
    
    # Build orchestration graph
    print("Building LangGraph...")
    graph = build_orchestration_graph(
        agents=agents,
        tools=tools_dict,
        supervisor_llm=llm
    )

    print(f"\n{'='*60}")
    print(f"Running LangGraph Orchestrator for query:")
    print(f"{query}")
    print(f"{'='*60}\n")

    # Initialize state
    initial_state = {
        "messages": [
            SystemMessage(content=OPTIMIZER_SYSTEM_PROMPT),
            HumanMessage(content=f"Analyze and optimize:\n\n```sql\n{query}\n```")
        ],
        "query": query,
        "tool_results": [],
        "turn_count": 0,
        "max_turns": 5,
        "error": None,
        "current_agent": None,
        "task_type": "optimize",
        "task_data": {}
    }
    
    config = {
        "recursion_limit": 10
    }
    
    # Run the graph
    result = graph.invoke(initial_state, config=config)

    print(f"\n{'='*60}")
    print(" WORKFLOW COMPLETED")
    print(f"{'='*60}")
    print(f"Total turns: {result['turn_count']}")
    print(f"Final agent: {result.get('current_agent', 'unknown')}")
    print(f"\nFinal messages count: {len(result['messages'])}")
    
    # Print the last message (should contain the optimization report)
    if result['messages']:
        last_message = result['messages'][-1]
        print(f"\nFinal response content:")
        print(last_message.content if hasattr(last_message, 'content') else last_message)


if __name__ == "__main__":
    main()