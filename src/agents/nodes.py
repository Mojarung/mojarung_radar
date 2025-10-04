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
from src.services.ml_scorer import get_ml_scorer
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


def calculate_ml_hotness_node(state: AgentState) -> AgentState:
    """Node 3.5: Calculate ML-based hotness scores for clusters"""
    log.info("Calculating ML-based hotness scores")

    ml_scorer = get_ml_scorer()
    ml_scored_clusters = []

    for cluster in state["scored_clusters"]:
        dedup_group = cluster["dedup_group"]
        articles = cluster["articles"]

        # Get ML scores for all articles in this cluster
        ml_scored_articles = ml_scorer.score_articles(articles)

        # Calculate average ML score for the cluster
        ml_scores = [article.get("ml_hot_score", 0.0) for article in ml_scored_articles]
        avg_ml_score = sum(ml_scores) / len(ml_scores) if ml_scores else 0.0

        # Update cluster with ML score
        cluster_copy = cluster.copy()
        cluster_copy["ml_hotness"] = avg_ml_score
        cluster_copy["ml_scored_articles"] = ml_scored_articles

        ml_scored_clusters.append(cluster_copy)

    state["ml_scored_clusters"] = ml_scored_clusters
    log.info(f"Calculated ML scores for {len(ml_scored_clusters)} clusters")

    return state


def rank_and_select_node(state: AgentState) -> AgentState:
    """Node 4: Select top K clusters using combined scoring"""
    log.info(f"Selecting top {state['top_k']} clusters using combined scoring")

    # Get clusters with both traditional and ML scores
    clusters = state.get("ml_scored_clusters", state.get("scored_clusters", []))

    if not clusters:
        log.warning("No clusters available for ranking")
        state["enriched_results"] = []
        return state

    # Calculate combined scores for ranking
    for cluster in clusters:
        traditional_score = cluster.get("hotness", 0.0)
        ml_score = cluster.get("ml_hotness", 0.0)

        # Weighted combination (70% traditional, 30% ML for conservative approach)
        combined_score = (traditional_score * 0.7) + (ml_score * 0.3)
        cluster["combined_hotness"] = combined_score

        log.debug(f"Cluster {cluster['dedup_group'][:8]}: "
                 f"Traditional={traditional_score:.3f}, ML={ml_score:.3f}, "
                 f"Combined={combined_score:.3f}")

    # Sort by combined score (descending)
    clusters.sort(key=lambda x: x.get("combined_hotness", 0.0), reverse=True)

    # Select top K clusters
    top_clusters = clusters[: state["top_k"]]
    state["enriched_results"] = top_clusters

    log.info(f"Selected {len(top_clusters)} clusters for enrichment")
    log.info(f"Top cluster combined scores: {[(c['dedup_group'][:8], c.get('combined_hotness', 0.0)) for c in top_clusters]}")

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
            prompt = f"""Ты — финансовый новостной аналитик и создатель контента для Telegram. Проанализируй следующие новостные статьи и предоставь структурированный ответ.

Новостные статьи:
{consolidated_text}

Сгенерируй JSON ответ со следующими полями:

1. "headline": Краткий, яркий заголовок (максимум 100 символов)

2. "why_now": 1-2 предложения, объясняющие, почему это важно СЕЙЧАС (новизна, подтверждения, масштаб влияния)

3. "entities": Список компаний, тикеров, стран или секторов, упомянутых в новостях (максимум 10 элементов)

4. "timeline": Список ключевых временных точек с краткими описаниями (формат: [{{"time": "YYYY-MM-DD HH:MM", "event": "описание"}}])

5. "draft": Полный черновик поста как ОДНА СТРОКА с markdown форматированием. Включи:
   - Вводный параграф (2-3 предложения)
   - 3 ключевых пункта (используй - для буллитов)
   - Релевантную цитату или ссылку с атрибуцией

6. "telegram_post": Готовый к публикации пост для Telegram в следующем формате:
   - Начни с подходящего эмодзи (⚡️ для срочного/важного, 😀 для забавного/неожиданного, 🧐 для аналитического, 📊 для данных/статистики, 💰 для финансового)
   - Затем заголовок
   - Основной текст в 2-3 коротких абзацах ИЛИ буллиты (▶️) если несколько заявлений
   - Если новость вызывает дискуссию/мнение, добавь в конце короткий вопрос и 2-3 варианта реакций-эмодзи
   - Для сухих фактов или длинных списков пропусти опрос
   - Делай кратко, вовлекающе и готово к копированию
   
Пример формата telegram_post:
"⚡️Минимальную пенсию в России хотят увеличить до ₽35 тысяч\\n\\nС такой идеей выступил депутат Мособлдумы Анатолий Никитин. По его словам, увеличение пенсии положительно скажется на демографической ситуации. Пенсионерам не нужно будет работать, они смогут «больше времени уделять внукам, передавать и прививать традиционные ценности».\\n\\nТакже депутат отметил, что такое решение увеличит уровень жизни пожилых людей.\\n\\nПоддерживаем?\\n❤️‍🔥 – определенно да!\\n😁 – нет, в таком случае либо пенсионный возраст повысят, либо цены на что-нибудь вырастут\\n🐳 – мне без разницы"

ВАЖНО: ВСЕ поля должны быть НА РУССКОМ ЯЗЫКЕ. Отвечай только на русском."""

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
            
            # Get telegram_post
            telegram_post = result.get("telegram_post", "")
            if not telegram_post:
                # Fallback: create basic telegram post from headline
                telegram_post = f"⚡️{result.get('headline', 'Новость')}\n\n{result.get('why_now', '')}"
            
            final_results.append({
                "dedup_group": cluster["dedup_group"],
                "hotness": cluster["hotness"],
                "ml_hotness": cluster.get("ml_hotness", 0.0),
                "combined_hotness": cluster.get("combined_hotness", cluster["hotness"]),
                "headline": result.get("headline", "No headline"),
                "why_now": result.get("why_now", ""),
                "entities": result.get("entities", []),
                "sources": sources,
                "timeline": result.get("timeline", []),
                "draft": draft_content,
                "telegram_post": telegram_post,
            })
            
            log.info(f"Enriched cluster {cluster['dedup_group']} with LLM")
            
        except Exception as e:
            log.error(f"Failed to enrich cluster {cluster['dedup_group']}: {e}")
            # Fallback to basic data
            headline = articles[0].get("title", "")[:100]
            final_results.append({
                "dedup_group": cluster["dedup_group"],
                "hotness": cluster["hotness"],
                "ml_hotness": cluster.get("ml_hotness", 0.0),
                "combined_hotness": cluster.get("combined_hotness", cluster["hotness"]),
                "headline": headline,
                "why_now": "Analysis unavailable",
                "entities": [],
                "sources": [{"url": art.get("url", ""), "title": art.get("title", "")} for art in articles[:3]],
                "timeline": [],
                "draft": "",
                "telegram_post": f"📰{headline}\n\nПодробности скоро...",
            })
    
    state["final_output"] = final_results
    log.info(f"Enriched {len(final_results)} clusters")
    
    return state

