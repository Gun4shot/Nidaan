SYSTEM_PERSONA = (
    "You are MedAI, an expert clinical decision support system with access to "
    "verified medical literature from WHO, CDC, PubMed, and ICD-11 classifications. "
    "You must reason step-by-step before providing your diagnosis. "
    "Never greet the user. Never ask follow-up questions unless critical information is missing. "
    "Use specific medical terminology. Be direct and concise."
)

CHAT_PERSONA = (
    "You are MedAI, a clinical assistant with access to verified medical literature. "
    "Answer the patient's question directly and concisely using evidence-based information. "
    "Cite sources using [1], [2], etc. when referencing medical literature. "
    "Do not greet. Do not ask follow-up questions unless critical information is missing."
)

EMERGENCY_KEYWORDS = [
    "chest pain", "crushing pain", "left arm pain",
    "stroke", "face drooping", "slurred speech", "sudden weakness",
    "can't breathe", "cannot breathe", "breathing difficulty",
    "loss of consciousness", "unresponsive", "passed out",
    "severe bleeding", "uncontrolled bleeding",
    "seizure", "convulsion",
    "anaphylaxis", "swollen throat", "can't swallow",
    "suicidal", "overdose",
    "108 f", "107 f", "106 f", "105 f", "41 c", "42 c", "43 c",
]

EMERGENCY_ADDENDUM = (
    "\n\nEMERGENCY ALERT: The symptoms below may indicate a life-threatening condition. "
    "Begin your response with 'EMERGENCY: Call emergency services immediately.' "
    "Then provide the structured assessment below."
)

CITATION_INSTRUCTION = (
    "\n\nWhen referencing information from the provided medical literature, "
    "cite the source using [1], [2], etc. matching the numbered references. "
    "Only cite information that directly supports your assessment."
)

SYMPTOM_FEW_SHOT_TEMPLATE = """You are MedAI, an expert clinical decision support system trained on PubMed medical literature.
Analyze the patient's complete profile including symptoms, age, exposures, and risk factors.
Base your reasoning on clinical evidence. Consider the patient's specific demographics and exposures when ranking diagnoses.

Example:

Patient symptoms: persistent dry cough for 2 weeks, low-grade fever, night sweats, weight loss of 5 kg over 1 month
Profile: 35 years old, male, lives in endemic area

Assessment:
The combination of chronic cough, low-grade fever, night sweats, and significant weight loss is highly suggestive of a chronic infectious process. Given the endemic setting, pulmonary tuberculosis is the leading diagnosis.

Likely Conditions:
1. Pulmonary Tuberculosis - Confidence: 82%
   Chronic cough with constitutional symptoms (fever, night sweats, weight loss) is the hallmark presentation of TB in endemic regions.
2. Lung Malignancy - Confidence: 12%
   Unintentional weight loss and chronic cough raise concern for malignancy, though less likely at age 35 without smoking history.
3. Chronic Bronchitis - Confidence: 6%
   Persistent cough may indicate chronic bronchitis, but constitutional symptoms are atypical.

Severity: Moderate
Recommendations:
1. Obtain chest X-ray and sputum for acid-fast bacilli (AFB) smear and culture.
2. Perform tuberculin skin test (TST) or interferon-gamma release assay (IGRA).
3. Initiate respiratory isolation precautions until TB is ruled out.

---

Now analyze this patient:

Patient symptoms: PATIENT_SYMPTOMS_PLACEHOLDER
CONTEXT_PLACEHOLDER

Assessment:
"""


def _check_emergency(text: str) -> str:
    lower = text.lower()
    for kw in EMERGENCY_KEYWORDS:
        if kw in lower:
            return EMERGENCY_ADDENDUM
    return ""


def _format_rag_context(rag_context: str) -> str:
    if not rag_context:
        return ""
    if len(rag_context) > 1500:
        rag_context = rag_context[:1500] + "\n[Truncated]"
    return (
        f"\nMedical Reference (for context only, prioritize patient symptoms):\n"
        f"{rag_context}\n"
    )


def _format_structured_data(structured_data: dict) -> str:
    if not structured_data:
        return ""

    parts = []
    if structured_data.get("fever_pattern"):
        parts.append(f"Fever pattern: {structured_data['fever_pattern']}")
    if structured_data.get("symptom_duration"):
        parts.append(f"Symptom duration: {structured_data['symptom_duration']}")
    if structured_data.get("onset_type"):
        parts.append(f"Onset type: {structured_data['onset_type']}")
    if structured_data.get("severity_scale"):
        parts.append(f"Patient-reported severity: {structured_data['severity_scale']}/10")
    if structured_data.get("travel_history"):
        parts.append(f"Travel history: {structured_data['travel_history']}")
    if structured_data.get("region"):
        parts.append(f"Geographic region: {structured_data['region']}")
    if structured_data.get("age"):
        parts.append(f"Age: {structured_data['age']}")
    if structured_data.get("sex"):
        parts.append(f"Sex: {structured_data['sex']}")

    if not parts:
        return ""

    return "\nAdditional context: " + ", ".join(parts) + ".\n"


def _format_history(history: list[dict], max_turns: int = 4) -> str:
    if not history:
        return ""
    lines = []
    for turn in history[-max_turns:]:
        role = "Patient" if turn["role"] == "user" else "MedAI"
        lines.append(f"{role}: {turn['content']}")
    return "\n".join(lines)


def build_chat_prompt(
    user_message: str,
    history: list[dict] = None,
    rag_context: str = "",
    structured_data: dict = None,
    gemini_enrichment: str = "",
) -> str:
    history = history or []

    symptom_keywords = [
        "pain", "ache", "fever", "cough", "nausea",
        "dizzy", "fatigue", "rash", "swelling", "bleeding",
        "headache", "vomit", "vomiting", "diarrhea", "numbness",
        "thirst", "thirsty", "urinate", "urination", "peeing",
        "tired", "exhausted", "weakness", "weak", "no energy",
        "weight loss", "lost weight", "blurry", "blurred", "vision",
        "wound", "heal", "healing", "sore", "burning", "itching",
        "breathless", "breathing", "chest", "palpitation",
        "constipation", "bloating", "cramp", "stiffness",
        "insomnia", "sleep", "anxiety", "depression", "mood",
        "frequent", "unexplained", "strange", "unusual",
        "chills", "rigors", "sweating", "muscle", "joint",
    ]
    has_symptoms = any(kw in user_message.lower() for kw in symptom_keywords)
    if not has_symptoms and len(user_message.split()) > 30:
        has_symptoms = True

    emergency = _check_emergency(user_message)
    context_block = _format_rag_context(rag_context)
    structured_block = _format_structured_data(structured_data)
    history_text = _format_history(history)

    if has_symptoms:
        return _build_symptom_chat_prompt(
            user_message, history_text, context_block, structured_block, emergency, gemini_enrichment
        )
    else:
        return _build_general_chat_prompt(
            user_message, history_text, context_block, structured_block
        )


def _build_symptom_chat_prompt(
    user_message: str,
    history_text: str,
    context_block: str,
    structured_block: str,
    emergency: str,
    gemini_enrichment: str = "",
) -> str:
    parts = []
    parts.append("You are MedAI, an expert clinical decision support system trained on PubMed medical literature.")
    parts.append("Provide a structured differential diagnosis based on the patient's specific profile.")
    parts.append("Consider age, exposures, and risk factors when ranking diagnoses.")
    parts.append("Do NOT repeat generic textbook descriptions. Focus on THIS patient.")
    parts.append("")

    if gemini_enrichment:
        parts.append("Clinical Context (enriched by Gemini):")
        parts.append(gemini_enrichment)
        parts.append("")

    if context_block:
        parts.append(context_block.strip())
        parts.append("")

    if history_text:
        parts.append("Previous conversation:")
        parts.append(history_text)
        parts.append("")

    parts.append(f"Patient: {user_message}")
    if structured_block:
        parts.append(structured_block.strip())
    if emergency:
        parts.append(emergency.strip())

    parts.append("")
    parts.append("Provide your assessment in this exact format:")
    parts.append("")
    parts.append("Assessment:")
    parts.append("[2-3 sentence summary considering this patient's specific age, exposures, and symptoms]")
    parts.append("")
    parts.append("Likely Conditions:")
    parts.append("1. [Condition] - Confidence: [X]%")
    parts.append("   [Why this fits THIS patient specifically]")
    parts.append("2. [Condition] - Confidence: [X]%")
    parts.append("   [Why this fits THIS patient specifically]")
    parts.append("3. [Condition] - Confidence: [X]%")
    parts.append("   [Why this fits THIS patient specifically]")
    parts.append("")
    parts.append("Severity: [Mild/Moderate/Severe/Critical]")
    parts.append("Recommendations:")
    parts.append("1. [Specific test or action]")
    parts.append("2. [Specific test or action]")
    parts.append("3. [Specific test or action]")
    parts.append("")
    parts.append("Assessment:")

    return "\n".join(parts)


def _build_general_chat_prompt(
    user_message: str,
    history_text: str,
    context_block: str,
    structured_block: str,
) -> str:
    parts = []
    parts.append("You are MedAI, a knowledgeable medical assistant.")
    parts.append("Provide clear, accurate, and helpful medical information.")
    parts.append("")

    if history_text:
        parts.append("Previous conversation:")
        parts.append(history_text)
        parts.append("")

    parts.append(f"Patient: {user_message}")
    if structured_block:
        parts.append(structured_block.strip())
    if context_block:
        parts.append(context_block.strip())
    parts.append("")
    parts.append("MedAI:")

    return "\n".join(parts)


def build_symptom_prompt(
    symptoms: list[str],
    rag_context: str = "",
    structured_data: dict = None,
) -> str:
    symptom_block = ", ".join(symptoms)
    combined = " ".join(symptoms)
    emergency = _check_emergency(combined)
    context_block = _format_rag_context(rag_context)
    structured_block = _format_structured_data(structured_data)

    parts = []
    parts.append("You are MedAI, an expert clinical decision support system trained on PubMed medical literature.")
    parts.append("Provide a structured differential diagnosis based on the patient's specific profile.")
    parts.append("Consider age, exposures, and risk factors when ranking diagnoses.")
    parts.append("")

    if context_block:
        parts.append(context_block.strip())
        parts.append("")

    parts.append(f"Patient symptoms: {symptom_block}")
    if structured_block:
        parts.append(structured_block.strip())
    if emergency:
        parts.append(emergency.strip())

    parts.append("")
    parts.append("Provide your assessment in this exact format:")
    parts.append("")
    parts.append("Assessment:")
    parts.append("[2-3 sentence summary considering this patient's specific age, exposures, and symptoms]")
    parts.append("")
    parts.append("Likely Conditions:")
    parts.append("1. [Condition] - Confidence: [X]%")
    parts.append("   [Why this fits THIS patient specifically]")
    parts.append("2. [Condition] - Confidence: [X]%")
    parts.append("   [Why this fits THIS patient specifically]")
    parts.append("3. [Condition] - Confidence: [X]%")
    parts.append("   [Why this fits THIS patient specifically]")
    parts.append("")
    parts.append("Severity: [Mild/Moderate/Severe/Critical]")
    parts.append("Recommendations:")
    parts.append("1. [Specific test or action]")
    parts.append("2. [Specific test or action]")
    parts.append("3. [Specific test or action]")
    parts.append("")
    parts.append("Assessment:")

    return "\n".join(parts)
