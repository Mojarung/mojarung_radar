"""LangGraph graph definition for news analysis pipeline"""
from langgraph.graph import StateGraph, END
from src.agents.nodes import (
    AgentState,
    fetch_recent_news_node,
    cluster_articles_node,
    calculate_hotness_node,
    calculate_ml_hotness_node,
    rank_and_select_node,
    enrich_with_llm_node,
)
from src.core.logging_config import log


def create_analysis_graph():
    """Create the LangGraph workflow for news analysis"""
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("fetch_news", fetch_recent_news_node)
    workflow.add_node("cluster", cluster_articles_node)
    workflow.add_node("calculate_hotness", calculate_hotness_node)
    workflow.add_node("calculate_ml_hotness", calculate_ml_hotness_node)
    workflow.add_node("rank_select", rank_and_select_node)
    workflow.add_node("enrich_llm", enrich_with_llm_node)

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
    
    log.info("LangGraph analysis workflow created")
    
    return app


# Create singleton instance
analysis_graph = create_analysis_graph()


def run_analysis(time_window_hours: int = 24, top_k: int = 5):
    """Run the complete analysis pipeline"""
    log.info(f"Starting analysis (window: {time_window_hours}h, top_k: {top_k})")
    
    initial_state: AgentState = {
        "time_window_hours": time_window_hours,
        "top_k": top_k,
        "raw_articles": [],
        "clustered_articles": {},
        "scored_clusters": [],
        "enriched_results": [],
        "final_output": [],
    }
    
    final_state = analysis_graph.invoke(initial_state)
    
    log.info("Analysis completed")
    
    return final_state["final_output"]

