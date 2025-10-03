from app.graph.state import RadarState
from app.core.logging import get_logger
from app.services.embeddings import EmbeddingService

logger = get_logger(__name__)


async def deduplication_node(state: RadarState) -> RadarState:
    """Узел дедупликации через векторное сходство.
    
    Определяет, является ли новость перепечаткой или частью существующего сюжета.
    """
    logger.info(f"Deduplication node processing: {state['news_id']}")
    
    embedding_service = EmbeddingService()
    
    is_duplicate, cluster_id = await embedding_service.find_duplicate(
        state["news_content"],
        threshold=0.85
    )
    
    state["is_duplicate"] = is_duplicate
    if is_duplicate and cluster_id:
        state["cluster_id"] = cluster_id
        logger.info(f"News {state['news_id']} is duplicate, cluster: {cluster_id}")
    else:
        logger.info(f"News {state['news_id']} is unique")
    
    return state

