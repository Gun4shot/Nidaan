# Nidaan Backend — Flask + BioMistral + Gemini + RAG

Flask API backend for the Nidaan medical AI platform. Provides NLP chatbot, symptom prediction, medical diagnosis pipeline, and RAG-based document retrieval.

## Architecture

```
Patient Input → Gemini 2.5 Flash (enrichment) → RAG Retrieval → BioMistral 7B (reasoning) → Structured Response
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness probe — returns model status |
| POST | `/predict` | Symptom prediction — list symptoms → ranked conditions |
| POST | `/chat` | Medical chat (non-streaming) |
| POST | `/chat/stream` | Medical chat (SSE token streaming) |
| POST | `/diagnose` | Full CV→Gemini→BioMistral diagnosis pipeline |
| GET | `/documents` | List uploaded medical documents |
| POST | `/documents/upload` | Upload medical document for RAG |
| POST | `/rag/query` | Query RAG index directly |

## Quick Start

```bash
cd MedAI/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings (MODEL_PATH, GEMINI_API_KEY, etc.)
python run.py
```

## Configuration (.env)

```env
MODEL_PATH=BioMistral/BioMistral-7B
USE_4BIT=true
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
FLASK_PORT=5000
```

## Connecting to Frontend

The Next.js frontend (on `main` branch) connects to this backend at `http://localhost:5000`.

## Folder Structure

```
backend/
├── run.py                          ← Entry point
├── config.py                       ← Centralized config from .env
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py                 ← Flask app factory
│   ├── routes/
│   │   ├── health.py               ← GET /health
│   │   ├── chat.py                 ← POST /chat, /chat/stream
│   │   ├── predict.py              ← POST /predict
│   │   ├── diagnose.py             ← POST /diagnose
│   │   ├── documents.py            ← Document management
│   │   └── rag.py                  ← RAG query endpoints
│   ├── services/
│   │   ├── model_service.py        ← BioMistral loader (singleton)
│   │   ├── prompt_service.py       ← Prompt templates
│   │   ├── parser_service.py       ← LLM output → JSON parser
│   │   ├── gemini_service.py       ← Gemini context enrichment
│   │   └── rag/
│   │       ├── vector_store.py     ← FAISS dense retrieval
│   │       ├── bm25_store.py       ← BM25 sparse retrieval
│   │       ├── retriever.py        ← Hybrid search orchestrator
│   │       ├── reranker.py         ← Cross-encoder reranking
│   │       ├── document_loader.py  ← Document ingestion
│   │       └── scheduler.py        ← Auto-sync scheduler
│   └── models/
│       └── validators.py           ← Input validation
├── medical_documents/              ← PubMed articles for RAG
└── rag_index/                      ← Pre-built FAISS + BM25 index
```
