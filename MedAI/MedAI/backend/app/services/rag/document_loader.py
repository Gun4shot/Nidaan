import os
import re
import logging
import hashlib
from pathlib import Path
from typing import Optional

from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)


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
    chunk_size: int = 500,
    chunk_overlap: int = 100,
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
    else:
        return {"organization": "Unknown", "type": "medical_document"}
