import os
import re
import sys
import logging
import requests
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "medical_documents")
os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "MedAI-RAG-Expander/1.0 (Medical Research Bot)",
})

PUBMED_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

WHO_FACT_SHEETS = [
    ("malaria", "Malaria"),
    ("tuberculosis", "Tuberculosis"),
    ("hiv-aids", "HIV/AIDS"),
    ("hepatitis", "Hepatitis"),
    ("pneumonia", "Pneumonia"),
    ("diabetes", "Diabetes"),
    ("hypertension", "Hypertension"),
    ("dengue-severe-dengue", "Dengue"),
    ("cardiovascular-diseases", "Cardiovascular Disease"),
    ("cancer", "Cancer"),
    ("asthma", "Asthma"),
    ("chronic-obstructive-pulmonary-disease-copd", "COPD"),
    ("epilepsy", "Epilepsy"),
    ("meningitis", "Meningitis"),
    ("depression", "Depression"),
    ("sepsis", "Sepsis"),
    ("stroke-cerebrovascular-accident", "Stroke"),
    ("chronic-kidney-disease", "Chronic Kidney Disease"),
    ("anaemia", "Anaemia"),
    ("influenza", "Influenza"),
]

CDC_GUIDELINES_QUERIES = [
    "CDC malaria treatment guidelines clinical",
    "CDC tuberculosis clinical guidelines treatment",
    "CDC pneumonia treatment recommendations adults",
    "CDC diabetes management clinical guidelines",
    "CDC hypertension treatment clinical guidelines",
    "CDC hepatitis B clinical guidelines treatment",
    "CDC COVID-19 clinical management treatment",
    "CDC dengue clinical guidelines diagnosis treatment",
    "CDC meningitis clinical guidelines treatment",
    "CDC sepsis clinical guidelines management",
    "CDC heart failure clinical guidelines treatment",
    "CDC stroke clinical guidelines acute management",
    "CDC asthma clinical guidelines management",
    "CDC COPD clinical guidelines treatment",
    "CDC epilepsy clinical guidelines treatment",
    "CDC chronic kidney disease clinical guidelines",
    "CDC anemia clinical guidelines evaluation",
    "CDC depression clinical guidelines treatment",
    "CDC sepsis early recognition management",
    "CDC antimicrobial resistance clinical guidelines",
]

ICD11_DISEASES = [
    ("1F40", "Malaria", "Plasmodium infection transmitted by Anopheles mosquitoes. Symptoms include fever, chills, sweating, headache, body aches. Types: P. falciparum (severe), P. vivax, P. ovale, P. malariae, P. knowlesi. Diagnosis: blood smear, rapid diagnostic test. Treatment: artemisinin-based combination therapy (ACT)."),
    ("1B10", "Tuberculosis", "Mycobacterium tuberculosis infection. Primarily affects lungs. Symptoms: chronic cough, night sweats, weight loss, fever, hemoptysis. Diagnosis: sputum culture, GeneXpert MTB/RIF, tuberculin skin test. Treatment: 6-month RIPE regimen (Rifampicin, Isoniazid, Pyrazinamide, Ethambutol)."),
    ("CA40", "Pneumonia", "Infection of the lung parenchyma. Symptoms: cough, fever, chills, dyspnea, chest pain, purulent sputum. Causes: bacterial (S. pneumoniae most common), viral, fungal. Diagnosis: chest X-ray, sputum culture. Treatment: antibiotics based on severity and likely pathogen."),
    ("BA00", "Essential Hypertension", "Persistently elevated arterial blood pressure >= 130/80 mmHg. Often asymptomatic. Risk factors: obesity, salt intake, alcohol, genetics, age. Complications: stroke, MI, heart failure, CKD. Treatment: lifestyle modifications plus antihypertensives (ACE inhibitors, ARBs, CCBs, thiazides)."),
    ("5A10", "Diabetes Mellitus Type 2", "Metabolic disorder characterized by insulin resistance and relative insulin deficiency. Symptoms: polyuria, polydipsia, polyphagia, weight loss, fatigue. Diagnosis: HbA1c >= 6.5%, fasting glucose >= 126 mg/dL. Treatment: metformin first-line, lifestyle modifications, insulin if needed."),
    ("RA01", "COVID-19", "SARS-CoV-2 infection. Symptoms: fever, cough, fatigue, loss of taste/smell, dyspnea, sore throat. Severe: ARDS, multi-organ failure. Diagnosis: RT-PCR, antigen test. Treatment: supportive care, antivirals (Paxlovid), corticosteroids for severe cases."),
    ("1E50", "Dengue Fever", "Flavivirus infection transmitted by Aedes mosquitoes. Symptoms: high fever, severe headache, retro-orbital pain, myalgia, arthralgia, rash, hemorrhagic manifestations. Warning signs: abdominal pain, persistent vomiting, fluid accumulation. Diagnosis: NS1 antigen, IgM/IgG. Treatment: supportive, fluid management."),
    ("DB90", "Hepatitis B", "Hepatitis B virus (HBV) liver infection. Symptoms: jaundice, fatigue, abdominal pain, nausea, dark urine. Can be acute or chronic. Diagnosis: HBsAg, anti-HBc, HBV DNA. Treatment: tenofovir or entecavir for chronic infection."),
    ("8A80", "Ischaemic Stroke", "Cerebral infarction due to vascular occlusion. Symptoms: sudden unilateral weakness, speech disturbance, visual loss, ataxia, severe headache. Diagnosis: CT/MRI brain. Treatment: thrombolysis within 4.5 hours, thrombectomy for large vessel occlusion."),
    ("BA40", "Heart Failure", "Cardiac dysfunction with inadequate cardiac output. Symptoms: dyspnea, orthopnea, peripheral edema, fatigue, exercise intolerance. Types: HFrEF (reduced EF), HFpEF (preserved EF). Diagnosis: echocardiography, BNP/NT-proBNP. Treatment: ACEi/ARB, beta-blockers, diuretics, SGLT2 inhibitors."),
    ("5A11", "Type 1 Diabetes Mellitus", "Autoimmune destruction of pancreatic beta cells leading to absolute insulin deficiency. Symptoms: polyuria, polydipsia, weight loss, diabetic ketoacidosis. Diagnosis: autoantibodies (GAD, IA-2), low C-peptide. Treatment: lifelong insulin therapy."),
    ("CA20", "Asthma", "Chronic inflammatory airway disease with reversible airflow obstruction. Symptoms: wheezing, dyspnea, chest tightness, cough (worse at night). Triggers: allergens, exercise, cold air, infections. Diagnosis: spirometry with bronchodilator reversibility. Treatment: inhaled corticosteroids, LABA, SABA for rescue."),
    ("CA22", "COPD", "Progressive airflow limitation due to airway and alveolar inflammation. Symptoms: progressive dyspnea, chronic cough, sputum production. Primary cause: smoking. Diagnosis: spirometry (FEV1/FVC < 0.7). Treatment: bronchodilators (LABA, LAMA), inhaled corticoderoids, pulmonary rehabilitation."),
    ("8A60", "Epilepsy", "Chronic neurological disorder characterized by recurrent unprovoked seizures. Types: focal, generalized, unknown. Diagnosis: EEG, MRI brain. Treatment: antiseizure medications (valproate, levetiracetam, carbamazepine). Refractory cases: surgery, vagus nerve stimulation."),
    ("GB60", "Chronic Kidney Disease", "Progressive loss of kidney function over months to years. Symptoms: fatigue, edema, nausea, pruritus, uremia. Causes: diabetes, hypertension, glomerulonephritis. Stages: G1-G5 based on GFR. Treatment: manage underlying cause, ACEi/ARB, dialysis for ESRD."),
    ("4A00", "Anaemia", "Reduction in hemoglobin concentration below normal. Symptoms: fatigue, weakness, pallor, dyspnea, dizziness. Types: iron deficiency, B12/folate deficiency, hemolytic, aplastic, chronic disease. Diagnosis: CBC, reticulocyte count, iron studies, peripheral smear. Treatment: address underlying cause, supplementation."),
    ("6A70", "Depression", "Persistent depressive disorder with depressed mood and/or loss of interest. Symptoms: sadness, anhedonia, sleep disturbance, appetite changes, fatigue, concentration difficulties, suicidal ideation. Diagnosis: PHQ-9, clinical assessment. Treatment: psychotherapy (CBT), antidepressants (SSRIs first-line)."),
    ("1C60", "Sepsis", "Life-threatening organ dysfunction due to dysregulated host response to infection. Symptoms: fever, tachycardia, tachypnea, hypotension, altered mental status, elevated lactate. Diagnosis: qSOFA, SOFA score. Treatment: early antibiotics, fluid resuscitation, vasopressors, source control."),
    ("1E00", "Meningitis", "Inflammation of the meninges. Symptoms: headache, neck stiffness, fever, photophobia, nausea, altered consciousness. Causes: bacterial (N. meningitidis, S. pneumoniae), viral, fungal. Diagnosis: lumbar puncture, CSF analysis. Treatment: empirical antibiotics (ceftriaxone + vancomycin), dexamethasone."),
    ("RA02", "Influenza", "Acute respiratory illness caused by influenza virus. Symptoms: fever, myalgia, headache, cough, sore throat, fatigue. Complications: pneumonia, myocarditis, encephalitis. Diagnosis: rapid influenza diagnostic test, RT-PCR. Treatment: oseltamivir within 48 hours, supportive care."),
]


def download_who_fact_sheets():
    logger.info("Downloading WHO Disease Fact Sheets...")
    downloaded = 0

    for slug, name in WHO_FACT_SHEETS:
        filename = f"who_{slug.replace('-', '_')}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(filepath):
            logger.info(f"  Skipping {name} (already exists)")
            continue

        try:
            url = f"https://www.who.int/news-room/fact-sheets/detail/{slug}"
            resp = session.get(url, timeout=30)

            if not resp.ok:
                logger.warning(f"  Failed to fetch WHO {name}: HTTP {resp.status_code}")
                continue

            text = re.sub(r'<[^>]+>', ' ', resp.text)
            text = re.sub(r'\s+', ' ', text).strip()

            start_markers = ["Key facts", "Overview", "Key Facts"]
            start_idx = 0
            for marker in start_markers:
                idx = text.find(marker)
                if idx != -1:
                    start_idx = idx
                    break

            end_markers = ["News", "Feature stories", "Related links", "Subscribe"]
            end_idx = len(text)
            for marker in end_markers:
                idx = text.find(marker, start_idx + 500)
                if idx != -1 and idx < end_idx:
                    end_idx = idx

            content = text[start_idx:end_idx].strip()

            if len(content) < 200:
                logger.warning(f"  WHO {name}: content too short, skipping")
                continue

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Title: WHO Fact Sheet — {name}\n")
                f.write(f"Source: World Health Organization\n")
                f.write(f"URL: {url}\n")
                f.write(f"Type: Disease Fact Sheet\n\n")
                f.write(content[:12000])

            downloaded += 1
            logger.info(f"  Downloaded: WHO {name}")
            time.sleep(1)

        except Exception as e:
            logger.error(f"  Error downloading WHO {name}: {e}")

    return downloaded


def download_cdc_guidelines():
    logger.info("Downloading CDC Clinical Guidelines via PubMed...")
    downloaded = 0

    for query in CDC_GUIDELINES_QUERIES:
        safe_name = re.sub(r'[^a-z0-9]+', '_', query.lower())[:50]
        filename = f"cdc_{safe_name}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(filepath):
            logger.info(f"  Skipping {query[:50]}... (already exists)")
            continue

        try:
            search_resp = session.get(
                f"{PUBMED_API}/esearch.fcgi",
                params={
                    "db": "pmc",
                    "term": query,
                    "retmax": 2,
                    "retmode": "json",
                    "sort": "relevance",
                },
                timeout=30,
            )
            search_resp.raise_for_status()
            id_list = search_resp.json().get("esearchresult", {}).get("idlist", [])

            if not id_list:
                continue

            pmc_id = id_list[0]
            fetch_resp = session.get(
                f"{PUBMED_API}/efetch.fcgi",
                params={"db": "pmc", "id": pmc_id, "rettype": "text", "retmode": "text"},
                timeout=60,
            )

            if not fetch_resp.ok or len(fetch_resp.text) < 200:
                continue

            text = re.sub(r'<[^>]+>', '', fetch_resp.text)
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r' {2,}', ' ', text)

            summary_resp = session.get(
                f"{PUBMED_API}/esummary.fcgi",
                params={"db": "pmc", "id": pmc_id, "retmode": "json"},
                timeout=30,
            )
            title = f"CDC Guideline: {query}"
            if summary_resp.ok:
                summary = summary_resp.json().get("result", {}).get(pmc_id, {})
                title = summary.get("title", title)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Title: {title}\n")
                f.write(f"Source: CDC via PubMed Central (PMC{pmc_id})\n")
                f.write(f"URL: https://pubmed.ncbi.nlm.nih.gov/{pmc_id}/\n")
                f.write(f"Type: Clinical Guideline\n\n")
                f.write(text[:12000])

            downloaded += 1
            logger.info(f"  Downloaded: {title[:60]}...")
            time.sleep(1)

        except Exception as e:
            logger.error(f"  Error downloading CDC guideline: {e}")

    return downloaded


def generate_icd11_descriptions():
    logger.info("Generating ICD-11 Disease Description documents...")
    generated = 0

    for code, name, description in ICD11_DISEASES:
        filename = f"icd_{code}_{name.lower().replace(' ', '_').replace('/', '_')}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(filepath):
            logger.info(f"  Skipping ICD-11 {name} (already exists)")
            continue

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Title: ICD-11 Disease Description — {name}\n")
            f.write(f"Source: WHO International Classification of Diseases 11th Revision\n")
            f.write(f"ICD-11 Code: {code}\n")
            f.write(f"Type: Disease Classification\n\n")
            f.write(f"Disease: {name} (ICD-11: {code})\n\n")
            f.write(description)

        generated += 1
        logger.info(f"  Generated: ICD-11 {name} ({code})")

    return generated


def main():
    logger.info("=" * 60)
    logger.info("MedAI RAG Document Expansion")
    logger.info("=" * 60)

    who_count = download_who_fact_sheets()
    cdc_count = download_cdc_guidelines()
    icd_count = generate_icd11_descriptions()

    logger.info("=" * 60)
    logger.info(f"Summary:")
    logger.info(f"  WHO Fact Sheets: {who_count} downloaded")
    logger.info(f"  CDC Guidelines:  {cdc_count} downloaded")
    logger.info(f"  ICD-11 Descriptions: {icd_count} generated")
    logger.info(f"  Total new documents: {who_count + cdc_count + icd_count}")
    logger.info("=" * 60)

    logger.info("\nNext steps:")
    logger.info("  1. Run: POST /documents/ingest-folder  to index new documents")
    logger.info("  2. Or restart the server with RAG_AUTO_SYNC=true")


if __name__ == "__main__":
    main()
