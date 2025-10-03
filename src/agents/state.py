from typing import Any, TypedDict


class RadarState(TypedDict, total=False):
    initial_news: dict[str, Any]
    cluster_id: str | None
    related_articles: list[dict[str, Any]]
    entities: dict[str, Any]
    timeline: list[dict[str, Any]]
    source_reputation: float
    hotness_score: float
    narrative_summary: str
    final_output: dict[str, Any] | None
    is_hot: bool
    is_new_cluster: bool

