"""Node functions for LangGraph agent pipeline"""
from typing import TypedDict, List, Dict, Any, Annotated
import uuid
from datetime import datetime
from collections import defaultdict
import polars as pl
from src.db.clickhouse_client import get_clickhouse_client
from src.db.session import get_db_context
from src.db.models import Source
from src.services.hotness_scorer import get_hotness_scorer
from src.services.llm_client import get_llm_client
from src.core.logging_config import log


class AgentState(TypedDict):
    """State object passed between nodes in the graph"""
    time_window_hours: int
    top_k: int
    raw_articles: List[Dict[str, Any]]
    clustered_articles: Dict[str, List[Dict[str, Any]]]
    scored_clusters: List[Dict[str, Any]]
    enriched_results: List[Dict[str, Any]]
    final_output: List[Dict[str, Any]]


def fetch_recent_news_node(state: AgentState) -> AgentState:
    """Node 1: Fetch recent news from ClickHouse"""
    log.info(f"Fetching news from last {state['time_window_hours']} hours")
    
    clickhouse = get_clickhouse_client()
    articles = clickhouse.get_recent_articles(state["time_window_hours"])
    
    state["raw_articles"] = articles
    log.info(f"Fetched {len(articles)} articles")
    
    return state


def cluster_articles_node(state: AgentState) -> AgentState:
    """Node 2: Group articles by dedup_group"""
    log.info("Clustering articles by dedup_group")
    
    clusters = defaultdict(list)
    for article in state["raw_articles"]:
        dedup_group = article.get("dedup_group")
        if dedup_group:
            clusters[str(dedup_group)].append(article)
    
    state["clustered_articles"] = dict(clusters)
    log.info(f"Created {len(clusters)} clusters")
    
    return state


def calculate_hotness_node(state: AgentState) -> AgentState:
    """Node 3: Calculate hotness score for each cluster"""
    log.info("Calculating hotness scores")
    
    scorer = get_hotness_scorer()
    scored_clusters = []
    
    # Fetch source reputation scores
    with get_db_context() as db:
        sources = {s.id: s.reputation_score for s in db.query(Source).all()}
    
    for dedup_group, articles in state["clustered_articles"].items():
        # Get reputation scores for articles in this cluster
        reputation_scores = [
            sources.get(article.get("source_id"), 0.5)
            for article in articles
        ]
        
        hotness = scorer.calculate_hotness(
            articles=articles,
            source_reputation_scores=reputation_scores,
            time_window_hours=state["time_window_hours"],
        )
        
        scored_clusters.append({
            "dedup_group": dedup_group,
            "articles": articles,
            "hotness": hotness,
            "article_count": len(articles),
        })
    
    # Sort by hotness score (descending)
    scored_clusters.sort(key=lambda x: x["hotness"], reverse=True)
    
    state["scored_clusters"] = scored_clusters
    log.info(f"Scored {len(scored_clusters)} clusters")
    
    return state


def rank_and_select_node(state: AgentState) -> AgentState:
    """Node 4: Select top K clusters"""
    log.info(f"Selecting top {state['top_k']} clusters")
    
    top_clusters = state["scored_clusters"][: state["top_k"]]
    state["enriched_results"] = top_clusters
    
    log.info(f"Selected {len(top_clusters)} clusters for enrichment")
    
    return state


def enrich_with_llm_node(state: AgentState) -> AgentState:
    """Node 5: Enrich top clusters with LLM-generated content"""
    log.info("Enriching clusters with LLM")
    
    llm = get_llm_client()
    final_results = []
    
    for cluster in state["enriched_results"]:
        articles = cluster["articles"]
        
        # Consolidate article content
        consolidated_text = "\n\n---\n\n".join([
            f"Title: {art.get('title', '')}\n"
            f"Source ID: {art.get('source_id', '')}\n"
            f"Published: {art.get('published_at', '')}\n"
            f"URL: {art.get('url', '')}\n"
            f"Content: {art.get('content', '')[:1000]}"  # Limit content length
            for art in articles
        ])
        
        # Generate enriched data with LLM
        try:
            prompt = f"""You are a financial news analyst. Analyze the following news cluster and provide structured output.

News Articles:
{consolidated_text}

Generate a JSON response with the following fields:
1. "headline": A concise, impactful headline (max 100 chars)
2. "why_now": 1-2 sentences explaining why this is important NOW (novelty, confirmations, scale of impact)
3. "entities": A list of companies, tickers, countries, or sectors mentioned (max 10 items)
4. "timeline": A list of key timestamps with brief descriptions (format: [{{"time": "YYYY-MM-DD HH:MM", "event": "description"}}])
5. "draft": A complete draft post as a SINGLE STRING with markdown formatting. Include:
   - Lead paragraph (2-3 sentences)
   - 3 bullet points (use - for bullets)
   - A relevant quote or reference with attribution
   
Example format for draft field:
"draft": "Lead paragraph here.\\n\\n- First key point\\n- Second key point\\n- Third key point\\n\\n\\"Quote here\\" - Source"

Ensure all information is grounded in the provided articles. RESPOND IN RUSSIA"""

            result = llm.generate_json(prompt, temperature=0.5, max_tokens=2000)
            
            # Extract sources
            sources = [
                {
                    "url": art.get("url", ""),
                    "title": art.get("title", ""),
                    "published_at": str(art.get("published_at", "")),
                }
                for art in articles[:5]  # Top 5 sources
            ]
            
            # Convert draft to string if it's a dict
            draft_content = result.get("draft", "")
            if isinstance(draft_content, dict):
                # If LLM returned structured draft, convert to string
                lead = draft_content.get("lead", "")
                bullets = draft_content.get("bullets", [])
                quote = draft_content.get("quote", "")
                
                draft_str = f"{lead}\n\n"
                for bullet in bullets:
                    draft_str += f"- {bullet}\n"
                if quote:
                    draft_str += f"\n\"{quote}\""
                draft_content = draft_str
            
            final_results.append({
                "dedup_group": cluster["dedup_group"],
                "hotness": cluster["hotness"],
                "headline": result.get("headline", "No headline"),
                "why_now": result.get("why_now", ""),
                "entities": result.get("entities", []),
                "sources": sources,
                "timeline": result.get("timeline", []),
                "draft": draft_content,
            })
            
            log.info(f"Enriched cluster {cluster['dedup_group']} with LLM")
            
        except Exception as e:
            log.error(f"Failed to enrich cluster {cluster['dedup_group']}: {e}")
            # Fallback to basic data
            final_results.append({
                "dedup_group": cluster["dedup_group"],
                "hotness": cluster["hotness"],
                "headline": articles[0].get("title", "")[:100],
                "why_now": "Analysis unavailable",
                "entities": [],
                "sources": [{"url": art.get("url", ""), "title": art.get("title", "")} for art in articles[:3]],
                "timeline": [],
                "draft": "",
            })
    
    state["final_output"] = final_results
    log.info(f"Enriched {len(final_results)} clusters")
    
    return state

