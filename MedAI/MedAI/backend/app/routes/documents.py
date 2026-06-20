import os
import logging
import tempfile
from pathlib import Path
from flask import Blueprint, request, jsonify
from app.services.rag.retriever import (
    ingest_document,
    list_documents,
    delete_document,
    get_rag_stats,
    get_sources,
)
from app.services.rag.crawlers import crawler
from app.services.rag.scheduler import scheduler
from config import Config

logger = logging.getLogger(__name__)
documents_bp = Blueprint("documents", __name__)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv"}
DOCS_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    Config.MEDICAL_DOCS_DIR,
)


@documents_bp.route("/documents", methods=["GET"])
def get_documents():
    docs = list_documents()
    stats = get_rag_stats()

    folder_files = []
    if os.path.isdir(DOCS_FOLDER):
        folder_files = [
            f for f in os.listdir(DOCS_FOLDER)
            if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS
        ]

    return jsonify({
        "documents": docs,
        "stats": stats,
        "medical_documents_folder": os.path.abspath(DOCS_FOLDER),
        "files_in_folder": folder_files,
    }), 200


@documents_bp.route("/documents/upload", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Use multipart/form-data with key 'file'."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}"}), 400

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            file.save(tmp)
            tmp_path = tmp.name

        result = ingest_document(tmp_path, filename=file.filename)

        if result["status"] == "error":
            return jsonify({"error": result["error"]}), 400

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@documents_bp.route("/documents/ingest-folder", methods=["POST"])
def ingest_folder():
    if not os.path.isdir(DOCS_FOLDER):
        return jsonify({"error": f"Folder not found: {DOCS_FOLDER}"}), 404

    files = [
        f for f in os.listdir(DOCS_FOLDER)
        if os.path.splitext(f)[1].lower() in ALLOWED_EXTENSIONS
    ]

    if not files:
        return jsonify({"error": f"No supported files found in {DOCS_FOLDER}"}), 404

    results = []
    for filename in files:
        file_path = os.path.join(DOCS_FOLDER, filename)
        try:
            result = ingest_document(file_path, filename=filename)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to ingest {filename}: {e}")
            results.append({"status": "error", "filename": filename, "error": str(e)})

    ok_count = sum(1 for r in results if r.get("status") == "ok")
    dup_count = sum(1 for r in results if r.get("status") == "duplicate")
    err_count = sum(1 for r in results if r.get("status") == "error")

    return jsonify({
        "total_files": len(files),
        "ingested": ok_count,
        "duplicates": dup_count,
        "errors": err_count,
        "details": results,
    }), 200


@documents_bp.route("/documents/<doc_id>", methods=["DELETE"])
def remove_document(doc_id: str):
    result = delete_document(doc_id)
    if result["status"] == "not_found":
        return jsonify({"error": f"Document {doc_id} not found"}), 404
    return jsonify(result), 200


@documents_bp.route("/documents/sources", methods=["GET"])
def list_sources():
    sources = get_sources()
    return jsonify(sources), 200


@documents_bp.route("/documents/rag/status", methods=["GET"])
def rag_status():
    stats = get_rag_stats()
    scheduler_status = scheduler.status
    return jsonify({**stats, "scheduler": scheduler_status}), 200
