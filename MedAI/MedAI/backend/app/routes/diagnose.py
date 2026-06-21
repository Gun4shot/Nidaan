import re
import json
import logging
from flask import Blueprint, request, jsonify
from app.services.model_service import model_service
from app.services.gemini_service import gemini_service
from app.services.rag.retriever import retrieve_and_format

logger = logging.getLogger(__name__)
diagnose_bp = Blueprint("diagnose", __name__)


@diagnose_bp.route("/diagnose", methods=["POST"])
def diagnose():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    age = data.get("age")
    gender = data.get("gender")
    cv_predictions = data.get("cv_predictions")

    if age is None:
        return jsonify({"error": "Field 'age' is required."}), 400
    if not gender:
        return jsonify({"error": "Field 'gender' is required."}), 400
    if not cv_predictions or not isinstance(cv_predictions, list):
        return jsonify({"error": "Field 'cv_predictions' is required (list of {label, confidence})."}), 400

    for i, pred in enumerate(cv_predictions):
        if not pred.get("label"):
            return jsonify({"error": f"cv_predictions[{i}].label is required."}), 400
        if "confidence" not in pred:
            return jsonify({"error": f"cv_predictions[{i}].confidence is required."}), 400

    if not gemini_service.is_ready:
        return jsonify({
            "error": "GEMINI_API_KEY not configured. Get a free key at "
                     "https://aistudio.google.com/apikey and add it to .env"
        }), 503

    if not model_service.is_ready:
        error_msg = model_service.load_error or "BioMistral is still loading. Try again shortly."
        return jsonify({"error": error_msg}), 503

    try:
        logger.info(f"Stage 2: Gemini enrichment for age={age}, gender={gender}, labels={len(cv_predictions)}")
        furnished_prompt = gemini_service.enrich(age, gender, cv_predictions)
        logger.info(f"Stage 2 complete: {len(furnished_prompt)} chars")
    except Exception as e:
        logger.error(f"Gemini enrichment failed: {e}", exc_info=True)
        return jsonify({"error": f"Gemini enrichment failed: {str(e)}"}), 500

    try:
        labels_query = " ".join(p["label"] for p in cv_predictions)
        rag_context, rag_results = retrieve_and_format(labels_query)
        if rag_context:
            logger.info(f"RAG context retrieved: {len(rag_context)} chars")
            furnished_prompt = _inject_rag_context(furnished_prompt, rag_context)
    except Exception as e:
        logger.warning(f"RAG retrieval failed (proceeding without): {e}")
        rag_results = []

    try:
        logger.info("Stage 3: BioMistral reasoning")
        raw_response = model_service.generate(
            furnished_prompt,
            max_new_tokens=1024,
            temperature=0.2,
        )
        logger.info(f"Stage 3 complete: {len(raw_response)} chars")
    except Exception as e:
        logger.error(f"BioMistral inference failed: {e}", exc_info=True)
        return jsonify({"error": f"BioMistral inference failed: {str(e)}"}), 500

    result = _parse_diagnosis_json(raw_response)

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
        "status": "success",
        "pipeline": {
            "stage_1": "CV Model — disease label detection",
            "stage_2": "Gemini 2.5 Flash — context enrichment",
            "stage_3": "BioMistral 7B 4-bit — medical reasoning",
        },
        "result": result,
        "rag_used": bool(rag_context),
        "sources": sources,
        "gemini_prompt_length": len(furnished_prompt),
    }), 200


@diagnose_bp.route("/diagnose/enrich", methods=["POST"])
def diagnose_enrich_only():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    age = data.get("age")
    gender = data.get("gender")
    cv_predictions = data.get("cv_predictions")

    if not gemini_service.is_ready:
        return jsonify({
            "error": "GEMINI_API_KEY not configured."
        }), 503

    try:
        furnished_prompt = gemini_service.enrich(age, gender, cv_predictions)
        return jsonify({
            "status": "success",
            "furnished_prompt": furnished_prompt,
            "prompt_length": len(furnished_prompt),
        }), 200
    except Exception as e:
        logger.error(f"Gemini enrichment failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


def _inject_rag_context(prompt: str, rag_context: str) -> str:
    if "</enriched_medical_context>" in prompt:
        return prompt.replace(
            "</enriched_medical_context>",
            f"\n\nRAG RETRIEVED CONTEXT (from PubMed medical literature):\n{rag_context}\n\n</enriched_medical_context>"
        )

    if "</reasoning_task>" in prompt:
        return prompt.replace(
            "</reasoning_task>",
            f"\n\nRAG RETRIEVED CONTEXT:\n{rag_context}\n\n</reasoning_task>"
        )

    return f"{prompt}\n\nRAG RETRIEVED CONTEXT:\n{rag_context}"


def _parse_diagnosis_json(raw_text: str) -> dict:
    cleaned = raw_text.strip()

    json_match = re.search(r'\{[\s\S]*\}', cleaned)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse BioMistral output as JSON, returning raw")
        return {
            "raw_output": raw_text[:2000],
            "parse_error": "Could not parse as structured JSON",
        }
