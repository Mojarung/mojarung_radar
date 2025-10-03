from langgraph.graph import StateGraph, END
from app.graph.state import RadarState
from app.graph.nodes.ingestion import ingestion_node
from app.graph.nodes.deduplication import deduplication_node
from app.graph.nodes.enrichment import enrichment_node
from app.graph.nodes.scoring import scoring_node
from app.graph.nodes.context import context_builder_node
from app.graph.nodes.draft import draft_generator_node
from app.core.logging import get_logger

logger = get_logger(__name__)


def should_generate_draft(state: RadarState) -> str:
    """Условие: нужно ли генерировать черновик."""
    if state["should_generate_draft"]:
        return "context"
    return "end"


def create_radar_graph():
    """Создает граф агента RADAR.
    
    Граф обрабатывает новости следующим образом:
    Ingestion → Deduplication → Enrichment → Scoring
                                                ↓
    [hotness_score > threshold?] → Context → Draft → END
                ↓
               END
    """
    workflow = StateGraph(RadarState)
    
    workflow.add_node("ingestion", ingestion_node)
    workflow.add_node("deduplication", deduplication_node)
    workflow.add_node("enrichment", enrichment_node)
    workflow.add_node("scoring", scoring_node)
    workflow.add_node("context", context_builder_node)
    workflow.add_node("draft", draft_generator_node)
    
    workflow.set_entry_point("ingestion")
    
    workflow.add_edge("ingestion", "deduplication")
    workflow.add_edge("deduplication", "enrichment")
    workflow.add_edge("enrichment", "scoring")
    
    workflow.add_conditional_edges(
        "scoring",
        should_generate_draft,
        {
            "context": "context",
            "end": END
        }
    )
    
    workflow.add_edge("context", "draft")
    workflow.add_edge("draft", END)
    
    graph = workflow.compile()
    
    logger.info("RADAR graph created successfully")
    
    return graph

