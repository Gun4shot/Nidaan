import logging
from flask import Blueprint, request, jsonify
from app.services.rag.retriever import retrieve_context, retrieve_and_format
from app.services.rag.crawlers import crawler
from app.services.rag.scheduler import scheduler

logger = logging.getLogger(__name__)
rag_bp = Blueprint("rag", __name__)


@rag_bp.route("/rag/query", methods=["POST"])
def rag_query():
    data = request.get_json(silent=True)
    if not data or not data.get("query"):
        return jsonify({"error": "Field 'query' is required."}), 400

    query = data["query"].strip()
    top_k = data.get("top_k", 5)
    use_reranker = data.get("use_reranker", None)

    try:
        results = retrieve_context(query, top_k=top_k, use_reranker=use_reranker)
        formatted, raw_results = retrieve_and_format(query, top_k=top_k)
    except Exception as e:
        logger.error(f"RAG query error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "query": query,
        "results": results,
        "formatted_context": formatted,
        "num_results": len(results),
        "reranker_used": use_reranker if use_reranker is not None else True,
    }), 200


@rag_bp.route("/rag/sync", methods=["POST"])
def rag_sync():
    try:
        result = scheduler.run_once()
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Sync error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@rag_bp.route("/rag/sync/start", methods=["POST"])
def rag_sync_start():
    data = request.get_json(silent=True) or {}
    interval = data.get("interval_hours", 24)

    try:
        scheduler.start(interval_hours=interval)
        return jsonify({
            "status": "started",
            "interval_hours": interval,
            "message": "Background sync scheduler started",
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rag_bp.route("/rag/sync/stop", methods=["POST"])
def rag_sync_stop():
    scheduler.stop()
    return jsonify({"status": "stopped"}), 200


@rag_bp.route("/rag/sync/status", methods=["GET"])
def rag_sync_status():
    return jsonify(scheduler.status), 200


@rag_bp.route("/rag/sources", methods=["GET"])
def rag_sources():
    from app.services.rag.crawlers import MEDICAL_SEARCH_QUERIES

    categories = {}
    for cat, config in MEDICAL_SEARCH_QUERIES.items():
        categories[cat] = {
            "query": config["query"],
            "max_results": config["max_results"],
            "source_label": config["source_label"],
        }

    return jsonify({
        "source": "PubMed Central API",
        "categories": categories,
    }), 200


@rag_bp.route("/rag/pubmed/search", methods=["POST"])
def pubmed_search():
    data = request.get_json(silent=True)
    if not data or not data.get("query"):
        return jsonify({"error": "Field 'query' is required."}), 400

    query = data["query"].strip()
    max_results = data.get("max_results", 5)

    try:
        results = crawler.search_pubmed(query, max_results=max_results)
        return jsonify({
            "query": query,
            "results": results,
            "count": len(results),
        }), 200
    except Exception as e:
        logger.error(f"PubMed search error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
