import os
import logging
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
        return cls._instance

    def _load_model(self):
        if self._model is not None:
            return

        from sentence_transformers import SentenceTransformer

        model_name = Config.EMBEDDING_MODEL
        device = Config.EMBEDDING_DEVICE

        logger.info(f"Loading embedding model: {model_name} on {device}")
        self._model = SentenceTransformer(model_name, device=device)
        self._dimension = self._model.get_embedding_dimension()
        logger.info(f"Embedding model loaded (dim={self._dimension})")

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._dimension

    def encode(self, texts: list[str], batch_size: int = 32):
        import numpy as np

        self._load_model()
        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return np.array(embeddings, dtype=np.float32)

    def encode_query(self, query: str):
        return self.encode([query])[0]

    @property
    def model_name(self) -> str:
        return Config.EMBEDDING_MODEL

    @property
    def is_biomedical(self) -> bool:
        biomedical_keywords = ["biobert", "pubmed", "biomed", "clinical", "med", "sapbert", "biovect"]
        model_lower = Config.EMBEDDING_MODEL.lower()
        return any(kw in model_lower for kw in biomedical_keywords)


embedding_service = EmbeddingService()
