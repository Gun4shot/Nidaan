from flask import Blueprint, jsonify
from app.services.model_service import model_service

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    try:
        import torch
        cuda = torch.cuda.is_available()
    except Exception:
        cuda = False

    response = {
        "status": "ok",
        "llm": model_service.is_ready,
        "device": model_service.device if model_service.is_ready else "unknown",
        "cuda": cuda,
    }
    if model_service.load_error:
        response["llm_error"] = model_service.load_error

    return jsonify(response), 200
