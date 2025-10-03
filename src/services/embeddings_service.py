import hashlib

import numpy as np
from sentence_transformers import SentenceTransformer

from src.core.config import Settings
from src.core.exceptions import EmbeddingException
from src.core.logging import get_logger
from src.infrastructure.redis.client import RedisClient

logger = get_logger(__name__)


class EmbeddingsService:
    def __init__(self, settings: Settings, redis_client: RedisClient):
        self.settings = settings
        self.redis = redis_client
        try:
            self.model = SentenceTransformer(settings.embedding_model)
        except Exception as e:
            raise EmbeddingException(f"Failed to load embedding model: {e}") from e

    async def get_embedding(self, text: str) -> np.ndarray:
        cache_key = self._get_cache_key(text)
        cached = await self.redis.get_embedding(cache_key)
        if cached is not None:
            logger.info("embedding_cache_hit", cache_key=cache_key)
            return cached

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            await self.redis.set_embedding(cache_key, embedding)
            logger.info("embedding_generated", cache_key=cache_key)
            return embedding
        except Exception as e:
            raise EmbeddingException(f"Failed to generate embedding: {e}") from e

    async def compute_similarity(self, text1: str, text2: str) -> float:
        emb1 = await self.get_embedding(text1)
        emb2 = await self.get_embedding(text2)
        return float(np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2)))

    def _get_cache_key(self, text: str) -> str:
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"embedding:{text_hash}"

