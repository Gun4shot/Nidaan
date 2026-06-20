import os
import re
import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

PUBMED_SEARCH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

MEDICAL_SEARCH_QUERIES = {
    "who_guidelines": {
        "query": "WHO guidelines treatment protocol clinical management",
        "max_results": 10,
        "source_label": "WHO",
    },
    "cdc_protocols": {
        "query": "CDC prevention treatment recommendations disease control",
        "max_results": 10,
        "source_label": "CDC",
    },
    "pneumonia": {
        "query": "community acquired pneumonia treatment guidelines antibiotic",
        "max_results": 5,
        "source_label": "PubMed",
    },
    "hypertension": {
        "query": "hypertension management treatment guidelines antihypertensive",
        "max_results": 5,
        "source_label": "PubMed",
    },
    "diabetes": {
        "query": "diabetes mellitus type 2 treatment guidelines management",
        "max_results": 5,
        "source_label": "PubMed",
    },
    "tuberculosis": {
        "query": "tuberculosis treatment WHO guidelines DOTS regimen",
        "max_results": 5,
        "source_label": "WHO",
    },
    "malaria": {
        "query": "malaria treatment artemisinin WHO guidelines plasmodium",
        "max_results": 5,
        "source_label": "WHO",
    },
    "covid19": {
        "query": "COVID-19 clinical management treatment WHO guidelines",
        "max_results": 5,
        "source_label": "WHO",
    },
    "hepatitis": {
        "query": "hepatitis B treatment antiviral tenofovir guidelines",
        "max_results": 5,
        "source_label": "PubMed",
    },
    "cardiovascular": {
        "query": "cardiovascular disease prevention treatment guidelines AHA ACC",
        "max_results": 5,
        "source_label": "PubMed",
    },
}


class MedicalCrawler:
    def __init__(self, download_dir: str = "medical_documents"):
        self.download_dir = os.path.abspath(download_dir)
        os.makedirs(self.download_dir, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MedAI-RAG-Crawler/1.0 (Medical Research Bot)",
        })

    def search_pubmed(self, query: str, max_results: int = 5) -> list[dict]:
        try:
            search_resp = self.session.get(
                f"{PUBMED_SEARCH_API}/esearch.fcgi",
                params={
                    "db": "pmc",
                    "term": query,
                    "retmax": max_results,
                    "retmode": "json",
                    "sort": "relevance",
                },
                timeout=30,
            )
            search_resp.raise_for_status()
            id_list = search_resp.json().get("esearchresult", {}).get("idlist", [])

            if not id_list:
                logger.info(f"No PubMed results for: {query}")
                return []

            results = []
            for pmc_id in id_list:
                try:
                    summary_resp = self.session.get(
                        f"{PUBMED_SEARCH_API}/esummary.fcgi",
                        params={"db": "pmc", "id": pmc_id, "retmode": "json"},
                        timeout=30,
                    )
                    if not summary_resp.ok:
                        continue

                    summary = summary_resp.json().get("result", {}).get(pmc_id, {})
                    title = summary.get("title", f"PMC Article {pmc_id}")

                    article_text = self._fetch_pmc_fulltext(pmc_id)
                    if not article_text or len(article_text) < 200:
                        continue

                    filename = f"pubmed_pmc{pmc_id}.txt"
                    file_path = os.path.join(self.download_dir, filename)

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(f"Title: {title}\n")
                        f.write(f"Source: PubMed Central (PMC{pmc_id})\n")
                        f.write(f"URL: https://pubmed.ncbi.nlm.nih.gov/{pmc_id}/\n\n")
                        f.write(article_text)

                    results.append({
                        "source": "PubMed",
                        "title": title,
                        "pmc_id": pmc_id,
                        "filename": filename,
                        "status": "downloaded",
                        "path": file_path,
                        "size_kb": os.path.getsize(file_path) / 1024,
                    })

                except Exception as e:
                    logger.error(f"Failed to process PMC{pmc_id}: {e}")

            return results

        except Exception as e:
            logger.error(f"PubMed search failed for '{query}': {e}")
            return []

    def _fetch_pmc_fulltext(self, pmc_id: str) -> str | None:
        try:
            resp = self.session.get(
                f"{PUBMED_SEARCH_API}/efetch.fcgi",
                params={"db": "pmc", "id": pmc_id, "rettype": "text", "retmode": "text"},
                timeout=60,
            )
            if resp.ok and len(resp.text) > 200:
                text = resp.text
                text = re.sub(r'<[^>]+>', '', text)
                text = re.sub(r'\n{3,}', '\n\n', text)
                text = re.sub(r' {2,}', ' ', text)
                return text[:15000].strip()
            return None
        except Exception:
            return None

    def download_category(self, category: str) -> list[dict]:
        if category not in MEDICAL_SEARCH_QUERIES:
            logger.error(f"Unknown category: {category}")
            return []

        config = MEDICAL_SEARCH_QUERIES[category]
        logger.info(f"Searching PubMed for: {category} ({config['query']})")

        results = self.search_pubmed(config["query"], config["max_results"])

        for r in results:
            r["category"] = category
            r["configured_source"] = config["source_label"]

        return results

    def download_all(self) -> dict:
        logger.info("Starting full medical document download from PubMed Central...")

        all_results = {}
        total_downloaded = 0
        total_failed = 0

        for category, config in MEDICAL_SEARCH_QUERIES.items():
            logger.info(f"  Category: {category}")
            results = self.search_pubmed(config["query"], config["max_results"])

            for r in results:
                r["category"] = category
                r["configured_source"] = config["source_label"]

            all_results[category] = results
            ok = sum(1 for r in results if r["status"] == "downloaded")
            total_downloaded += ok
            total_failed += len(results) - ok

        return {
            "results": all_results,
            "summary": {
                "categories": len(MEDICAL_SEARCH_QUERIES),
                "total_downloaded": total_downloaded,
                "total_failed": total_failed,
            },
        }


crawler = MedicalCrawler()
