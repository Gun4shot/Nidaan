import logging
import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from app.services.model_service import model_service
from app.services.prompt_service import build_chat_prompt
from app.services.parser_service import clean_chat_response
from app.services.rag.retriever import retrieve_and_format
from app.models.validators import validate_chat_request

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


def _get_rag_context(message: str) -> tuple[str, list]:
    try:
        ctx, results = retrieve_and_format(message)
        if ctx:
            logger.info(f"RAG context retrieved ({len(ctx)} chars, {len(results)} chunks)")
        return ctx, results
    except Exception as e:
        logger.warning(f"RAG retrieval failed (proceeding without): {e}")
        return "", []


@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    error, cleaned = validate_chat_request(data)
    if error:
        return jsonify({"error": error}), 400

    if not model_service.is_ready:
        return jsonify({"error": "Model is still loading. Try again shortly."}), 503

    rag_context, rag_results = _get_rag_context(cleaned["message"])

    prompt = build_chat_prompt(
        user_message=cleaned["message"],
        history=cleaned["history"],
        rag_context=rag_context,
    )

    try:
        raw = model_service.generate(prompt, max_new_tokens=512, temperature=0.7)
        response_text = clean_chat_response(raw)
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

    sources = []
    for r in rag_results:
        meta = r.get("metadata", {})
        sources.append({
            "filename": meta.get("filename", "unknown"),
            "organization": meta.get("source_org", "Unknown"),
            "title": meta.get("title", ""),
            "relevance": r.get("rerank_score", r.get("score", 0)),
        })

    return jsonify({
        "response": response_text,
        "rag_used": bool(rag_context),
        "sources": sources,
    }), 200


@chat_bp.route("/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json(silent=True)
    error, cleaned = validate_chat_request(data)
    if error:
        return jsonify({"error": error}), 400

    if not model_service.is_ready:
        return jsonify({"error": "Model is still loading. Try again shortly."}), 503

    rag_context, rag_results = _get_rag_context(cleaned["message"])

    prompt = build_chat_prompt(
        user_message=cleaned["message"],
        history=cleaned["history"],
        rag_context=rag_context,
    )

    sources = []
    for r in rag_results:
        meta = r.get("metadata", {})
        sources.append({
            "filename": meta.get("filename", "unknown"),
            "organization": meta.get("source_org", "Unknown"),
            "title": meta.get("title", ""),
        })

    def generate_sse():
        try:
            if sources:
                yield f"data: {json.dumps({'sources': sources})}\n\n"

            for token in model_service.generate_stream(prompt, temperature=0.7):
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield f"data: {json.dumps({'token': '[END]'})}\n\n"

    return Response(
        stream_with_context(generate_sse()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )
