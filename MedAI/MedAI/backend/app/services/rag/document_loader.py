import os
import re
import logging
import hashlib
from pathlib import Path
from typing import Optional

from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

DISEASE_SYMPTOM_MAP = {
    "malaria": {
        "symptoms": ["fever", "chills", "sweating", "headache", "nausea", "vomiting", "body aches", "fatigue", "cyclic fever", "plasmodium"],
        "severity": "severe",
        "disease_name": "Malaria",
    },
    "tuberculosis": {
        "symptoms": ["cough", "night sweats", "weight loss", "fever", "fatigue", "chest pain", "hemoptysis"],
        "severity": "severe",
        "disease_name": "Tuberculosis",
    },
    "pneumonia": {
        "symptoms": ["cough", "fever", "chills", "shortness of breath", "chest pain", "fatigue", "sputum"],
        "severity": "severe",
        "disease_name": "Pneumonia",
    },
    "hypertension": {
        "symptoms": ["headache", "dizziness", "blurred vision", "chest pain", "shortness of breath", "high blood pressure"],
        "severity": "moderate",
        "disease_name": "Hypertension",
    },
    "diabetes": {
        "symptoms": ["thirst", "frequent urination", "fatigue", "blurred vision", "weight loss", "slow healing", "hyperglycemia"],
        "severity": "moderate",
        "disease_name": "Diabetes Mellitus",
    },
    "covid": {
        "symptoms": ["fever", "cough", "shortness of breath", "fatigue", "loss of taste", "loss of smell", "sore throat"],
        "severity": "severe",
        "disease_name": "COVID-19",
    },
    "hepatitis": {
        "symptoms": ["jaundice", "fatigue", "abdominal pain", "nausea", "dark urine", "loss of appetite"],
        "severity": "moderate",
        "disease_name": "Hepatitis",
    },
    "dengue": {
        "symptoms": ["fever", "headache", "joint pain", "muscle pain", "rash", "bleeding", "platelet count"],
        "severity": "severe",
        "disease_name": "Dengue Fever",
    },
    "asthma": {
        "symptoms": ["wheezing", "shortness of breath", "chest tightness", "cough", "breathing difficulty"],
        "severity": "moderate",
        "disease_name": "Asthma",
    },
    "stroke": {
        "symptoms": ["sudden weakness", "numbness", "confusion", "trouble speaking", "vision loss", "severe headache", "face drooping"],
        "severity": "critical",
        "disease_name": "Stroke",
    },
    "sepsis": {
        "symptoms": ["fever", "rapid heart rate", "rapid breathing", "confusion", "low blood pressure", "organ failure"],
        "severity": "critical",
        "disease_name": "Sepsis",
    },
    "meningitis": {
        "symptoms": ["stiff neck", "fever", "headache", "nausea", "confusion", "sensitivity to light", "rash"],
        "severity": "critical",
        "disease_name": "Meningitis",
    },
    "heart failure": {
        "symptoms": ["shortness of breath", "fatigue", "swollen legs", "rapid heartbeat", "persistent cough", "edema"],
        "severity": "severe",
        "disease_name": "Heart Failure",
    },
    "myocardial infarction": {
        "symptoms": ["chest pain", "arm pain", "shortness of breath", "nausea", "sweating", "dizziness", "crushing pain"],
        "severity": "critical",
        "disease_name": "Myocardial Infarction",
    },
    "epilepsy": {
        "symptoms": ["seizures", "convulsions", "loss of consciousness", "staring spells", "confusion"],
        "severity": "moderate",
        "disease_name": "Epilepsy",
    },
    "ckd": {
        "symptoms": ["fatigue", "swelling", "urination changes", "nausea", "shortness of breath", "kidney disease"],
        "severity": "severe",
        "disease_name": "Chronic Kidney Disease",
    },
    "anemia": {
        "symptoms": ["fatigue", "weakness", "pale skin", "shortness of breath", "dizziness", "cold hands"],
        "severity": "moderate",
        "disease_name": "Anemia",
    },
    "depression": {
        "symptoms": ["sadness", "loss of interest", "fatigue", "sleep changes", "appetite changes", "concentration", "hopelessness"],
        "severity": "moderate",
        "disease_name": "Depression",
    },
    "copd": {
        "symptoms": ["shortness of breath", "chronic cough", "wheezing", "chest tightness", "sputum production"],
        "severity": "severe",
        "disease_name": "COPD",
    },
}


def _extract_disease_metadata(text: str, filename: str) -> dict:
    lower_text = text.lower()
    lower_filename = filename.lower()

    matched_diseases = []
    all_symptoms = set()

    for disease_key, info in DISEASE_SYMPTOM_MAP.items():
        if disease_key in lower_filename or disease_key in lower_text[:2000]:
            matched_diseases.append(info["disease_name"])
            for symptom in info["symptoms"]:
                if symptom in lower_text:
                    all_symptoms.add(symptom)

    for disease_key, info in DISEASE_SYMPTOM_MAP.items():
        symptom_count = sum(1 for s in info["symptoms"] if s in lower_text)
        if symptom_count >= 3 and info["disease_name"] not in matched_diseases:
            matched_diseases.append(info["disease_name"])

    severity = "unknown"
    for disease_key, info in DISEASE_SYMPTOM_MAP.items():
        if info["disease_name"] in matched_diseases:
            if info["severity"] == "critical":
                severity = "critical"
                break
            elif info["severity"] == "severe" and severity != "critical":
                severity = "severe"
            elif info["severity"] == "moderate" and severity in ("unknown",):
                severity = "moderate"

    return {
        "disease_names": matched_diseases[:5],
        "symptoms_mentioned": sorted(all_symptoms)[:10],
        "severity_classification": severity,
    }


def extract_text_from_pdf(file_path: str) -> tuple[str, dict]:
    reader = PdfReader(file_path)
    pages = []
    metadata = {}

    if reader.metadata:
        metadata["title"] = reader.metadata.get("/Title", "")
        metadata["author"] = reader.metadata.get("/Author", "")
        metadata["subject"] = reader.metadata.get("/Subject", "")
        metadata["creator"] = reader.metadata.get("/Creator", "")

    metadata["total_pages"] = len(reader.pages)

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(text.strip())

    return "\n\n".join(pages), metadata


def extract_text_from_txt(file_path: str) -> tuple[str, dict]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    metadata = {}
    lines = text.split("\n")
    for line in lines[:10]:
        if line.lower().startswith("title:"):
            metadata["title"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("source:"):
            metadata["source"] = line.split(":", 1)[1].strip()

    return text, metadata


def extract_text(file_path: str) -> tuple[str, dict]:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".txt", ".md", ".csv"):
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def clean_medical_text(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
    text = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1-\2', text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 2048,
    chunk_overlap: int = 400,
) -> list[str]:
    text = clean_medical_text(text)

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{para}" if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())

            if len(para) > chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current_chunk = ""
                for sent in sentences:
                    if len(current_chunk) + len(sent) + 1 <= chunk_size:
                        current_chunk = f"{current_chunk} {sent}" if current_chunk else sent
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sent
            else:
                current_chunk = para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    if chunk_overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-chunk_overlap:]
            overlapped.append(f"{prev_tail} ... {chunks[i]}")
        chunks = overlapped

    return [c for c in chunks if len(c) > 20]


def generate_doc_id(file_path: str) -> str:
    name = Path(file_path).stem
    size = os.path.getsize(file_path)
    raw = f"{name}_{size}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def infer_source(filename: str) -> dict:
    lower = filename.lower()
    if lower.startswith("who_"):
        return {"organization": "WHO", "type": "clinical_guideline"}
    elif lower.startswith("cdc_"):
        return {"organization": "CDC", "type": "clinical_protocol"}
    elif lower.startswith("pubmed_"):
        return {"organization": "PubMed", "type": "research_article"}
    elif lower.startswith("icd_"):
        return {"organization": "WHO-ICD", "type": "disease_classification"}
    elif lower.startswith("cochrane_"):
        return {"organization": "Cochrane", "type": "systematic_review"}
    elif lower.startswith("statpearl"):
        return {"organization": "NCBI-StatPearls", "type": "clinical_textbook"}
    elif lower.startswith("medlineplus_"):
        return {"organization": "MedlinePlus-NIH", "type": "patient_information"}
    else:
        return {"organization": "Unknown", "type": "medical_document"}
