"""ML-based hotness scoring service using trained model"""
import sys
import os
import pandas as pd
from typing import List, Dict, Any
import uuid
from pathlib import Path

# Add ML module to path
ml_path = Path(__file__).parent.parent.parent / "ml"
sys.path.append(str(ml_path))

try:
    from hot_news_model.inference import predict_hot_score
except ImportError:
    print("Warning: ML model not found. Using fallback scoring.")
    predict_hot_score = None

from src.core.logging_config import log


class MLScorer:
    """ML-based hotness scorer using trained model"""

    def __init__(self, model_path: str = None):
        # Определяем путь к модели в контейнере
        if model_path is None:
            # В контейнере модель должна быть в /app/ml/hot_news_model/models/
            model_path = "/app/ml/hot_news_model/models"

        self.model_path = model_path
        self.model_name = "lenta_model.joblib"
        self.model_available = predict_hot_score is not None

        if self.model_available:
            log.info(f"ML model loaded from {model_path}")
        else:
            log.warning("ML model not available, using fallback scoring")

    def score_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score articles using ML model.

        Args:
            articles: List of article dictionaries from ClickHouse

        Returns:
            List of articles with ML-predicted hot scores
        """
        if not self.model_available or not articles:
            return self._fallback_scoring(articles)

        try:
            # Convert articles to DataFrame format expected by ML model
            df = self._articles_to_dataframe(articles)

            # Save to temporary CSV for ML model
            temp_csv = f"/tmp/articles_{uuid.uuid4()}.csv"
            df.to_csv(temp_csv, index=False)

            # Get model predictions
            temp_output = f"/tmp/ml_predictions_{uuid.uuid4()}.csv"
            results_df = predict_hot_score(
                model_path=self.model_path,
                data_path=temp_csv,
                output_path=temp_output,
                model_name=self.model_name
            )

            # Clean up temp files
            try:
                os.remove(temp_csv)
                os.remove(temp_output)
            except:
                pass

            # Merge predictions back to articles
            return self._merge_predictions(articles, results_df)

        except Exception as e:
            log.error(f"ML scoring failed: {e}")
            return self._fallback_scoring(articles)

    def _articles_to_dataframe(self, articles: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert articles to DataFrame format expected by ML model"""
        data = []

        for article in articles:
            # Handle datetime conversion
            published_at = article.get("published_at")
            if isinstance(published_at, str):
                # Convert ISO format to datetime
                try:
                    from datetime import datetime
                    published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    date_str = published_at.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    date_str = "2024-01-01 00:00:00"
            else:
                date_str = "2024-01-01 00:00:00"

            # Handle companies and people (should be lists but stored as strings)
            companies = article.get("companies", "")
            people = article.get("people", "")

            data.append({
                "headline": article.get("title", ""),
                "text": article.get("content", ""),
                "date": date_str,
                "companies": companies,
                "people": people,
            })

        return pd.DataFrame(data)

    def _merge_predictions(self, articles: List[Dict[str, Any]], results_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Merge ML predictions back to articles"""
        # Create mapping from title to prediction
        title_to_score = {}
        for _, row in results_df.iterrows():
            title = row.get("headline", "")
            score = row.get("predicted_hot_score", 0.0)
            title_to_score[title] = score

        # Add ML scores to articles
        scored_articles = []
        for article in articles:
            title = article.get("title", "")
            ml_score = title_to_score.get(title, 0.0)

            # Normalize score to 0-1 range (assuming model outputs 0-100 range)
            normalized_score = min(1.0, max(0.0, ml_score / 100.0))

            article_copy = article.copy()
            article_copy["ml_hot_score"] = normalized_score
            scored_articles.append(article_copy)

        return scored_articles

    def _fallback_scoring(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback scoring when ML model is not available"""
        log.info("Using fallback scoring for articles")

        scored_articles = []
        for article in articles:
            # Simple fallback based on title length and content
            title = article.get("title", "")
            content = article.get("content", "")

            # Basic heuristic: longer titles and content with keywords get higher scores
            title_length_score = min(1.0, len(title) / 100.0)
            content_length_score = min(1.0, len(content) / 1000.0)

            # Check for hot keywords
            hot_keywords = ["важн", "срочн", "кризис", "рост", "паден", "рекорд"]
            keyword_score = 0.0
            text_combined = (title + " " + content).lower()
            for keyword in hot_keywords:
                if keyword in text_combined:
                    keyword_score += 0.2

            fallback_score = min(1.0, (title_length_score + content_length_score + keyword_score) / 2.0)

            article_copy = article.copy()
            article_copy["ml_hot_score"] = fallback_score
            scored_articles.append(article_copy)

        return scored_articles


# Singleton instance
_ml_scorer: MLScorer = MLScorer()


def get_ml_scorer() -> MLScorer:
    """Get singleton ML scorer instance"""
    return _ml_scorer
