import logging
from flask import Blueprint, request, jsonify
from app.services.model_service import model_service
from app.services.prompt_service import build_symptom_prompt
from app.services.parser_service import parse_prediction_response
from app.services.rag.retriever import retrieve_and_format
from app.models.validators import validate_predict_request

logger = logging.getLogger(__name__)
predict_bp = Blueprint("predict", __name__)


@predict_bp.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)
    error, cleaned = validate_predict_request(data)
    if error:
        return jsonify({"error": error}), 400

    symptoms = cleaned["symptoms"]
    logger.info(f"Predict request | symptoms: {symptoms}")

    if not model_service.is_ready:
        return jsonify({"error": "Model is still loading. Try again shortly."}), 503

    query = " ".join(symptoms)
    rag_context = ""
    rag_results = []
    try:
        rag_context, rag_results = retrieve_and_format(query)
        if rag_context:
            logger.info(f"RAG context retrieved for predict ({len(rag_context)} chars)")
    except Exception as e:
        logger.warning(f"RAG retrieval failed (proceeding without): {e}")

    prompt = build_symptom_prompt(symptoms, rag_context=rag_context)

    try:
        raw_response = model_service.generate(
            prompt,
            max_new_tokens=600,
            temperature=0.4,
        )
    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        return jsonify({"error": f"Inference failed: {str(e)}"}), 500

    try:
        results = parse_prediction_response(raw_response)
    except Exception as e:
        logger.error(f"Parse error: {e}", exc_info=True)
        results = [{
            "name": "Analysis Result",
            "confidence": 0.75,
            "severity": "moderate",
            "description": raw_response[:400],
            "recommendations": ["Consult a healthcare provider for a proper diagnosis."],
        }]

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
        "symptoms": symptoms,
        "results": results,
        "raw": raw_response,
        "rag_used": bool(rag_context),
        "sources": sources,
    }), 200
