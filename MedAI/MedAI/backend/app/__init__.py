import logging
import threading
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    CORS(app, resources={r"/*": {"origins": "*"}})

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    from app.routes.health import health_bp
    from app.routes.chat import chat_bp
    from app.routes.predict import predict_bp
    from app.routes.documents import documents_bp
    from app.routes.rag import rag_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(rag_bp)

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Endpoint not found"}, 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return {"error": "Method not allowed"}, 405

    @app.errorhandler(500)
    def internal_error(e):
        return {"error": "Internal server error"}, 500

    from app.services.model_service import model_service
    from app.services.rag.vector_store import vector_store

    def _load_model():
        try:
            model_service.initialize()
            app.logger.info("BioMistral ready")
        except Exception as e:
            app.logger.error(f"Model failed to load: {e}", exc_info=True)

    def _load_rag_index():
        try:
            loaded = vector_store.load()
            if loaded:
                app.logger.info(
                    f"RAG index loaded: {vector_store.chunk_count} chunks "
                    f"from {vector_store.doc_count} documents"
                )
            else:
                app.logger.info("No RAG index found — upload via POST /documents/upload")
        except Exception as e:
            app.logger.error(f"RAG index load failed: {e}", exc_info=True)

    def _start_scheduler():
        from config import Config
        if Config.RAG_AUTO_SYNC:
            from app.services.rag.scheduler import scheduler
            scheduler.start(interval_hours=Config.RAG_SYNC_INTERVAL_HOURS)
            app.logger.info(f"Auto-sync enabled (every {Config.RAG_SYNC_INTERVAL_HOURS}h)")

    app.logger.info("Starting model loading in background...")
    threading.Thread(target=_load_model, daemon=True).start()

    _load_rag_index()
    _start_scheduler()

    return app
