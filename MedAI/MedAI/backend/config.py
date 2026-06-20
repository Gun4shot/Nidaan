import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Model ──────────────────────────────────────────
    MODEL_PATH = os.getenv(
        "MODEL_PATH",
        "BioMistral/BioMistral-7B",
    )
    USE_4BIT = os.getenv("USE_4BIT", "true").lower() == "true"
    USE_8BIT = os.getenv("USE_8BIT", "false").lower() == "true"
    DEVICE = os.getenv("DEVICE", "auto")

    # ── Generation defaults ────────────────────────────
    MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "512"))
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
    TOP_P = float(os.getenv("TOP_P", "0.9"))
    REPETITION_PENALTY = float(os.getenv("REPETITION_PENALTY", "1.1"))
    MAX_CONTEXT = 2048

    # ── Flask ──────────────────────────────────────────
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # ── RAG — Embeddings ───────────────────────────────
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

    # ── RAG — Chunking ─────────────────────────────────
    RAG_INDEX_DIR = os.getenv("RAG_INDEX_DIR", "rag_index")
    RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "500"))
    RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))

    # ── RAG — Retrieval ────────────────────────────────
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
    RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.3"))

    # ── RAG — Reranker ─────────────────────────────────
    RERANKER_MODEL = os.getenv(
        "RERANKER_MODEL",
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
    )
    RAG_USE_RERANKER = os.getenv("RAG_USE_RERANKER", "true").lower() == "true"

    # ── RAG — Scheduler ────────────────────────────────
    RAG_SYNC_INTERVAL_HOURS = int(os.getenv("RAG_SYNC_INTERVAL_HOURS", "24"))
    RAG_AUTO_SYNC = os.getenv("RAG_AUTO_SYNC", "false").lower() == "true"

    # ── RAG — Medical Documents Folder ─────────────────
    MEDICAL_DOCS_DIR = os.getenv("MEDICAL_DOCS_DIR", "medical_documents")
