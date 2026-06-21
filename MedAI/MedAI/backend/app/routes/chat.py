import logging
import json
from flask import Blueprint, request, jsonify, Response, stream_with_context
from app.services.model_service import model_service
from app.services.gemini_service import gemini_service
from app.services.prompt_service import build_chat_prompt
from app.services.parser_service import clean_chat_response, parse_prediction_response
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


def _has_symptoms(message: str) -> bool:
    symptom_keywords = [
        "pain", "ache", "fever", "cough", "nausea",
        "dizzy", "fatigue", "rash", "swelling", "bleeding",
        "headache", "vomit", "vomiting", "diarrhea", "numbness",
        "tired", "exhausted", "weakness", "weak", "no energy",
        "weight loss", "blurry", "blurred", "vision",
        "wound", "sore", "burning", "itching",
        "breathless", "breathing", "chest", "palpitation",
        "chills", "rigors", "sweating", "muscle", "joint",
    ]
    lower = message.lower()
    if any(kw in lower for kw in symptom_keywords):
        return True
    if len(message.split()) > 30:
        return True
    return False


def _extract_symptoms_from_message(message: str) -> list[str]:
    known_symptoms = [
        "fever", "high-grade fever", "low-grade fever",
        "headache", "severe headache", "mild headache",
        "vomiting", "nausea", "diarrhea",
        "cough", "dry cough", "wet cough",
        "fatigue", "extreme fatigue", "tiredness",
        "chills", "rigors", "sweating", "profuse sweating",
        "muscle ache", "muscle pain", "myalgia",
        "joint ache", "joint pain", "arthralgia",
        "abdominal pain", "stomach pain", "chest pain",
        "breathing difficulty", "shortness of breath", "dyspnea",
        "rash", "skin rash", "itching",
        "dizziness", "vertigo", "blurred vision",
        "sore throat", "runny nose", "nasal congestion",
        "weight loss", "loss of appetite", "anorexia",
        "dark urine", "jaundice", "yellowing skin",
        "back pain", "neck stiffness", "confusion",
        "insomnia", "anxiety", "depression",
        "constipation", "bloating", "heartburn",
        "frequent urination", "painful urination",
        "swelling", "edema", "numbness", "tingling",
        "palpitation", "irregular heartbeat",
        "wound", "sore", "burning sensation",
    ]

    lower = message.lower()
    found = []
    for symptom in known_symptoms:
        if symptom in lower:
            found.append(symptom)

    if not found:
        words = message.lower().replace(",", " ").replace(".", " ").split()
        generic = [
            "fever", "headache", "vomiting", "nausea", "diarrhea", "cough",
            "fatigue", "chills", "rash", "pain", "ache", "dizziness",
            "sweating", "weakness", "breathing", "bleeding",
        ]
        for w in words:
            if w in generic and w not in found:
                found.append(w)

    return found[:10]


@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    error, cleaned = validate_chat_request(data)
    if error:
        return jsonify({"error": error}), 400

    if not model_service.is_ready:
        error_msg = model_service.load_error or "Model is still loading. Try again shortly."
        return jsonify({"error": error_msg}), 503

    user_message = cleaned["message"]
    history = cleaned["history"]
    is_symptom_query = _has_symptoms(user_message)

    gemini_enrichment = ""
    if is_symptom_query and gemini_service.is_ready:
        try:
            history_text = ""
            if history:
                lines = []
                for turn in history[-4:]:
                    role = "Patient" if turn["role"] == "user" else "MedAI"
                    lines.append(f"{role}: {turn['content']}")
                history_text = "\n".join(lines)

            gemini_enrichment = gemini_service.enhance_symptoms(user_message, history_text)
            logger.info(f"Gemini enrichment: {len(gemini_enrichment)} chars")
        except Exception as e:
            logger.warning(f"Gemini enhancement failed (proceeding without): {e}")

    rag_context = ""
    rag_results = []
    if not is_symptom_query:
        rag_context, rag_results = _get_rag_context(user_message)

    prompt = build_chat_prompt(
        user_message=user_message,
        history=history,
        rag_context=rag_context,
        structured_data=cleaned,
        gemini_enrichment=gemini_enrichment,
    )
    logger.info(f"Prompt length: {len(prompt)} chars, symptom_query: {is_symptom_query}, gemini: {bool(gemini_enrichment)}")

    try:
        max_tokens = 1536 if is_symptom_query else 512
        temperature = 0.5 if is_symptom_query else 0.7
        raw = model_service.generate(prompt, max_new_tokens=max_tokens, temperature=temperature)
        logger.info(f"Raw model output ({len(raw)} chars): {raw[:300]}")
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

    response_text = clean_chat_response(raw, user_message)

    predictions = []
    if is_symptom_query:
        try:
            predictions = parse_prediction_response(raw)
        except Exception as e:
            logger.warning(f"Prediction parsing failed: {e}")

    if not response_text and predictions:
        response_text = _format_predictions_as_text(predictions)
    elif not response_text:
        response_text = raw.strip() or "I'm sorry, I couldn't generate a response. Please try rephrasing your symptoms."

    sources = []
    for r in rag_results:
        meta = r.get("metadata", {})
        sources.append({
            "filename": meta.get("filename", "unknown"),
            "organization": meta.get("source_org", "Unknown"),
            "title": meta.get("title", ""),
            "relevance": r.get("rerank_score", r.get("score", 0)),
        })

    result = {
        "response": response_text,
        "rag_used": bool(rag_context),
        "gemini_used": bool(gemini_enrichment),
        "sources": sources,
    }

    if predictions:
        result["predictions"] = predictions
        result["has_predictions"] = True

    return jsonify(result), 200


def _format_predictions_as_text(predictions: list) -> str:
    lines = []
    lines.append("Based on the symptoms presented, here are the likely conditions:\n")
    for i, pred in enumerate(predictions, 1):
        name = pred.get("name", "Unknown")
        confidence = pred.get("confidence", 0)
        severity = pred.get("severity", "moderate")
        desc = pred.get("description", "")
        lines.append(f"{i}. {name} (Confidence: {confidence:.0%})")
        if desc:
            lines.append(f"   {desc}")
        lines.append(f"   Severity: {severity.capitalize()}")
        recs = pred.get("recommendations", [])
        if recs:
            lines.append(f"   Recommendations: {'; '.join(recs[:2])}")
        lines.append("")
    return "\n".join(lines)


@chat_bp.route("/chat/stream", methods=["POST"])
def chat_stream():
    data = request.get_json(silent=True)
    error, cleaned = validate_chat_request(data)
    if error:
        return jsonify({"error": error}), 400

    if not model_service.is_ready:
        error_msg = model_service.load_error or "Model is still loading. Try again shortly."
        return jsonify({"error": error_msg}), 503

    user_message = cleaned["message"]
    history = cleaned["history"]

    rag_context, rag_results = _get_rag_context(user_message)

    prompt = build_chat_prompt(
        user_message=user_message,
        history=history,
        rag_context=rag_context,
        structured_data=cleaned,
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
