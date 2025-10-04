"""FastText-based news classifier for financial relevance"""
from typing import Dict, Any, Optional, List
from huggingface_hub import hf_hub_download
import fasttext
from src.core.logging_config import log


class FastTextClassifierPipeline:
    """FastText classifier pipeline mimicking HuggingFace interface"""
    
    def __init__(self, model_path: str):
        self.model = fasttext.load_model(model_path)
        log.info(f"Loaded FastText model from {model_path}")
    
    def __call__(self, texts):
        """Classify text(s)"""
        # Handle both single string and list of strings
        if isinstance(texts, str):
            texts = [texts]
        
        results = []
        for text in texts:
            # Clean text: remove newlines and extra spaces
            text = text.replace('\n', ' ').replace('\r', ' ').strip()
            
            # Get the top prediction from the model
            prediction = self.model.predict(text)
            # Clean up the label and get the score
            label = prediction[0][0].replace("__label__", "")
            score = float(prediction[1][0])
            results.append({"label": label, "score": score})
        
        # If only one text was passed, return a single result
        return results[0] if len(results) == 1 else results


class FastTextNewsClassifier:
    """Fast classifier for financial news using FastText"""
    
    # Financial categories from the model
    FINANCIAL_CATEGORIES = {
        'economy',      # Экономика
        'stock',        # Акции/биржа
        'business',     # Бизнес
        'finance',      # Финансы
        'technology',   # Технологии (часто связаны с бизнесом)
    }
    
    def __init__(self, model_name: str = "data-silence/fasttext-rus-news-classifier"):
        self.model_name = model_name
        self.classifier = None
        self._load_model()
    
    def _load_model(self):
        """Download and load FastText model from HuggingFace"""
        try:
            log.info(f"Downloading FastText model: {self.model_name}")
            model_file = hf_hub_download(
                repo_id=self.model_name,
                filename="fasttext_news_classifier.bin"
            )
            self.classifier = FastTextClassifierPipeline(model_file)
            log.info("FastText model loaded successfully")
        except Exception as e:
            log.error(f"Failed to load FastText model: {e}")
            raise
    
    def is_financial(self, label: str, score: float, min_score: float = 0.5) -> bool:
        """
        Check if the predicted category is financial.
        
        Args:
            label: Predicted category
            score: Prediction confidence
            min_score: Minimum confidence threshold
        
        Returns:
            True if financial and confident enough
        """
        # Economy category - always accept regardless of score!
        if label == 'economy':
            return True
        
        # Other financial categories - check threshold
        return label in self.FINANCIAL_CATEGORIES and score >= min_score
    
    def classify_article(
        self,
        title: str,
        content_preview: str = "",
        min_score: float = 0.5
    ) -> Dict[str, Any]:
        """
        Classify single article.
        
        Args:
            title: Article title
            content_preview: Article preview/snippet
            min_score: Minimum confidence threshold
        
        Returns:
            Classification result dict
        """
        # Combine title and full content for better classification
        if content_preview:
            # Clean newlines before classification
            text = f"{title} {content_preview}".replace('\n', ' ').replace('\r', ' ').strip()
        else:
            text = title.replace('\n', ' ').replace('\r', ' ').strip()
        
        # Log what we're classifying
        log.debug(
            f"Classifying text (len={len(text)}): title='{title[:50]}...', "
            f"content_len={len(content_preview)}"
        )
        
        try:
            result = self.classifier(text)
            
            is_relevant = self.is_financial(result['label'], result['score'], min_score)
            
            classification = {
                'is_relevant': is_relevant,
                'confidence': result['score'],
                'category': result['label'],
                'reason': f"FastText classified as '{result['label']}' with score {result['score']:.3f}"
            }
            
            log.debug(
                f"Classified: '{title[:50]}...' -> "
                f"category={result['label']}, score={result['score']:.3f}, "
                f"relevant={is_relevant}"
            )
            
            return classification
            
        except Exception as e:
            log.error(f"Classification failed for '{title[:50]}...': {e}")
            # Fallback: mark as relevant to not lose articles
            return {
                'is_relevant': True,
                'confidence': 0.5,
                'category': 'unknown',
                'reason': f'Classification failed: {str(e)}'
            }
    
    def batch_classify(
        self,
        articles: List[Dict[str, Any]],
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Classify multiple articles efficiently.
        
        Args:
            articles: List of article dicts with 'title' and optionally 'overview'
            min_score: Minimum confidence threshold
        
        Returns:
            List of relevant articles with classification info
        """
        classified = []
        
        for article in articles:
            title = article.get('title', '')
            content_preview = article.get('overview', '') or article.get('content_preview', '')
            
            # Classify
            classification = self.classify_article(title, content_preview, min_score)
            article['classification'] = classification
            
            # Keep relevant articles
            if classification['is_relevant']:
                # Log economy articles specially
                if classification['category'] == 'economy':
                    log.info(
                        f"✓ Economy: '{title[:60]}...' "
                        f"(score={classification['confidence']:.3f})"
                    )
                classified.append(article)
            else:
                log.debug(
                    f"✗ Filtered out: '{title[:50]}...' "
                    f"(category={classification['category']}, "
                    f"score={classification['confidence']:.3f})"
                )
        
        log.info(
            f"FastText classified {len(articles)} articles -> "
            f"{len(classified)} relevant ({len(classified)/len(articles)*100:.1f}%)"
        )
        
        return classified


# Singleton instance
_fasttext_classifier: Optional[FastTextNewsClassifier] = None


def get_fasttext_classifier() -> FastTextNewsClassifier:
    """Get singleton FastText classifier instance"""
    global _fasttext_classifier
    if _fasttext_classifier is None:
        _fasttext_classifier = FastTextNewsClassifier()
    return _fasttext_classifier

