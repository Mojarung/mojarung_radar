"""News analysis API endpoints"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.api.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisResult,
    NewsSource,
    TimelineEvent,
)
from src.api.dependencies import get_db
from src.agents.graphs import run_analysis
from src.core.logging_config import log

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_news(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze recent news and return top K hot stories.
    
    This endpoint triggers the LangGraph agent pipeline which:
    1. Fetches recent articles from ClickHouse
    2. Clusters them by deduplication groups
    3. Calculates hotness scores
    4. Selects top K clusters
    5. Enriches with LLM-generated summaries and drafts
    """
    try:
        log.info(
            f"Analysis request received: window={request.time_window_hours}h, "
            f"top_k={request.top_k}"
        )
        
        # Run the LangGraph analysis pipeline
        results = run_analysis(
            time_window_hours=request.time_window_hours,
            top_k=request.top_k
        )
        
        # Convert to response schema
        analysis_results = []
        for result in results:
            analysis_results.append(
                AnalysisResult(
                    dedup_group=result["dedup_group"],
                    hotness=result["hotness"],
                    headline=result["headline"],
                    why_now=result["why_now"],
                    entities=result["entities"],
                    sources=[
                        NewsSource(**source) for source in result["sources"]
                    ],
                    timeline=[
                        TimelineEvent(**event) for event in result["timeline"]
                    ] if isinstance(result["timeline"], list) else [],
                    draft=result["draft"],
                    telegram_post=result.get("telegram_post", ""),
                )
            )
        
        # TODO: Get actual counts from the pipeline state
        total_articles = sum(len(r.get("sources", [])) for r in results)
        total_clusters = len(results)
        
        response = AnalysisResponse(
            results=analysis_results,
            total_articles_analyzed=total_articles,
            total_clusters=total_clusters,
        )
        
        log.info(f"Analysis completed: {len(analysis_results)} results")
        
        return response
        
    except Exception as e:
        log.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

