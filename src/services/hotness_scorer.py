"""Hotness scoring logic for news clusters"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import numpy as np
from src.core.logging_config import log


class HotnessScorer:
    """Calculate hotness score for news clusters"""

    def __init__(self):
        # Weights for different factors
        self.weights = {
            "materiality": 0.25,
            "velocity": 0.25,
            "breadth": 0.20,
            "credibility": 0.20,
            "unexpectedness": 0.10,
        }

    def calculate_hotness(
        self,
        articles: List[Dict[str, Any]],
        source_reputation_scores: List[float],
        time_window_hours: int = 720,
    ) -> float:
        """
        Calculate hotness score for a cluster of articles.
        
        Args:
            articles: List of article dictionaries
            source_reputation_scores: Reputation scores for each article's source
            time_window_hours: Time window for velocity calculation
            
        Returns:
            Hotness score between 0 and 1
        """
        if not articles:
            return 0.0

        materiality = self._calculate_materiality(articles)
        velocity = self._calculate_velocity(articles, time_window_hours)
        breadth = self._calculate_breadth(articles)
        credibility = self._calculate_credibility(source_reputation_scores)
        unexpectedness = self._calculate_unexpectedness(articles)

        hotness = (
            self.weights["materiality"] * materiality +
            self.weights["velocity"] * velocity +
            self.weights["breadth"] * breadth +
            self.weights["credibility"] * credibility +
            self.weights["unexpectedness"] * unexpectedness
        )

        log.debug(
            f"Hotness components - M:{materiality:.2f} V:{velocity:.2f} "
            f"B:{breadth:.2f} C:{credibility:.2f} U:{unexpectedness:.2f} "
            f"=> Total:{hotness:.2f}"
        )

        return min(1.0, max(0.0, hotness))

    def _calculate_materiality(self, articles: List[Dict[str, Any]]) -> float:
        """
        Calculate materiality based on keywords and content.
        
        High-impact keywords increase the score.
        """
        high_impact_keywords = [
            "merger", "acquisition", "bankruptcy", "guidance", "regulation",
            "lawsuit", "fraud", "investigation", "earnings", "restructuring",
            "default", "dividend", "buyback", "ipo", "delisting",
            "слияние", "поглощение", "банкротство", "регулирование",
            "иск", "мошенничество", "расследование", "прибыль"
        ]

        score = 0.0
        for article in articles:
            content = (article.get("title", "") + " " + article.get("content", "")).lower()
            keyword_count = sum(1 for keyword in high_impact_keywords if keyword in content)
            score += min(1.0, keyword_count / 3.0)  # Normalize to 0-1

        return min(1.0, score / len(articles))

    def _calculate_velocity(
        self, articles: List[Dict[str, Any]], time_window_hours: int
    ) -> float:
        """
        Calculate velocity as the rate of article publication.
        
        Sharp increases indicate higher velocity.
        """
        if len(articles) <= 1:
            return 0.3  # Baseline for single article

        # Sort by published_at
        sorted_articles = sorted(
            articles,
            key=lambda x: x.get("published_at", datetime.min)
        )

        # Calculate time span
        first_time = sorted_articles[0].get("published_at")
        last_time = sorted_articles[-1].get("published_at")

        if isinstance(first_time, str):
            first_time = datetime.fromisoformat(first_time.replace("Z", "+00:00"))
        if isinstance(last_time, str):
            last_time = datetime.fromisoformat(last_time.replace("Z", "+00:00"))

        time_span = (last_time - first_time).total_seconds() / 3600  # hours

        if time_span < 0.1:  # Less than 6 minutes
            time_span = 0.1

        # Articles per hour
        velocity = len(articles) / time_span

        # Normalize: 1+ articles per hour = high velocity
        normalized_velocity = min(1.0, velocity / 2.0)

        return normalized_velocity

    def _calculate_breadth(self, articles: List[Dict[str, Any]]) -> float:
        """
        Calculate breadth based on number of unique sources.
        
        More sources = higher breadth.
        """
        unique_sources = set(article.get("source_id") for article in articles)
        
        # Normalize: 5+ sources = max breadth
        breadth = min(1.0, len(unique_sources) / 5.0)
        
        return breadth

    def _calculate_credibility(self, source_reputation_scores: List[float]) -> float:
        """Calculate average credibility from source reputation scores"""
        if not source_reputation_scores:
            return 0.5  # Default middle score

        return np.mean(source_reputation_scores)

    def _calculate_unexpectedness(self, articles: List[Dict[str, Any]]) -> float:
        """
        Calculate unexpectedness (placeholder implementation).
        
        In production, this would compare against historical baseline.
        """
        # Placeholder: Use content length and title as proxy
        # Longer, more detailed articles might indicate unexpected events
        avg_length = np.mean([
            len(article.get("content", ""))
            for article in articles
        ])

        # Normalize: 2000+ chars = high unexpectedness
        unexpectedness = min(1.0, avg_length / 2000.0)

        return unexpectedness


# Singleton instance
_hotness_scorer: HotnessScorer = HotnessScorer()


def get_hotness_scorer() -> HotnessScorer:
    """Get singleton hotness scorer instance"""
    return _hotness_scorer

