from typing import Literal

from langgraph.graph import END, START, StateGraph

from src.agents.nodes import (
    ContextRAGNode,
    DeduplicationNode,
    DraftGeneratorNode,
    EnrichmentNode,
    ScoringNode,
)
from src.agents.state import RadarState
from src.core.logging import get_logger

logger = get_logger(__name__)


def create_radar_graph(
    dedup_node: DeduplicationNode,
    enrichment_node: EnrichmentNode,
    scoring_node: ScoringNode,
    context_rag_node: ContextRAGNode,
    draft_generator_node: DraftGeneratorNode,
):
    workflow = StateGraph(RadarState)

    workflow.add_node("deduplication", dedup_node)
    workflow.add_node("enrichment", enrichment_node)
    workflow.add_node("scoring", scoring_node)
    workflow.add_node("context_rag", context_rag_node)
    workflow.add_node("draft_generator", draft_generator_node)

    workflow.add_edge(START, "deduplication")
    workflow.add_edge("deduplication", "enrichment")
    workflow.add_edge("enrichment", "scoring")

    def should_generate_draft(state: RadarState) -> Literal["context_rag", "__end__"]:
        if state.get("is_hot", False):
            logger.info("routing_to_rag", hotness=state.get("hotness_score"))
            return "context_rag"
        logger.info("routing_to_end", hotness=state.get("hotness_score"))
        return END

    workflow.add_conditional_edges(
        "scoring",
        should_generate_draft,
        {
            "context_rag": "context_rag",
            END: END,
        },
    )

    workflow.add_edge("context_rag", "draft_generator")
    workflow.add_edge("draft_generator", END)

    return workflow.compile()

