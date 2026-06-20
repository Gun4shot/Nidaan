import os
import json
import logging
import faiss
import numpy as np
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self):
        self.index = None
        self.chunks: list[str] = []
        self.metadata: list[dict] = []
        self._index_path = Config.RAG_INDEX_DIR
        os.makedirs(self._index_path, exist_ok=True)

    def _index_file(self) -> str:
        return os.path.join(self._index_path, "faiss.index")

    def _metadata_file(self) -> str:
        return os.path.join(self._index_path, "metadata.json")

    def _chunks_file(self) -> str:
        return os.path.join(self._index_path, "chunks.json")

    def _sources_file(self) -> str:
        return os.path.join(self._index_path, "sources.json")

    def build_index(self, embeddings: np.ndarray):
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        logger.info(f"FAISS index built: {self.index.ntotal} vectors, dim={dimension}")

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[dict]:
        if self.index is None or self.index.ntotal == 0:
            return []

        query = query_embedding.reshape(1, -1).astype(np.float32)
        scores, indices = self.index.search(query, min(top_k * 2, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            results.append({
                "text": self.chunks[idx],
                "score": float(score),
                "metadata": self.metadata[idx] if idx < len(self.metadata) else {},
            })
        return results

    def add_chunks(
        self,
        new_chunks: list[str],
        new_embeddings: np.ndarray,
        new_metadata: list[dict],
    ):
        if self.index is None:
            self.build_index(new_embeddings)
        else:
            self.index.add(new_embeddings.astype(np.float32))

        self.chunks.extend(new_chunks)
        self.metadata.extend(new_metadata)
        logger.info(f"Added {len(new_chunks)} chunks. Total: {self.index.ntotal}")

    def delete_by_doc_id(self, doc_id: str) -> int:
        keep_mask = [m.get("doc_id") != doc_id for m in self.metadata]
        removed = sum(1 for m in self.metadata if m.get("doc_id") == doc_id)

        if removed == 0:
            return 0

        kept_embeddings = []
        if self.index is not None and self.index.ntotal > 0:
            all_embeddings = faiss.rev_swig_ptr(
                self.index.get_xb(), self.index.ntotal * self.index.d
            ).reshape(self.index.ntotal, self.index.d)
            kept_embeddings = all_embeddings[keep_mask]

        self.chunks = [c for c, keep in zip(self.chunks, keep_mask) if keep]
        self.metadata = [m for m, keep in zip(self.metadata, keep_mask) if keep]

        if kept_embeddings:
            self.index = faiss.IndexFlatIP(self.index.d)
            self.index.add(kept_embeddings.astype(np.float32))
        else:
            self.index = None

        logger.info(f"Deleted {removed} chunks for doc_id={doc_id}")
        return removed

    def save(self):
        if self.index is not None:
            faiss.write_index(self.index, self._index_file())

        with open(self._chunks_file(), "w") as f:
            json.dump(self.chunks, f)

        with open(self._metadata_file(), "w") as f:
            json.dump(self.metadata, f)

        sources = self.get_documents()
        with open(self._sources_file(), "w") as f:
            json.dump(sources, f, indent=2)

        logger.info(f"Index saved: {len(self.chunks)} chunks")

    def load(self) -> bool:
        index_path = self._index_file()
        chunks_path = self._chunks_file()
        meta_path = self._metadata_file()

        if not all(os.path.exists(p) for p in [index_path, chunks_path, meta_path]):
            logger.info("No saved index found")
            return False

        try:
            self.index = faiss.read_index(index_path)
            with open(chunks_path, "r") as f:
                self.chunks = json.load(f)
            with open(meta_path, "r") as f:
                self.metadata = json.load(f)
            logger.info(f"Index loaded: {len(self.chunks)} chunks")
            return True
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False

    @property
    def doc_count(self) -> int:
        return len(set(m.get("doc_id", "") for m in self.metadata))

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def get_documents(self) -> list[dict]:
        docs = {}
        for m in self.metadata:
            doc_id = m.get("doc_id", "unknown")
            if doc_id not in docs:
                docs[doc_id] = {
                    "doc_id": doc_id,
                    "filename": m.get("filename", "unknown"),
                    "chunk_count": 0,
                    "source_org": m.get("source_org", "Unknown"),
                    "source_type": m.get("source_type", "medical_document"),
                }
            docs[doc_id]["chunk_count"] += 1
        return list(docs.values())

    def get_sources_summary(self) -> dict:
        orgs = {}
        for m in self.metadata:
            org = m.get("source_org", "Unknown")
            if org not in orgs:
                orgs[org] = {"count": 0, "documents": set()}
            orgs[org]["count"] += 1
            orgs[org]["documents"].add(m.get("filename", "unknown"))

        return {
            org: {
                "chunk_count": info["count"],
                "document_count": len(info["documents"]),
                "documents": list(info["documents"]),
            }
            for org, info in orgs.items()
        }


vector_store = VectorStore()
