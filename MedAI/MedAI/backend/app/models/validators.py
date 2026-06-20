from typing import Optional, Tuple


def validate_predict_request(data: dict) -> Tuple[Optional[str], Optional[dict]]:
    if not data:
        return "Request body is required.", None

    symptoms = data.get("symptoms")
    if symptoms is None:
        return "Field 'symptoms' is required.", None
    if not isinstance(symptoms, list):
        return "Field 'symptoms' must be a list of strings.", None
    if len(symptoms) == 0:
        return "At least one symptom is required.", None
    if len(symptoms) > 20:
        return "Maximum 20 symptoms allowed per request.", None

    cleaned = []
    for s in symptoms:
        if not isinstance(s, str):
            return "Each symptom must be a string.", None
        s = s.strip()
        if len(s) < 2:
            return f"Symptom too short: '{s}'", None
        if len(s) > 100:
            return f"Symptom too long (max 100 chars): '{s[:20]}...'", None
        cleaned.append(s)

    return None, {"symptoms": cleaned}


def validate_chat_request(data: dict) -> Tuple[Optional[str], Optional[dict]]:
    if not data:
        return "Request body is required.", None

    message = data.get("message")
    if message is None:
        return "Field 'message' is required.", None
    if not isinstance(message, str):
        return "Field 'message' must be a string.", None

    message = message.strip()
    if len(message) == 0:
        return "Message cannot be empty.", None
    if len(message) > 2000:
        return "Message too long (max 2000 characters).", None

    history = data.get("history", [])
    if not isinstance(history, list):
        return "Field 'history' must be a list.", None

    cleaned_history = []
    for turn in history[-10:]:
        if not isinstance(turn, dict):
            continue
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role in ("user", "assistant") and isinstance(content, str):
            cleaned_history.append({"role": role, "content": content[:1000]})

    return None, {"message": message, "history": cleaned_history}
