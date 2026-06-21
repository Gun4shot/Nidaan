import os
import logging
from pathlib import Path

from app.services.rag.document_loader import extract_text, chunk_text, generate_doc_id, infer_source, _extract_disease_metadata
from app.services.rag import embedding_service
from app.services.rag.vector_store import vector_store
from app.services.rag.bm25_store import bm25_store
from app.services.rag.reranker import reranker_service
from config import Config

logger = logging.getLogger(__name__)


def ingest_document(file_path: str, filename: str = None) -> dict:
    if filename is None:
        filename = Path(file_path).name

    doc_id = generate_doc_id(file_path)

    existing_docs = vector_store.get_documents()
    if any(d["doc_id"] == doc_id for d in existing_docs):
        return {"status": "duplicate", "doc_id": doc_id, "filename": filename}

    raw_text, doc_metadata = extract_text(file_path)
    if not raw_text or len(raw_text.strip()) < 50:
        return {"status": "error", "error": "Document is empty or too short"}

    chunks = chunk_text(
        raw_text,
        chunk_size=Config.RAG_CHUNK_SIZE,
        chunk_overlap=Config.RAG_CHUNK_OVERLAP,
    )

    if not chunks:
        return {"status": "error", "error": "No valid chunks extracted"}

    embeddings = embedding_service.encode(chunks)

    source_info = infer_source(filename)
    disease_meta = _extract_disease_metadata(raw_text, filename)

    metadata = [
        {
            "doc_id": doc_id,
            "filename": filename,
            "chunk_index": i,
            "source": file_path,
            "source_org": source_info["organization"],
            "source_type": source_info["type"],
            "title": doc_metadata.get("title", filename),
            "doc_metadata": doc_metadata,
            "disease_names": disease_meta["disease_names"],
            "symptoms_mentioned": disease_meta["symptoms_mentioned"],
            "severity_classification": disease_meta["severity_classification"],
        }
        for i in range(len(chunks))
    ]

    vector_store.add_chunks(chunks, embeddings, metadata)
    vector_store.save()

    logger.info(f"Ingested '{filename}': {len(chunks)} chunks (source: {source_info['organization']})")
    return {
        "status": "ok",
        "doc_id": doc_id,
        "filename": filename,
        "chunks": len(chunks),
        "text_length": len(raw_text),
        "source": source_info,
    }


def _reciprocal_rank_fusion(
    dense_results: list[dict],
    sparse_results: list[dict],
    dense_weight: float = 0.6,
    sparse_weight: float = 0.4,
    k: int = 60,
) -> list[dict]:
    doc_scores: dict[str, dict] = {}

    for rank, result in enumerate(dense_results):
        text = result["text"]
        rrf_score = dense_weight / (k + rank + 1)
        if text in doc_scores:
            doc_scores[text]["score"] += rrf_score
        else:
            doc_scores[text] = {
                "text": text,
                "score": rrf_score,
                "metadata": result.get("metadata", {}),
                "dense_score": result.get("score", 0),
            }

    for rank, result in enumerate(sparse_results):
        text = result["text"]
        rrf_score = sparse_weight / (k + rank + 1)
        if text in doc_scores:
            doc_scores[text]["score"] += rrf_score
            doc_scores[text]["bm25_score"] = result.get("bm25_score", 0)
        else:
            doc_scores[text] = {
                "text": text,
                "score": rrf_score,
                "metadata": result.get("metadata", {}),
                "bm25_score": result.get("bm25_score", 0),
            }

    merged = sorted(doc_scores.values(), key=lambda x: x["score"], reverse=True)
    return merged


def retrieve_context(
    query: str,
    top_k: int = None,
    use_reranker: bool = None,
) -> list[dict]:
    if top_k is None:
        top_k = Config.RAG_TOP_K

    if use_reranker is None:
        use_reranker = Config.RAG_USE_RERANKER

    if vector_store.index is None or vector_store.chunk_count == 0:
        return []

    use_hybrid = Config.RAG_HYBRID_SEARCH and bm25_store.chunk_count > 0

    query_embedding = embedding_service.encode_query(query)
    dense_results = vector_store.search(query_embedding, top_k=top_k * 2)

    if use_hybrid:
        sparse_results = bm25_store.search(query, top_k=top_k * 2)
        results = _reciprocal_rank_fusion(
            dense_results,
            sparse_results,
            dense_weight=Config.RAG_DENSE_WEIGHT,
            sparse_weight=Config.RAG_BM25_WEIGHT,
        )
        logger.info(
            f"Hybrid search: {len(dense_results)} dense + {len(sparse_results)} sparse -> {len(results)} merged"
        )
    else:
        results = dense_results

    if use_reranker and results:
        results = reranker_service.rerank(query, results, top_k=top_k)
    else:
        results = [r for r in results if r.get("score", 0) >= Config.RAG_MIN_SCORE][:top_k]

    return results


def retrieve_and_format(query: str, top_k: int = None) -> tuple[str, list[dict]]:
    results = retrieve_context(query, top_k=top_k)

    if not results:
        return "", []

    parts = []
    for i, r in enumerate(results, 1):
        source = r["metadata"].get("filename", "unknown")
        org = r["metadata"].get("source_org", "")
        title = r["metadata"].get("title", source)
        score_key = "rerank_score" if "rerank_score" in r else "score"
        score = r[score_key]

        disease_names = r["metadata"].get("disease_names", [])
        symptoms = r["metadata"].get("symptoms_mentioned", [])
        severity = r["metadata"].get("severity_classification", "")

        meta_tags = []
        if disease_names:
            meta_tags.append(f"Diseases: {', '.join(disease_names)}")
        if symptoms:
            meta_tags.append(f"Symptoms: {', '.join(symptoms[:5])}")
        if severity and severity != "unknown":
            meta_tags.append(f"Severity: {severity}")

        meta_str = f"\n[Metadata: {' | '.join(meta_tags)}]" if meta_tags else ""

        parts.append(f"[{i}] Source: {org} — {title} (relevance: {score:.2f}){meta_str}\n{r['text']}")

    return "\n\n---\n\n".join(parts), results


def delete_document(doc_id: str) -> dict:
    removed = vector_store.delete_by_doc_id(doc_id)
    if removed > 0:
        vector_store.save()
        return {"status": "ok", "doc_id": doc_id, "chunks_removed": removed}
    return {"status": "not_found", "doc_id": doc_id}


def list_documents() -> list[dict]:
    return vector_store.get_documents()


def get_rag_stats() -> dict:
    return {
        "documents": vector_store.doc_count,
        "total_chunks": vector_store.chunk_count,
        "index_loaded": vector_store.index is not None,
        "embedding_model": Config.EMBEDDING_MODEL,
        "embedding_biomedical": embedding_service.is_biomedical,
        "reranker_model": Config.RERANKER_MODEL,
        "reranker_enabled": Config.RAG_USE_RERANKER,
        "hybrid_search_enabled": Config.RAG_HYBRID_SEARCH,
        "bm25_chunks": bm25_store.chunk_count,
        "sources": vector_store.get_sources_summary(),
    }


def get_sources() -> dict:
    return {
        "documents": vector_store.get_documents(),
        "sources_summary": vector_store.get_sources_summary(),
    }
