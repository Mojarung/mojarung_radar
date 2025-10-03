"""Faiss-based deduplication service using embeddings"""
import os
import pickle
import uuid
from pathlib import Path
from typing import Optional, Tuple, List
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from src.core.config import get_settings
from src.core.logging_config import log

settings = get_settings()


class DedupService:
    """Service for managing Faiss index and similarity search"""

    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        self.index: Optional[faiss.IndexFlatIP] = None
        self.id_to_dedup_group: dict = {}
        self.index_path = Path(settings.faiss_index_path)
        self.threshold = settings.dedup_similarity_threshold
        
        self._load_or_create_index()

    def _load_or_create_index(self):
        """Load existing index or create a new one"""
        self.index_path.mkdir(parents=True, exist_ok=True)
        index_file = self.index_path / "faiss_index.bin"
        mapping_file = self.index_path / "id_mapping.pkl"

        if index_file.exists() and mapping_file.exists():
            try:
                self.index = faiss.read_index(str(index_file))
                with open(mapping_file, "rb") as f:
                    self.id_to_dedup_group = pickle.load(f)
                log.info(f"Loaded Faiss index with {self.index.ntotal} vectors")
            except Exception as e:
                log.warning(f"Failed to load index: {e}. Creating new index.")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        """Create a new Faiss index"""
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.id_to_dedup_group = {}
        log.info(f"Created new Faiss index (dimension: {self.embedding_dim})")

    def save_index(self):
        """Save the current index and mappings to disk"""
        try:
            index_file = self.index_path / "faiss_index.bin"
            mapping_file = self.index_path / "id_mapping.pkl"
            
            faiss.write_index(self.index, str(index_file))
            with open(mapping_file, "wb") as f:
                pickle.dump(self.id_to_dedup_group, f)
            
            log.info(f"Saved Faiss index with {self.index.ntotal} vectors")
        except Exception as e:
            log.error(f"Failed to save index: {e}")

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        embedding = self.embedding_model.encode(text, normalize_embeddings=True)
        return embedding.astype('float32')

    def find_duplicate(
        self, text: str, article_id: uuid.UUID
    ) -> Tuple[bool, Optional[uuid.UUID]]:
        """
        Check if text is a duplicate of existing articles.
        
        Returns:
            (is_duplicate, dedup_group_id)
        """
        if self.index.ntotal == 0:
            # No articles in index yet
            return False, None

        embedding = self.generate_embedding(text)
        embedding = np.expand_dims(embedding, axis=0)

        # Search for nearest neighbor
        distances, indices = self.index.search(embedding, k=1)
        
        if len(distances[0]) > 0:
            similarity = float(distances[0][0])
            nearest_idx = int(indices[0][0])
            
            log.debug(f"Similarity score: {similarity:.4f} (threshold: {self.threshold})")
            
            if similarity >= self.threshold:
                # Found a duplicate
                dedup_group = self.id_to_dedup_group.get(nearest_idx)
                log.info(f"Article {article_id} is duplicate (similarity: {similarity:.4f})")
                return True, dedup_group

        return False, None

    def add_article(
        self, text: str, article_id: uuid.UUID, dedup_group: uuid.UUID
    ):
        """Add article embedding to the index"""
        embedding = self.generate_embedding(text)
        embedding = np.expand_dims(embedding, axis=0)
        
        current_idx = self.index.ntotal
        self.index.add(embedding)
        self.id_to_dedup_group[current_idx] = dedup_group
        
        log.debug(f"Added article {article_id} to index (total: {self.index.ntotal})")
        
        # Periodic save every 100 articles
        if self.index.ntotal % 100 == 0:
            self.save_index()


# Singleton instance
_dedup_service: Optional[DedupService] = None


def get_dedup_service() -> DedupService:
    """Get singleton dedup service instance"""
    global _dedup_service
    if _dedup_service is None:
        _dedup_service = DedupService()
    return _dedup_service

