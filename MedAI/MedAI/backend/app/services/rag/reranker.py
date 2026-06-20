import logging
from sentence_transformers import CrossEncoder
from config import Config

logger = logging.getLogger(__name__)


class RerankerService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._model = None
        return cls._instance

    def _load_model(self):
        if self._model is not None:
            return

        model_name = Config.RERANKER_MODEL
        logger.info(f"Loading reranker: {model_name}")
        self._model = CrossEncoder(model_name, max_length=512)
        logger.info("Reranker loaded")

    def rerank(
        self,
        query: str,
        passages: list[dict],
        top_k: int = None,
    ) -> list[dict]:
        if not passages:
            return []

        if top_k is None:
            top_k = Config.RAG_TOP_K

        self._load_model()

        pairs = [[query, p["text"]] for p in passages]
        scores = self._model.predict(pairs)

        for i, score in enumerate(scores):
            passages[i]["rerank_score"] = float(score)

        passages.sort(key=lambda x: x["rerank_score"], reverse=True)

        return passages[:top_k]


reranker_service = RerankerService()
