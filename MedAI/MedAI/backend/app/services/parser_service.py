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


def _extract_confidence_score(text: str) -> float | None:
    patterns = [
        r'confidence[:\s]+(\d{1,3})\s*%',
        r'confidence[:\s]+([0-9]*\.?[0-9]+)',
        r'score[:\s]+([0-9]*\.?[0-9]+)',
        r'likelihood[:\s]+([0-9]*\.?[0-9]+)',
        r'(\d{1,3})\s*%',
        r'\(([0-9]*\.?[0-9]+)\)',
        r'([0-9]*\.?[0-9]+)\s*(?:out of|/)\s*1',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            if "%" in pattern and 0 <= val <= 100:
                return val / 100.0
            if 0 <= val <= 1:
                return val
            if 1 < val <= 100:
                return val / 100.0
    return None


def _extract_cot_sections(raw_text: str) -> dict:
    sections = {}
    step_patterns = [
        (r'STEP\s*1[^\n]*SYMPTOM\s*ANALYSIS[:\s]*(.*?)(?=STEP\s*2|$)', 'symptom_analysis'),
        (r'STEP\s*2[^\n]*(?:LITERATURE|MATCHING)[:\s]*(.*?)(?=STEP\s*3|$)', 'literature_matching'),
        (r'STEP\s*3[^\n]*DIFFERENTIAL\s*DIAGNOSIS[:\s]*(.*?)(?=STEP\s*4|$)', 'differential_diagnosis'),
        (r'STEP\s*4[^\n]*SEVERITY\s*ASSESSMENT[:\s]*(.*?)(?=STEP\s*5|$)', 'severity_assessment'),
        (r'STEP\s*5[^\n]*RECOMMENDATIONS?[:\s]*(.*?)(?=$)', 'recommendations'),
    ]
    for pattern, key in step_patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.DOTALL)
        if match:
            sections[key] = match.group(1).strip()
    return sections


def parse_prediction_response(raw_text: str) -> list[dict[str, Any]]:
    structured = _extract_structured_predictions(raw_text)
    if structured:
        return structured

    cot_sections = _extract_cot_sections(raw_text)
    if cot_sections.get('differential_diagnosis'):
        return _parse_cot_response(raw_text, cot_sections)

    legacy = _parse_legacy_response(raw_text)
    if legacy and legacy[0].get("name") != "Analysis Complete":
        return legacy

    nl_extracted = _extract_conditions_from_natural_language(raw_text)
    if nl_extracted:
        return nl_extracted

    return legacy


def _extract_structured_predictions(raw_text: str) -> list[dict[str, Any]]:
    results = []

    numbered_pattern = re.compile(
        r'(\d+)\.\s*'
        r'([A-Za-z][\w\s\-\(\)]+?)'
        r'\s*[—–\-]\s*'
        r'[Cc]onfidence[:\s]*(\d{1,3})\s*%',
        re.MULTILINE
    )

    matches = list(numbered_pattern.finditer(raw_text))
    if len(matches) >= 2:
        severity_text = ""
        sev_match = re.search(r'Severity[:\s]*(Mild|Moderate|Severe|Critical)', raw_text, re.IGNORECASE)
        if sev_match:
            severity_text = sev_match.group(1).lower()

        recs = _extract_numbered_recommendations(raw_text)

        for i, match in enumerate(matches):
            name = match.group(2).strip()
            confidence = int(match.group(3)) / 100.0

            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
            block = raw_text[start:end].strip()

            justification = ""
            just_lines = [l.strip() for l in block.split('\n') if l.strip() and not l.strip().startswith(('Severity', 'Recommendation', 'Assessment'))]
            if just_lines:
                justification = just_lines[0][:200]

            severity = severity_text if severity_text else infer_severity(block)

            condition_recs = []
            if i == 0 and len(recs) >= 1:
                condition_recs = recs[:2]
            elif i == 1 and len(recs) >= 3:
                condition_recs = recs[2:3]

            results.append({
                "name": name,
                "confidence": confidence,
                "severity": severity,
                "description": justification or f"Clinical assessment based on presented symptoms",
                "recommendations": condition_recs if condition_recs else ["Consult a healthcare provider for proper evaluation"],
            })

        return results

    alt_pattern = re.compile(
        r'(?:Diagnosis|Condition|Differential)\s*(\d+)[:\.\s]*'
        r'([A-Za-z][\w\s\-\(\)]+?)'
        r'(?:\s*[—–\-]\s*[Cc]onfidence[:\s]*(\d{1,3})\s*%)?',
        re.IGNORECASE | re.MULTILINE
    )
    alt_matches = list(alt_pattern.finditer(raw_text))
    if len(alt_matches) >= 2:
        sev_match = re.search(r'Severity[:\s]*(Mild|Moderate|Severe|Critical)', raw_text, re.IGNORECASE)
        severity_text = sev_match.group(1).lower() if sev_match else ""
        recs = _extract_numbered_recommendations(raw_text)

        for i, match in enumerate(alt_matches):
            name = match.group(2).strip()
            conf_str = match.group(3)
            confidence = int(conf_str) / 100.0 if conf_str else infer_confidence(i + 1)

            start = match.end()
            end = alt_matches[i + 1].start() if i + 1 < len(alt_matches) else len(raw_text)
            block = raw_text[start:end].strip()

            severity = severity_text if severity_text else infer_severity(block)

            results.append({
                "name": name,
                "confidence": confidence,
                "severity": severity,
                "description": block[:200].strip() or f"Clinical assessment based on presented symptoms",
                "recommendations": recs[i:i+1] if i < len(recs) else ["Consult a healthcare provider"],
            })

        return results

    return []


def _extract_numbered_recommendations(raw_text: str) -> list[str]:
    recs = []
    rec_section = re.search(r'Recommendations?:\s*\n((?:\d+\..*\n?)+)', raw_text, re.IGNORECASE)
    if rec_section:
        for line in rec_section.group(1).strip().split('\n'):
            cleaned = re.sub(r'^\s*\d+\.\s*', '', line).strip()
            if cleaned and len(cleaned) > 5:
                recs.append(cleaned)
    return recs


def _extract_conditions_from_natural_language(raw_text: str) -> list[dict[str, Any]]:
    known_conditions = [
        "malaria", "tuberculosis", "pneumonia", "meningitis",
        "dengue", "typhoid", "hepatitis", "covid-19",
        "influenza", "bronchitis", "asthma", "copd",
        "appendicitis", "cholera", "measles",
        "urinary tract infection", "sepsis",
        "gastroenteritis", "gastritis", "pancreatitis",
        "encephalitis", "pericarditis", "endocarditis",
        "diabetes", "hypertension", "anemia",
        "pulmonary embolism", "deep vein thrombosis",
        "heart failure", "myocardial infarction", "stroke",
        "brain tumor", "subarachnoid hemorrhage",
        "cerebral aneurysm", "heat stroke",
        "lung cancer", "lung malignancy",
        "chronic bronchitis", "emphysema", "pleural effusion",
        "dehydration", "allergic reaction", "anaphylaxis",
        "costochondritis", "anxiety", "panic attack",
        "pneumoconiosis", "occupational asthma",
        "interstitial lung disease", "pulmonary fibrosis",
        "precordial catch syndrome", "gerd", "acid reflux",
        "musculoskeletal pain", "fibromyalgia",
    ]

    lower = raw_text.lower()

    penalty_patterns = [
        r"other\s+(?:potential\s+)?(?:diagnos|condition)s?\s+(?:include|are)",
        r"(?:less|rarely|unlikely|differential)\s+(?:include|are)",
        r"also\s+(?:consider|mentioned)",
        r"(?:must|should)\s+(?:also\s+)?rule\s+out",
        r"other\s+possibilities",
    ]
    penalty_ranges = []
    for pat in penalty_patterns:
        for m in re.finditer(pat, lower):
            end = lower.find(".", m.end())
            if end == -1:
                end = min(m.end() + 200, len(lower))
            penalty_ranges.append((m.start(), end))

    boost_patterns = [
        (r"(?:most\s+likely|primary|leading|consistent\s+with|suggestive\s+of|indicative\s+of)\s+(?:diagnosis\s+(?:is|of)\s+)?", 0.20),
        (r"(?:likely|probable|suspected)\s+(?:diagnosis\s+(?:is|of)\s+)?", 0.15),
        (r"(?:concerning\s+for|raises?\s+concern\s+for|compatible\s+with)\s+", 0.10),
    ]
    boost_ranges = []
    for pat, boost_val in boost_patterns:
        for m in re.finditer(pat, lower):
            end = lower.find(".", m.end())
            if end == -1:
                end = min(m.end() + 100, len(lower))
            boost_ranges.append((m.start(), end, boost_val))

    found_conditions = []
    for condition in known_conditions:
        for m in re.finditer(re.escape(condition), lower):
            pos = m.start()

            in_penalty = any(s <= pos <= e for s, e in penalty_ranges)

            boost = 0.0
            for bs, be, bv in boost_ranges:
                if bs <= pos <= be:
                    boost = max(boost, bv)

            found_conditions.append((condition, pos, in_penalty, boost))

    if not found_conditions:
        return []

    scored = []
    for condition, pos, in_penalty, boost in found_conditions:
        sentence_start = max(0, lower.rfind(".", 0, pos))
        sentence_end = lower.find(".", pos)
        if sentence_end == -1:
            sentence_end = len(lower)
        sentence = lower[sentence_start:sentence_end]

        base_score = 0.40
        if in_penalty:
            base_score = 0.15
        base_score += boost

        if any(w in sentence for w in ["consistent with", "suggestive of", "indicative of"]):
            base_score += 0.15
        if any(w in sentence for w in ["diagnosis", "most likely", "primary"]):
            base_score += 0.10
        if any(w in sentence for w in ["unlikely", "less likely", "ruled out"]):
            base_score -= 0.20

        base_score = max(0.10, min(0.92, base_score))
        scored.append((condition, base_score, sentence.strip()))

    scored.sort(key=lambda x: -x[1])

    seen = set()
    unique = []
    for condition, score, sentence in scored:
        canonical = condition.replace("-", " ").strip()
        if canonical not in seen:
            seen.add(canonical)
            unique.append((condition, score, sentence))

    severity = infer_severity(raw_text)

    results = []
    for condition, confidence, sentence in unique[:3]:
        name = condition.title()
        if name == "Covid-19":
            name = "COVID-19"
        if name == "Gerd":
            name = "GERD (Gastroesophageal Reflux Disease)"

        desc = sentence[:200] if sentence else "Clinical assessment based on presented symptoms"

        results.append({
            "name": name,
            "confidence": round(confidence, 2),
            "severity": severity,
            "description": desc,
            "recommendations": ["Consult a healthcare provider for proper evaluation and testing."],
        })

    return results


def _extract_condition_context(raw_text: str, condition: str) -> str:
    sentences = re.split(r'[.!?]\s+', raw_text)
    for sentence in sentences:
        if condition.lower() in sentence.lower():
            return sentence.strip()[:200]
    return f"Clinical assessment based on presented symptoms"


def _parse_cot_response(raw_text: str, sections: dict) -> list[dict[str, Any]]:
    results = []
    dd_text = sections.get('differential_diagnosis', '')

    condition_blocks = re.split(r'\n\s*(?=\*{0,2}\d+[\.\)]\*{0,2}\s)', dd_text.strip())
    if len(condition_blocks) <= 1:
        condition_blocks = re.split(r'\n\s*(?=\*{0,2}(?:Condition|Diagnosis|Differential)\s*\d*)', dd_text.strip(), flags=re.IGNORECASE)
    if len(condition_blocks) <= 1:
        condition_blocks = re.split(r'\n\s*(?=\*{0,2}[A-Z][a-z]+(?:\s+[A-Za-z]+)*\s*[:\-—])', dd_text.strip())

    severity_text = sections.get('severity_assessment', '')
    overall_severity = infer_severity(severity_text)

    recs_text = sections.get('recommendations', '')
    all_recommendations = []
    for line in recs_text.split('\n'):
        line = re.sub(r'^\s*[\d\.\)\-•*]+\s*', '', line).strip()
        if line and len(line) > 5:
            all_recommendations.append(line)

    for block in condition_blocks:
        block = block.strip()
        if not block or len(block) < 10:
            continue

        first_line = block.split('\n')[0].strip()

        name_match = re.match(
            r'^\s*\*{0,2}\d+[\.\)]\*{0,2}\s*\*{0,2}(.+?)\*{0,2}\s*$',
            first_line,
        )
        if name_match:
            raw_name = name_match.group(1).strip()
        else:
            raw_name = re.sub(r'^\*{0,2}(?:Condition|Diagnosis|Differential)\s*\d*[:\.\s]*\*{0,2}', '', first_line, flags=re.IGNORECASE).strip()

        condition_name = re.split(r'\s*\(confidence[:\s]', raw_name, flags=re.IGNORECASE)[0]
        condition_name = re.split(r'\s*\(score[:\s]', condition_name, flags=re.IGNORECASE)[0]
        condition_name = re.split(r'\s*\(likelihood[:\s]', condition_name, flags=re.IGNORECASE)[0]
        condition_name = re.split(r'\s*[—–-]\s+', condition_name)[0]
        condition_name = condition_name.strip().rstrip(':').strip()

        if not condition_name or len(condition_name) < 2 or len(condition_name) > 80:
            continue

        confidence = _extract_confidence_score(block)
        if confidence is None:
            confidence = infer_confidence(len(results) + 1)

        severity = infer_severity(block)
        if overall_severity in ("severe", "critical") and severity == "moderate":
            severity = overall_severity

        desc_lines = []
        for line in block.split('\n'):
            line = line.strip()
            if line and not re.match(r'^\s*\*{0,2}\d+[\.\)]', line):
                cleaned = re.sub(r'(?:confidence|score|likelihood|severity|justification)[:\s]*[^\n]*', '', line, flags=re.IGNORECASE).strip()
                if cleaned and len(cleaned) > 10:
                    desc_lines.append(cleaned)
        description = " ".join(desc_lines)[:300]

        condition_recs = []
        for i, rec in enumerate(all_recommendations):
            if len(results) == 0 and i < 2:
                condition_recs.append(rec)
            elif len(results) == 1 and i < 3:
                condition_recs.append(rec)

        results.append({
            "name": condition_name,
            "confidence": confidence,
            "severity": severity,
            "description": description or f"Clinical assessment based on presented symptoms",
            "recommendations": condition_recs[:3] if condition_recs else ["Consult a healthcare provider for proper evaluation"],
        })

        if len(results) >= 3:
            break

    if not results:
        return _parse_legacy_response(raw_text)

    return results


def _parse_legacy_response(raw_text: str) -> list[dict[str, Any]]:
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


def clean_chat_response(raw_text: str, user_message: str = "") -> str:
    text = re.sub(r'\[/?INST\]', '', raw_text)
    text = re.sub(r'</?s>', '', text)
    text = re.sub(r'###\s*(Instruction|Response)[:\s]*', '', text)
    text = re.sub(r'^\s*MedAI\s*:', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*Patient\s*:', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    if user_message and text:
        user_stripped = user_message.strip()
        if text.startswith(user_stripped):
            text = text[len(user_stripped):].strip()
        elif user_stripped.startswith(text[:80]) and len(text) < len(user_stripped) + 50:
            return ""

    instruction_markers = [
        "You are MedAI, an expert clinical",
        "You are MedAI, a clinical assistant",
        "Analyze the patient's symptoms",
        "Provide your assessment in this exact format",
        "Patient symptoms:",
        "Previous conversation:",
        "Reference Medical Literature:",
    ]
    for marker in instruction_markers:
        if text.startswith(marker):
            idx = text.find("\nLikely Conditions:")
            if idx == -1:
                idx = text.find("\nAssessment:")
            if idx != -1:
                text = text[idx:].strip()
                break

    return text
