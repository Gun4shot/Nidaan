SYSTEM_PERSONA = (
    "You are a clinical decision support system. "
    "Analyze patient symptoms and list the top 3 most likely conditions ranked by likelihood. "
    "For each condition provide a one-line clinical justification. "
    "Rate overall severity as Mild, Moderate, or Severe with a one-line reason. "
    "Give 3 actionable recommendations. "
    "List 3 red-flag symptoms that require immediate medical attention. "
    "Never greet the user. Never ask follow-up questions. Never hedge. "
    "Use specific medical terminology. Be direct and concise."
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
]

EMERGENCY_ADDENDUM = (
    "\n\nEMERGENCY ALERT: The symptoms below may indicate a life-threatening condition. "
    "Begin your response with 'EMERGENCY: Call emergency services immediately.' "
    "Then provide the structured assessment below."
)

RESPONSE_PRIMER = "Top 3 Possible Conditions:\n1."

CITATION_INSTRUCTION = (
    "\n\nWhen referencing information from the provided medical literature, "
    "cite the source using [1], [2], etc. matching the numbered references. "
    "Only cite information that directly supports your assessment."
)


def _check_emergency(text: str) -> str:
    lower = text.lower()
    for kw in EMERGENCY_KEYWORDS:
        if kw in lower:
            return EMERGENCY_ADDENDUM
    return ""


def _format_rag_context(rag_context: str) -> str:
    if not rag_context:
        return ""
    return (
        f"\n\nReference Medical Literature:\n"
        f"Use the following verified medical information to inform your assessment.\n"
        f"Do not repeat the references verbatim — integrate findings naturally.\n"
        f"Cite sources using [1], [2], etc. when referencing specific guidelines.\n\n"
        f"{rag_context}\n"
    )


def build_symptom_prompt(symptoms: list[str], rag_context: str = "") -> str:
    symptom_block = "\n".join(f"- {s}" for s in symptoms)
    combined = " ".join(symptoms)
    emergency = _check_emergency(combined)
    context_block = _format_rag_context(rag_context)

    return (
        f"### Instruction:\n"
        f"{SYSTEM_PERSONA}\n\n"
        f"Patient-reported symptoms:\n"
        f"{symptom_block}\n"
        f"{emergency}"
        f"{context_block}\n\n"
        f"Provide your assessment in this exact format:\n"
        f"Top 3 Possible Conditions (numbered, with one-line justification each)\n"
        f"Severity: level — one-line reason\n"
        f"Recommendations: 3 actionable steps\n"
        f"See a doctor immediately if: 3 red-flag symptoms\n\n"
        f"### Response:\n"
        f"{RESPONSE_PRIMER}"
    )


def build_chat_prompt(
    user_message: str,
    history: list[dict] = None,
    rag_context: str = "",
) -> str:
    history = history or []

    context = ""
    for turn in history[-4:]:
        role = "Patient" if turn["role"] == "user" else "MedAI"
        context += f"{role}: {turn['content']}\n"

    symptom_keywords = [
        "pain", "ache", "fever", "cough", "nausea",
        "dizzy", "fatigue", "rash", "swelling", "bleeding",
        "headache", "vomit", "diarrhea", "numbness",
    ]
    has_symptoms = any(kw in user_message.lower() for kw in symptom_keywords)
    emergency = _check_emergency(user_message)
    context_block = _format_rag_context(rag_context)

    if has_symptoms:
        return (
            f"### Instruction:\n"
            f"{SYSTEM_PERSONA}\n\n"
            f"Conversation so far:\n"
            f"{context}"
            f"Patient: {user_message}\n"
            f"{emergency}"
            f"{context_block}\n\n"
            f"### Response:\n"
            f"{RESPONSE_PRIMER}"
        )

    return (
        f"### Instruction:\n"
        f"You are MedAI, a clinical assistant. Answer the patient's "
        f"question directly and concisely. Do not greet. Do not ask "
        f"follow-up questions unless critical information is missing.\n\n"
        f"Conversation so far:\n"
        f"{context}"
        f"Patient: {user_message}\n"
        f"{context_block}\n\n"
        f"### Response:\n"
        f"MedAI:"
    )
