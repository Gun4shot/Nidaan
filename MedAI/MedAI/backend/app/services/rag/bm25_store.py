import os
import re
import json
import logging
import pickle
import numpy as np
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


def tokenize_medical_text(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s\-]', ' ', text)
    tokens = text.split()
    tokens = [t for t in tokens if len(t) > 1]
    return tokens


class BM25Store:
    def __init__(self):
        self.corpus_tokens: list[list[str]] = []
        self.chunks: list[str] = []
        self.metadata: list[dict] = []
        self._bm25: BM25Okapi | None = None

    def _rebuild_index(self):
        if self.corpus_tokens:
            self._bm25 = BM25Okapi(self.corpus_tokens)
            logger.info(f"BM25 index rebuilt: {len(self.corpus_tokens)} documents")
        else:
            self._bm25 = None

    def add_chunks(
        self,
        new_chunks: list[str],
        new_metadata: list[dict],
    ):
        for chunk, meta in zip(new_chunks, new_metadata):
            tokens = tokenize_medical_text(chunk)
            self.corpus_tokens.append(tokens)
            self.chunks.append(chunk)
            self.metadata.append(meta)

        self._rebuild_index()

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        if self._bm25 is None or not self.chunks:
            return []

        query_tokens = tokenize_medical_text(query)
        scores = self._bm25.get_scores(query_tokens)

        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if idx < len(self.chunks) and scores[idx] > 0:
                results.append({
                    "text": self.chunks[idx],
                    "bm25_score": float(scores[idx]),
                    "metadata": self.metadata[idx] if idx < len(self.metadata) else {},
                })

        return results

    def delete_by_doc_id(self, doc_id: str) -> int:
        keep_mask = [m.get("doc_id") != doc_id for m in self.metadata]
        removed = sum(1 for m in self.metadata if m.get("doc_id") == doc_id)

        if removed == 0:
            return 0

        self.corpus_tokens = [t for t, keep in zip(self.corpus_tokens, keep_mask) if keep]
        self.chunks = [c for c, keep in zip(self.chunks, keep_mask) if keep]
        self.metadata = [m for m, keep in zip(self.metadata, keep_mask) if keep]

        self._rebuild_index()
        return removed

    def save(self, index_dir: str):
        bm25_path = os.path.join(index_dir, "bm25_corpus.pkl")
        chunks_path = os.path.join(index_dir, "bm25_chunks.json")
        meta_path = os.path.join(index_dir, "bm25_metadata.json")

        with open(bm25_path, "wb") as f:
            pickle.dump(self.corpus_tokens, f)

        with open(chunks_path, "w") as f:
            json.dump(self.chunks, f)

        with open(meta_path, "w") as f:
            json.dump(self.metadata, f)

        logger.info(f"BM25 index saved: {len(self.chunks)} chunks")

    def load(self, index_dir: str) -> bool:
        bm25_path = os.path.join(index_dir, "bm25_corpus.pkl")
        chunks_path = os.path.join(index_dir, "bm25_chunks.json")
        meta_path = os.path.join(index_dir, "bm25_metadata.json")

        if not all(os.path.exists(p) for p in [bm25_path, chunks_path, meta_path]):
            logger.info("No saved BM25 index found")
            return False

        try:
            with open(bm25_path, "rb") as f:
                self.corpus_tokens = pickle.load(f)
            with open(chunks_path, "r") as f:
                self.chunks = json.load(f)
            with open(meta_path, "r") as f:
                self.metadata = json.load(f)

            self._rebuild_index()
            logger.info(f"BM25 index loaded: {len(self.chunks)} chunks")
            return True
        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}")
            return False

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)


bm25_store = BM25Store()
