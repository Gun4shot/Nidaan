import logging
from app import create_app

logger = logging.getLogger(__name__)
app = create_app()

if __name__ == "__main__":
    from config import Config

    port = Config.FLASK_PORT
    debug = Config.FLASK_DEBUG

    logger.info(f"MedAI backend starting on port {port}")
    logger.info("Endpoints:")
    logger.info("  GET  /health")
    logger.info("  POST /predict")
    logger.info("  POST /chat")
    logger.info("  POST /chat/stream")
    logger.info("  GET  /documents")
    logger.info("  POST /documents/upload")
    logger.info("  POST /documents/ingest-folder")
    logger.info("  DEL  /documents/<doc_id>")
    logger.info("  GET  /documents/sources")
    logger.info("  GET  /documents/rag/status")
    logger.info("  POST /rag/query")
    logger.info("  POST /rag/sync")
    logger.info("  POST /rag/sync/start")
    logger.info("  POST /rag/sync/stop")
    logger.info("  GET  /rag/sync/status")
    logger.info("  GET  /rag/sources")
    logger.info("  POST /rag/pubmed/search")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        use_reloader=False,
        threaded=True,
    )
