"""
download_medical_docs.py — Downloads reputed medical literature for RAG knowledge base.

Sources:
1. PubMed Central — peer-reviewed clinical research
2. NCBI Bookshelf — free medical textbooks & clinical guides
3. Cochrane Library — systematic reviews (open access)
4. MedlinePlus / NIH — disease summaries & treatment guides
5. CDC MMWR — morbidity & mortality weekly reports
6. WHO — clinical management guidelines (via PMC)
7. NICE — UK clinical guidelines (via PMC)

Run: conda run -n rl python download_medical_docs.py
"""

import os
import re
import sys
import json
import time
import logging
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)

DOWNLOAD_DIR = os.path.join(BACKEND_DIR, "medical_documents")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({"User-Agent": "MedAI-RAG/1.0 (Medical Research)"})

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def save_text(filename: str, title: str, source: str, url: str, text: str) -> dict:
    if not text or len(text.strip()) < 200:
        return {"status": "skipped", "reason": "too short"}

    filepath = os.path.join(DOWNLOAD_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\n")
        f.write(f"Source: {source}\n")
        f.write(f"URL: {url}\n\n")
        f.write(text.strip())

    size_kb = os.path.getsize(filepath) / 1024
    return {"status": "ok", "filename": filename, "size_kb": round(size_kb, 1)}


def fetch_pmc_text(pmc_id: str) -> str | None:
    try:
        resp = session.get(
            f"{EUTILS}/efetch.fcgi",
            params={"db": "pmc", "id": pmc_id, "rettype": "text", "retmode": "text"},
            timeout=60,
        )
        if resp.ok and len(resp.text) > 300:
            text = resp.text
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r' {2,}', ' ', text)
            return text[:20000].strip()
        return None
    except Exception:
        return None


def search_pmc(query: str, max_results: int = 10) -> list[str]:
    try:
        resp = session.get(
            f"{EUTILS}/esearch.fcgi",
            params={"db": "pmc", "term": query, "retmax": max_results, "retmode": "json", "sort": "relevance"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        logger.error(f"PMC search failed: {e}")
        return []


def get_pmc_title(pmc_id: str) -> str:
    try:
        resp = session.get(
            f"{EUTILS}/esummary.fcgi",
            params={"db": "pmc", "id": pmc_id, "retmode": "json"},
            timeout=15,
        )
        if resp.ok:
            return resp.json().get("result", {}).get(pmc_id, {}).get("title", f"PMC{pmc_id}")
    except Exception:
        pass
    return f"PMC{pmc_id}"


def download_from_pmc(query: str, label: str, max_results: int = 10) -> list[dict]:
    logger.info(f"[{label}] Searching PMC: {query}")
    ids = search_pmc(query, max_results)
    results = []

    for pmc_id in ids:
        filename = f"pubmed_{pmc_id}.txt"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if os.path.exists(filepath):
            results.append({"status": "exists", "pmc_id": pmc_id})
            continue

        title = get_pmc_title(pmc_id)
        text = fetch_pmc_text(pmc_id)
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmc_id}/"
        result = save_text(filename, title, f"PubMed Central ({label})", url, text)
        result["pmc_id"] = pmc_id
        results.append(result)
        logger.info(f"  [{result['status']}] {title[:60]}...")
        time.sleep(0.5)

    ok = sum(1 for r in results if r["status"] == "ok")
    logger.info(f"[{label}] {ok}/{len(results)} downloaded")
    return results


def fetch_bookshelf_text(book_id: str) -> str | None:
    try:
        resp = session.get(
            f"https://www.ncbi.nlm.nih.gov/books/{book_id}/",
            timeout=30,
            headers={"Accept": "text/html"},
        )
        if not resp.ok:
            return None
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        body = soup.find("div", class_="body") or soup.find("article") or soup.find("main")
        if body:
            return body.get_text(separator="\n", strip=True)[:20000]
        return None
    except Exception:
        return None


BOOKSHELF_IDS = {
    "NBK279386": "WHO Guidelines on Pharmacological Treatment of Persisting Pain in Children",
    "NBK559276": "StatPearls — Pharmacology, Antibiotics",
    "NBK554585": "StatPearls — Hypertension",
    "NBK507837": "StatPearls — Type 2 Diabetes",
    "NBK441980": "StatPearls — Community Acquired Pneumonia",
    "NBK538162": "StatPearls — Tuberculosis",
    "NBK525962": "StatPearls — Malaria",
    "NBK519032": "StatPearls — COVID-19",
    "NBK482364": "StatPearls — Hepatitis B",
    "NBK507861": "StatPearls — Congestive Heart Failure",
    "NBK470448": "StatPearls — Myocardial Infarction",
    "NBK559141": "StatPearls — Asthma",
    "NBK499987": "StatPearls — Chronic Obstructive Pulmonary Disease",
    "NBK542189": "StatPearls — Stroke",
    "NBK557426": "StatPearls — Seizures",
    "NBK532896": "StatPearls — Sepsis",
    "NBK482471": "StatPearls — Anemia",
    "NBK538152": "StatPearls — Meningitis",
    "NBK559176": "StatPearls — Kidney Disease",
    "NBK499934": "StatPearls — Depression",
}


def download_bookshelf() -> list[dict]:
    logger.info(f"[NCBI Bookshelf] Downloading {len(BOOKSHELF_IDS)} clinical references...")
    results = []

    for book_id, title in BOOKSHELF_IDS.items():
        safe_name = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')[:60]
        filename = f"bookshelf_{safe_name}.txt"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        if os.path.exists(filepath):
            results.append({"status": "exists", "filename": filename})
            continue

        logger.info(f"  Fetching: {title[:60]}...")
        url = f"https://www.ncbi.nlm.nih.gov/books/{book_id}/"
        text = fetch_bookshelf_text(book_id)
        result = save_text(filename, title, "NCBI Bookshelf (StatPearls)", url, text)
        results.append(result)
        time.sleep(1)

    ok = sum(1 for r in results if r["status"] == "ok")
    logger.info(f"[Bookshelf] {ok}/{len(results)} downloaded")
    return results


MEDLINEPLUS_TOPICS = [
    "pneumonia", "hypertension", "diabetes", "tuberculosis", "malaria",
    "hepatitis", "asthma", "heartattack", "stroke", "copd",
    "meningitis", "sepsis", "anemia", "depression", "epilepsy",
    "heartfailure", "kidneydisease", "bronchitis", "sinusitis", "arthritis",
    "influenza", "chickenpox", "measles", "dengue", "typhoid",
]


def download_medlineplus() -> list[dict]:
    logger.info(f"[MedlinePlus] Downloading {len(MEDLINEPLUS_TOPICS)} disease summaries...")
    results = []

    for topic in MEDLINEPLUS_TOPICS:
        filename = f"medlineplus_{topic}.txt"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        if os.path.exists(filepath):
            results.append({"status": "exists", "filename": filename})
            continue

        try:
            url = f"https://medlineplus.gov/{topic}.html"
            resp = session.get(url, timeout=30)
            if not resp.ok:
                results.append({"status": "failed", "topic": topic})
                continue

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                tag.decompose()

            content = soup.find("div", id="mplus-content") or soup.find("main") or soup.find("article")
            if content:
                text = content.get_text(separator="\n", strip=True)[:15000]
                title_tag = soup.find("h1")
                title = title_tag.get_text(strip=True) if title_tag else topic.title()
                result = save_text(filename, title, "MedlinePlus (NIH)", url, text)
                results.append(result)
                logger.info(f"  [{result['status']}] {title[:50]}...")
            else:
                results.append({"status": "failed", "topic": topic})

            time.sleep(0.5)

        except Exception as e:
            results.append({"status": "failed", "topic": topic, "error": str(e)})

    ok = sum(1 for r in results if r["status"] == "ok")
    logger.info(f"[MedlinePlus] {ok}/{len(results)} downloaded")
    return results


MMWR_URLS = [
    ("https://www.cdc.gov/mmwr/preview/mmwrhtml/mm7110a1.htm", "CDC MMWR — COVID-19 Vaccine Effectiveness"),
    ("https://www.cdc.gov/mmwr/preview/mmwrhtml/mm7042a1.htm", "CDC MMWR — Antibiotic Resistance Threats"),
    ("https://www.cdc.gov/mmwr/preview/mmwrhtml/mm7218a1.htm", "CDC MMWR — Diabetes Statistics"),
    ("https://www.cdc.gov/mmwr/preview/mmwrhtml/mm7115a1.htm", "CDC MMWR — Hypertension Control"),
    ("https://www.cdc.gov/mmwr/preview/mmwrhtml/mm7045a1.htm", "CDC MMWR — Influenza Activity"),
]


def download_cdc_mmwr() -> list[dict]:
    logger.info(f"[CDC MMWR] Downloading {len(MMWR_URLS)} reports...")
    results = []

    for url, title in MMWR_URLS:
        safe_name = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')[:60]
        filename = f"cdc_mmwr_{safe_name}.txt"
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        if os.path.exists(filepath):
            results.append({"status": "exists", "filename": filename})
            continue

        try:
            resp = session.get(url, timeout=30)
            if not resp.ok:
                results.append({"status": "failed", "title": title})
                continue

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "header", "footer"]):
                tag.decompose()

            body = soup.find("div", {"id": "content"}) or soup.find("article") or soup.find("main")
            if body:
                text = body.get_text(separator="\n", strip=True)[:15000]
                result = save_text(filename, title, "CDC MMWR", url, text)
                results.append(result)
                logger.info(f"  [{result['status']}] {title[:50]}...")
            else:
                results.append({"status": "failed", "title": title})

            time.sleep(0.5)

        except Exception as e:
            results.append({"status": "failed", "title": title, "error": str(e)})

    ok = sum(1 for r in results if r["status"] == "ok")
    logger.info(f"[CDC MMWR] {ok}/{len(results)} downloaded")
    return results


WHO_PMC_QUERIES = [
    ("WHO malaria treatment guidelines artemisinin", "WHO Malaria Guidelines", 5),
    ("WHO tuberculosis treatment DOTS protocol", "WHO TB Guidelines", 5),
    ("WHO HIV antiretroviral treatment guidelines", "WHO HIV Guidelines", 5),
    ("WHO pneumonia clinical management children", "WHO Pneumonia Guidelines", 5),
    ("WHO cardiovascular disease prevention management", "WHO CVD Guidelines", 5),
    ("WHO diabetes type 2 management primary care", "WHO Diabetes Guidelines", 5),
    ("WHO essential medicines list formulary", "WHO Essential Medicines", 5),
    ("WHO infection prevention control guidelines healthcare", "WHO IPC Guidelines", 5),
    ("WHO emergency triage treatment ETAT guidelines", "WHO Emergency Care", 3),
    ("WHO surgical safety checklist perioperative care", "WHO Surgical Care", 3),
]


def download_who_via_pmc() -> list[dict]:
    logger.info(f"[WHO via PMC] Downloading {len(WHO_PMC_QUERIES)} guideline categories...")
    all_results = []

    for query, label, count in WHO_PMC_QUERIES:
        results = download_from_pmc(f"{query} AND (who[au] OR world health organization)", label, count)
        all_results.extend(results)
        time.sleep(1)

    return all_results


COCHRANE_QUERIES = [
    ("Cochrane systematic review antibiotic pneumonia treatment", "Cochrane Antibiotics", 5),
    ("Cochrane systematic review hypertension antihypertensive", "Cochrane Hypertension", 5),
    ("Cochrane systematic review diabetes metformin insulin", "Cochrane Diabetes", 5),
    ("Cochrane systematic review asthma corticosteroid inhaler", "Cochrane Asthma", 5),
    ("Cochrane systematic review statin cardiovascular prevention", "Cochrane Statins", 5),
    ("Cochrane systematic review anticoagulant atrial fibrillation", "Cochrane Anticoagulation", 3),
    ("Cochrane systematic review antidepressant depression", "Cochrane Depression", 3),
    ("Cochrane systematic review vaccine influenza efficacy", "Cochrane Vaccines", 3),
]


def download_cochrane() -> list[dict]:
    logger.info(f"[Cochrane via PMC] Downloading {len(COCHRANE_QUERIES)} review categories...")
    all_results = []

    for query, label, count in COCHRANE_QUERIES:
        results = download_from_pmc(f"{query} AND cochrane[au]", label, count)
        all_results.extend(results)
        time.sleep(1)

    return all_results


def main():
    print("=" * 60)
    print("MedAI Medical Document Downloader")
    print("=" * 60)
    print()

    total_results = {}

    # 1. NCBI Bookshelf (StatPearls — clinical textbooks)
    print("\n[1/7] NCBI Bookshelf (StatPearls Clinical References)")
    total_results["bookshelf"] = download_bookshelf()

    # 2. MedlinePlus (NIH disease summaries)
    print("\n[2/7] MedlinePlus (NIH Disease Summaries)")
    total_results["medlineplus"] = download_medlineplus()

    # 3. CDC MMWR reports
    print("\n[3/7] CDC MMWR Reports")
    total_results["cdc_mmwr"] = download_cdc_mmwr()

    # 4. WHO guidelines via PMC
    print("\n[4/7] WHO Clinical Guidelines (via PubMed Central)")
    total_results["who"] = download_who_via_pmc()

    # 5. Cochrane systematic reviews
    print("\n[5/7] Cochrane Systematic Reviews")
    total_results["cochrane"] = download_cochrane()

    # 6. Core clinical research (broad PMC queries)
    print("\n[6/7] Core Clinical Research (PubMed Central)")
    core_queries = [
        ("community acquired pneumonia treatment amoxicillin guidelines", "Pneumonia Treatment", 10),
        ("hypertension management first-line antihypertensive guidelines", "Hypertension Management", 10),
        ("diabetes mellitus type 2 metformin treatment guidelines", "Diabetes Treatment", 10),
        ("myocardial infarction STEMI NSTEMI treatment protocol", "Heart Attack Treatment", 5),
        ("stroke ischemic treatment thrombolysis guidelines", "Stroke Treatment", 5),
        ("sepsis management sepsis-3 surviving sepsis guidelines", "Sepsis Management", 5),
        ("tuberculosis treatment regimen rifampicin isoniazid protocol", "TB Treatment", 5),
        ("malaria treatment artemisinin combination therapy guidelines", "Malaria Treatment", 5),
        ("asthma management GINA guidelines inhaled corticosteroid", "Asthma Management", 5),
        ("COPD treatment bronchodilator guidelines GOLD protocol", "COPD Treatment", 5),
        ("hepatitis B treatment tenofovir entecavir antiviral guidelines", "Hepatitis B Treatment", 5),
        ("HIV antiretroviral therapy ART guidelines WHO protocol", "HIV Treatment", 5),
        ("depression treatment SSRI antidepressant guidelines", "Depression Treatment", 5),
        ("epilepsy seizure treatment antiepileptic drug guidelines", "Epilepsy Treatment", 5),
        ("chronic kidney disease CKD management nephrology guidelines", "CKD Management", 5),
        ("meningitis bacterial treatment antibiotic protocol", "Meningitis Treatment", 3),
        ("anemia iron deficiency treatment supplementation guidelines", "Anemia Treatment", 3),
        ("dengue fever management WHO guidelines supportive care", "Dengue Management", 3),
    ]

    all_core = []
    for query, label, count in core_queries:
        results = download_from_pmc(query, label, count)
        all_core.extend(results)
        time.sleep(0.5)
    total_results["core_research"] = all_core

    # 7. Emergency medicine & critical care
    print("\n[7/7] Emergency Medicine & Critical Care")
    emergency_queries = [
        ("emergency department triage guidelines protocol acute care", "Emergency Triage", 5),
        ("mechanical ventilation ARDS lung protective strategy guidelines", "Ventilation Guidelines", 3),
        ("cardiac arrest ACLS protocol advanced life support guidelines", "ACLS Protocol", 3),
        ("anaphylaxis treatment epinephrine guidelines emergency", "Anaphylaxis Treatment", 3),
        ("trauma management ATLS protocol initial assessment guidelines", "Trauma Management", 3),
    ]

    all_emergency = []
    for query, label, count in emergency_queries:
        results = download_from_pmc(query, label, count)
        all_emergency.extend(results)
        time.sleep(0.5)
    total_results["emergency"] = all_emergency

    # Summary
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)

    total_ok = 0
    total_exists = 0
    total_failed = 0

    for category, results in total_results.items():
        ok = sum(1 for r in results if r.get("status") == "ok")
        exists = sum(1 for r in results if r.get("status") == "exists")
        failed = sum(1 for r in results if r.get("status") in ("failed", "skipped"))
        total_ok += ok
        total_exists += exists
        total_failed += failed
        print(f"  {category}: {ok} new, {exists} existing, {failed} failed")

    all_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.txt')]
    total_size = sum(os.path.getsize(os.path.join(DOWNLOAD_DIR, f)) for f in all_files) / (1024 * 1024)

    print(f"\nTotal files in medical_documents/: {len(all_files)}")
    print(f"Total size: {total_size:.1f} MB")
    print(f"New downloads: {total_ok}")
    print(f"Already existed: {total_exists}")
    print(f"Failed: {total_failed}")

    # Save download manifest
    manifest = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_files": len(all_files),
        "total_size_mb": round(total_size, 1),
        "categories": {
            cat: {
                "ok": sum(1 for r in results if r.get("status") == "ok"),
                "exists": sum(1 for r in results if r.get("status") == "exists"),
                "failed": sum(1 for r in results if r.get("status") in ("failed", "skipped")),
            }
            for cat, results in total_results.items()
        },
    }

    manifest_path = os.path.join(DOWNLOAD_DIR, "_download_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest saved: {manifest_path}")
    print("\nNext step: Run POST /documents/ingest-folder to index into FAISS")


if __name__ == "__main__":
    main()
