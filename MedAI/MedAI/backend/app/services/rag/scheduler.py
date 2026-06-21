import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class IngestionScheduler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._running = False
            cls._instance._thread = None
            cls._instance._last_sync = None
            cls._instance._sync_history = []
        return cls._instance

    def _run_sync(self):
        from app.services.rag.crawlers import crawler
        from app.services.rag.retriever import ingest_document

        while self._running:
            try:
                logger.info("Starting scheduled sync...")
                download_results = crawler.download_all()

                ingested = 0
                for category, items in download_results.get("results", {}).items():
                    for item in items:
                        if item.get("path") and item.get("status") == "downloaded":
                            try:
                                doc_result = ingest_document(
                                    item["path"],
                                    filename=item.get("filename", "unknown"),
                                )
                                if doc_result.get("status") == "ok":
                                    ingested += 1
                            except Exception as e:
                                logger.error(f"Failed to ingest {item.get('filename')}: {e}")

                self._last_sync = datetime.now().isoformat()
                self._sync_history.append({
                    "timestamp": self._last_sync,
                    "downloaded": download_results["summary"]["total_downloaded"],
                    "ingested": ingested,
                })

                if len(self._sync_history) > 50:
                    self._sync_history = self._sync_history[-50:]

                logger.info(f"Sync complete: {ingested} new documents ingested")

            except Exception as e:
                logger.error(f"Scheduled sync failed: {e}", exc_info=True)

            time.sleep(86400)

    def start(self, interval_hours: int = 24):
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_sync,
            daemon=True,
            name="rag-scheduler",
        )
        self._thread.start()
        logger.info(f"RAG scheduler started (sync every {interval_hours}h)")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("RAG scheduler stopped")

    def run_once(self) -> dict:
        from app.services.rag.crawlers import crawler
        from app.services.rag.retriever import ingest_document

        logger.info("Running one-time sync...")
        download_results = crawler.download_all()

        ingestion_results = []
        for category, items in download_results.get("results", {}).items():
            for item in items:
                if item.get("path") and item.get("status") == "downloaded":
                    try:
                        doc_result = ingest_document(
                            item["path"],
                            filename=item.get("filename", "unknown"),
                        )
                        ingestion_results.append(doc_result)
                    except Exception as e:
                        ingestion_results.append({
                            "status": "error",
                            "filename": item.get("filename"),
                            "error": str(e),
                        })

        self._last_sync = datetime.now().isoformat()

        ok = sum(1 for r in ingestion_results if r.get("status") == "ok")
        dup = sum(1 for r in ingestion_results if r.get("status") == "duplicate")
        err = sum(1 for r in ingestion_results if r.get("status") == "error")

        return {
            "download": download_results["summary"],
            "ingestion": {"ok": ok, "duplicates": dup, "errors": err},
            "details": ingestion_results,
            "timestamp": self._last_sync,
        }

    @property
    def status(self) -> dict:
        return {
            "running": self._running,
            "last_sync": self._last_sync,
            "sync_count": len(self._sync_history),
            "history": self._sync_history[-5:],
        }


scheduler = IngestionScheduler()
