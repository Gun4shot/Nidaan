import os
import logging
from pathlib import Path

from app.services.rag.document_loader import extract_text, chunk_text, generate_doc_id, infer_source
from app.services.rag import embedding_service
from app.services.rag.vector_store import vector_store
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

    query_embedding = embedding_service.encode_query(query)
    results = vector_store.search(query_embedding, top_k=top_k * 2)

    if use_reranker and results:
        results = reranker_service.rerank(query, results, top_k=top_k)
    else:
        results = [r for r in results if r["score"] >= Config.RAG_MIN_SCORE][:top_k]

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

        parts.append(f"[{i}] Source: {org} — {title} (relevance: {score:.2f})\n{r['text']}")

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
        "sources": vector_store.get_sources_summary(),
    }


def get_sources() -> dict:
    return {
        "documents": vector_store.get_documents(),
        "sources_summary": vector_store.get_sources_summary(),
    }
