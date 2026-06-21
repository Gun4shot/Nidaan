import os
import json
import logging
from config import Config

logger = logging.getLogger(__name__)


class GeminiService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
        return cls._instance

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not Config.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Get a free key at "
                "https://aistudio.google.com/apikey and add it to .env"
            )

        from google import genai

        self._client = genai.Client(api_key=Config.GEMINI_API_KEY)
        logger.info(f"Gemini client initialized (model={Config.GEMINI_MODEL})")
        return self._client

    @property
    def is_ready(self) -> bool:
        return bool(Config.GEMINI_API_KEY)

    def enrich(self, age: int, gender: str, cv_predictions: list[dict]) -> str:
        client = self._get_client()

        gemini_prompt = self._build_enrichment_prompt(age, gender, cv_predictions)

        logger.info(
            f"Gemini enrichment request: age={age}, gender={gender}, "
            f"labels={len(cv_predictions)}"
        )

        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents=gemini_prompt,
        )

        raw = response.text

        if "---BIOMISTRAL PROMPT START---" in raw and "---BIOMISTRAL PROMPT END---" in raw:
            furnished = raw.split("---BIOMISTRAL PROMPT START---")[1]
            furnished = furnished.split("---BIOMISTRAL PROMPT END---")[0].strip()
        else:
            furnished = raw.strip()
            logger.warning("Gemini response missing markers, using raw output")

        logger.info(f"Gemini enrichment complete: {len(furnished)} chars")
        return furnished

    def _build_enrichment_prompt(
        self, age: int, gender: str, cv_predictions: list[dict]
    ) -> str:
        return f"""You are Gemini ({Config.GEMINI_MODEL}), operating as the medical context enrichment engine in a clinical AI pipeline. You sit between a Computer Vision model and BioMistral, a PubMed-trained medical LLM.

You have received the following inputs from the Computer Vision model:

Patient Age    : {age}
Patient Gender : {gender}
CV Detections  : {json.dumps(cv_predictions, indent=2)}

YOUR JOB:
Enrich these raw inputs into a fully furnished medical prompt that BioMistral (2048 token context limit) can reason over. You must do ALL of the following jobs:

JOB 1 — CLINICAL DEFINITION
  For each detected disease:
  - Full medical name and definition
  - ICD-11 classification code
  - Organ system affected
  - How the disease develops (pathophysiology)

JOB 2 — DEMOGRAPHIC RELEVANCE
  - How disease presents in this age group
  - How gender affects severity and prognosis
  - Risk factors for this patient profile

JOB 3 — SYMPTOM MAPPING
  - Primary symptoms
  - Secondary symptoms
  - Symptoms overlapping with other detected labels

JOB 4 — SEVERITY STRATIFICATION
  - Mild    : specific clinical indicators
  - Moderate: specific clinical indicators
  - Severe  : specific clinical indicators

JOB 5 — DISEASE INTERACTION (if multiple labels)
  - Which disease is PRIMARY (root cause)
  - Which disease is SECONDARY (caused by primary)
  - How they worsen each other
  - Which to treat first

JOB 6 — CONFIRMATION TESTS
  - Tests to confirm each disease
  - Lab values to check
  - Imaging findings to look for

JOB 7 — TREATMENT DIRECTION
  - First-line treatment approach
  - Procedural interventions if needed
  - Do NOT specify drug dosages

JOB 8 — URGENT COMPLICATIONS
  - Life-threatening complications if untreated
  - Early warning signs of deterioration

After completing all 8 jobs, construct ONE fully furnished prompt for BioMistral using this EXACT format:

---BIOMISTRAL PROMPT START---

<system>
You are BioMistral, an expert clinical diagnosis assistant pre-trained on 1.47 million PubMed Central medical documents totaling 3 billion tokens. Evaluated on 10 medical QA benchmarks: MedQA (USMLE), MedMCQA (193,000+ questions), PubMedQA, and MMLU medical subjects. Running in 4-bit quantized mode with 2048 token context window.

STRICT RULES:
- Reason step by step before final output
- Validate each CV detection against enriched context
- Identify causal relationships between diseases
- Return structured JSON only — no free text outside
- Never recommend specific drug dosages
- Always include medical disclaimer
</system>

<patient_profile>
Age    : {age}
Gender : {gender}
</patient_profile>

<cv_model_detections>
{chr(10).join(f"- {p['label']} (confidence: {p['confidence']}%)" for p in cv_predictions)}
</cv_model_detections>

<enriched_medical_context>
[INSERT ALL 8 JOBS STRUCTURED CLEARLY HERE]

Format each disease as:
DISEASE: [Name]
  Definition     : ...
  ICD-11 Code    : ...
  Demographic    : ...
  Symptoms       : ...
  Severity       : ...
  Confirmation   : ...
  Treatment      : ...
  Complications  : ...

DISEASE INTERACTION:
  Primary        : ...
  Secondary      : ...
  Interaction    : ...
  Priority       : ...
</enriched_medical_context>

<reasoning_task>
STEP 1 - Validate each CV detection against context
STEP 2 - Assess severity for each condition
STEP 3 - Analyze disease interaction and causal link
STEP 4 - Write patient-friendly explanation
STEP 5 - Write doctor-facing clinical summary

Return ONLY this JSON:
{{
  "detected_conditions": [
    {{
      "disease": "",
      "confidence": 0.0,
      "validation": "supported / unsupported",
      "validation_reason": "",
      "severity": "mild / moderate / severe",
      "severity_reason": "",
      "key_symptoms_to_watch": [],
      "urgent_complications": [],
      "confirmation_tests_needed": [],
      "treatment_direction": ""
    }}
  ],
  "disease_interaction": {{
    "primary_condition": "",
    "secondary_condition": "",
    "causal_relationship": "",
    "combined_impact": "",
    "treatment_priority": ""
  }},
  "patient_explanation": "",
  "clinical_summary": "",
  "immediate_actions": [],
  "specialist_referral": [],
  "follow_up_timeline": "",
  "disclaimer": "This is AI-assisted clinical decision support. Always consult a licensed physician for final decisions."
}}
</reasoning_task>

---BIOMISTRAL PROMPT END---

STRICT OUTPUT RULES:
1. Output ONLY content between the markers
2. No text before or after the markers
3. Keep total length under 1800 tokens
4. If confidence below 50%, flag as low confidence
5. Prompt must be fully self-contained for BioMistral"""

    def enhance_symptoms(self, user_message: str, history_text: str = "") -> str:
        client = self._get_client()

        prompt = f"""You are Gemini ({Config.GEMINI_MODEL}), operating as the clinical context enrichment engine in a medical AI pipeline. You sit between a Patient and BioMistral, a PubMed-trained medical LLM (7B parameters, 4-bit quantized, limited reasoning capacity).

The patient has described their symptoms in natural language. Your job is to transform this into a structured clinical context that BioMistral can reason over effectively.

PATIENT MESSAGE:
{user_message}

{f"CONVERSATION HISTORY:{chr(10)}{history_text}" if history_text else ""}

YOUR TASK -- Extract and enrich the following clinical information:

1. SYMPTOM EXTRACTION: List each distinct symptom mentioned, using proper medical terminology in parentheses. Example: "chest pain (thoracodynia)", "difficulty breathing (dyspnea)"

2. PATIENT PROFILE: Extract any mentioned demographics -- age, sex, smoking status, occupation, exposures, travel history, medications, pre-existing conditions.

3. TEMPORAL ANALYSIS: When did symptoms start? Acute vs chronic? Progressive? Cyclical pattern?

4. RED FLAGS: Identify any symptoms that could indicate a life-threatening condition requiring immediate attention.

5. KEY DIFFERENTIAL DIAGNOSES: Based on the symptom cluster and patient profile, list the top 3-5 most likely conditions a clinician would consider. For each, briefly explain WHY it fits this specific patient (age, exposures, symptom combination). Assign a rough likelihood: High (>60%), Moderate (30-60%), Low (<30%).

6. RECOMMENDED WORKUP: List the most relevant diagnostic tests (blood work, imaging, specific clinical tests) for this presentation.

7. CLINICAL REASONING: Write a 2-3 sentence clinical reasoning chain that connects the symptoms to the most likely diagnosis, considering the patient's specific risk factors.

Keep total output under 800 tokens. Be precise and clinical. Do NOT include a disclaimer -- BioMistral will handle that.

Output your enrichment as structured text (not JSON), using clear headers like:
SYMPTOMS:
PATIENT PROFILE:
RED FLAGS:
DIFFERENTIAL DIAGNOSES:
RECOMMENDED WORKUP:
CLINICAL REASONING:
"""

        logger.info(f"Gemini symptom enhancement request: {user_message[:100]}...")

        try:
            response = client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=prompt,
            )
            enriched = response.text.strip()
            logger.info(f"Gemini symptom enhancement complete: {len(enriched)} chars")
            return enriched
        except Exception as e:
            logger.error(f"Gemini symptom enhancement failed: {e}")
            raise


gemini_service = GeminiService()
