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

    return jsonify({
        "status": "ok",
        "llm": model_service.is_ready,
        "device": model_service.device if model_service.is_ready else "unknown",
        "cuda": cuda,
    }), 200
