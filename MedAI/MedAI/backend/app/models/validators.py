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

    structured = {}

    fever_pattern = data.get("fever_pattern")
    if fever_pattern and isinstance(fever_pattern, str):
        fever_pattern = fever_pattern.strip().lower()
        valid_patterns = ["cyclic", "continuous", "intermittent", "remittent", "low-grade", "high-grade", "none"]
        if fever_pattern in valid_patterns or len(fever_pattern) <= 30:
            structured["fever_pattern"] = fever_pattern

    travel_history = data.get("travel_history")
    if travel_history and isinstance(travel_history, str):
        travel_history = travel_history.strip()
        if len(travel_history) <= 200:
            structured["travel_history"] = travel_history

    region = data.get("region")
    if region and isinstance(region, str):
        region = region.strip()
        if len(region) <= 100:
            structured["region"] = region

    symptom_duration = data.get("symptom_duration")
    if symptom_duration and isinstance(symptom_duration, str):
        symptom_duration = symptom_duration.strip()
        if len(symptom_duration) <= 50:
            structured["symptom_duration"] = symptom_duration

    onset_type = data.get("onset_type")
    if onset_type and isinstance(onset_type, str):
        onset_type = onset_type.strip().lower()
        valid_onsets = ["sudden", "gradual", "acute", "chronic", "progressive"]
        if onset_type in valid_onsets or len(onset_type) <= 20:
            structured["onset_type"] = onset_type

    severity_scale = data.get("severity_scale")
    if severity_scale is not None:
        try:
            severity_scale = int(severity_scale)
            if 1 <= severity_scale <= 10:
                structured["severity_scale"] = severity_scale
        except (ValueError, TypeError):
            pass

    age = data.get("age")
    if age is not None:
        try:
            age = int(age)
            if 0 <= age <= 150:
                structured["age"] = age
        except (ValueError, TypeError):
            pass

    sex = data.get("sex")
    if sex and isinstance(sex, str):
        sex = sex.strip().lower()
        if sex in ("male", "female", "m", "f"):
            structured["sex"] = sex

    return None, {"symptoms": cleaned, **structured}


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

    structured = {}

    fever_pattern = data.get("fever_pattern")
    if fever_pattern and isinstance(fever_pattern, str):
        structured["fever_pattern"] = fever_pattern.strip().lower()

    travel_history = data.get("travel_history")
    if travel_history and isinstance(travel_history, str):
        structured["travel_history"] = travel_history.strip()[:200]

    region = data.get("region")
    if region and isinstance(region, str):
        structured["region"] = region.strip()[:100]

    symptom_duration = data.get("symptom_duration")
    if symptom_duration and isinstance(symptom_duration, str):
        structured["symptom_duration"] = symptom_duration.strip()[:50]

    onset_type = data.get("onset_type")
    if onset_type and isinstance(onset_type, str):
        structured["onset_type"] = onset_type.strip().lower()

    severity_scale = data.get("severity_scale")
    if severity_scale is not None:
        try:
            severity_scale = int(severity_scale)
            if 1 <= severity_scale <= 10:
                structured["severity_scale"] = severity_scale
        except (ValueError, TypeError):
            pass

    return None, {"message": message, "history": cleaned_history, **structured}
