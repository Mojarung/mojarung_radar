"""LangGraph graph definition for news analysis pipeline"""
import asyncio
from langgraph.graph import StateGraph, END
from src.agents.nodes import (
    AgentState,
    fetch_recent_news_node,
    cluster_articles_node,
    calculate_hotness_node,
    calculate_ml_hotness_node,
    rank_and_select_node,
    enrich_with_llm_node,
    enrich_with_llm_node_async,
)
from src.core.logging_config import log


def create_analysis_graph(async_mode: bool = False):
    """Create the LangGraph workflow for news analysis"""

    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("fetch_news", fetch_recent_news_node)
    workflow.add_node("cluster", cluster_articles_node)
    workflow.add_node("calculate_hotness", calculate_hotness_node)
    workflow.add_node("calculate_ml_hotness", calculate_ml_hotness_node)
    workflow.add_node("rank_select", rank_and_select_node)

    # Use async or sync LLM enrichment
    if async_mode:
        workflow.add_node("enrich_llm", enrich_with_llm_node_async)
        log.info("Using async LLM enrichment node")
    else:
        workflow.add_node("enrich_llm", enrich_with_llm_node)
        log.info("Using sync LLM enrichment node")

    # Define edges
    workflow.set_entry_point("fetch_news")
    workflow.add_edge("fetch_news", "cluster")
    workflow.add_edge("cluster", "calculate_hotness")
    workflow.add_edge("calculate_hotness", "calculate_ml_hotness")
    workflow.add_edge("calculate_ml_hotness", "rank_select")
    workflow.add_edge("rank_select", "enrich_llm")
    workflow.add_edge("enrich_llm", END)

    # Compile graph
    app = workflow.compile()

    log.info(f"LangGraph analysis workflow created (async_mode: {async_mode})")

    return app


# Create singleton instances
analysis_graph = create_analysis_graph(async_mode=False)  # Default sync
async_analysis_graph = create_analysis_graph(async_mode=True)  # Async version


def run_analysis(time_window_hours: int = 720, top_k: int = 5, async_mode: bool = False):
    """Run the complete analysis pipeline"""
    log.info(f"Starting analysis (window: {time_window_hours}h, top_k: {top_k}, async: {async_mode})")

    initial_state: AgentState = {
        "time_window_hours": time_window_hours,
        "top_k": top_k,
        "raw_articles": [],
        "clustered_articles": {},
        "scored_clusters": [],
        "enriched_results": [],
        "final_output": [],
    }

    # Use appropriate graph based on async mode
    graph = async_analysis_graph if async_mode else analysis_graph

    if async_mode:
        # For async mode, run in thread executor to avoid event loop conflicts
        import concurrent.futures

        def run_sync_analysis():
            return graph.invoke(initial_state)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_sync_analysis)
            final_state = future.result()
    else:
        final_state = graph.invoke(initial_state)

    log.info("Analysis completed")

    return final_state["final_output"]



