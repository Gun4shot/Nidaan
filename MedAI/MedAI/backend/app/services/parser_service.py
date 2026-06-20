import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

SEVERE_KEYWORDS = [
    "severe", "critical", "emergency", "urgent", "life-threatening",
    "hospitalization", "immediate", "serious",
]
MILD_KEYWORDS = [
    "mild", "minor", "self-limiting", "common cold", "rest",
    "home remedy", "over-the-counter",
]


def infer_severity(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in SEVERE_KEYWORDS):
        return "severe"
    if any(k in lower for k in MILD_KEYWORDS):
        return "mild"
    return "moderate"


def infer_confidence(rank: int) -> float:
    return {1: 0.87, 2: 0.65, 3: 0.42}.get(rank, 0.30)


def parse_prediction_response(raw_text: str) -> list[dict[str, Any]]:
    results = []
    sections = re.split(r'\n(?=\s*\*{0,2}\d+[\.\)]\*{0,2}\s)', raw_text.strip())

    for section in sections:
        if not section.strip():
            continue

        name_match = re.match(
            r'^\s*\*{0,2}\d+[\.\)]\*{0,2}\s*\*{0,2}([^\n\*]+)\*{0,2}',
            section.strip(),
        )
        if not name_match:
            continue

        condition_name = name_match.group(1).strip().rstrip(':').strip()
        if not condition_name or len(condition_name) < 3:
            continue

        body = section[name_match.end():].strip()

        severity_match = re.search(r'severity[:\s]+([a-z]+)', body, re.IGNORECASE)
        if severity_match:
            sev_raw = severity_match.group(1).lower()
            severity = sev_raw if sev_raw in ("mild", "moderate", "severe") else infer_severity(body)
        else:
            severity = infer_severity(body)

        desc_text = re.sub(r'severity[:\s]+\w+', '', body, flags=re.IGNORECASE)
        desc_text = re.sub(r'recommendations?[:\s]+.*', '', desc_text, flags=re.IGNORECASE | re.DOTALL)
        description = " ".join(desc_text.split()[:40]).strip()

        rec_match = re.search(
            r'recommendations?[:\s]+(.*?)(?=\n\s*\d+[\.\)]|\Z)',
            body, re.IGNORECASE | re.DOTALL,
        )
        recommendations = []
        if rec_match:
            raw_recs = re.split(r'[\n•\-\*]+', rec_match.group(1).strip())
            recommendations = [r.strip() for r in raw_recs if r.strip() and len(r.strip()) > 5][:4]

        results.append({
            "name": condition_name,
            "confidence": infer_confidence(len(results) + 1),
            "severity": severity,
            "description": description,
            "recommendations": recommendations,
        })

        if len(results) >= 3:
            break

    if not results:
        logger.warning("Parser found no structured conditions. Returning raw fallback.")
        results = [{
            "name": "Analysis Complete",
            "confidence": 0.70,
            "severity": "moderate",
            "description": raw_text[:300].strip(),
            "recommendations": ["Consult a healthcare provider for a proper diagnosis."],
        }]

    return results


def clean_chat_response(raw_text: str) -> str:
    text = re.sub(r'###\s*(Instruction|Response)[:\s]*', '', raw_text)
    text = re.sub(r'MedAI\s*:', '', text)
    text = re.sub(r'Patient\s*:', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
