<div align="center">

# Nidaan

### AI-Powered Medical Diagnostics & Blood Analytics Platform

<br>

![Next.js](https://img.shields.io/badge/Next.js-16-black?style=for-the-badge&logo=next.js&logoColor=white)
![Python](https://img.shields.io/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/PyTorch-2.x-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![TypeScript](https://img.shields.io/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/TailwindCSS-4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

<br>

An end-to-end medical AI system combining **deep learning–based disease classification** from medical imaging with an **advanced blood analytics dashboard** featuring 12 clinical visualizations, anomaly detection, and predictive risk scoring.

<br>

![Nidaan Banner](public/media/screen.png)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Medical Imaging Pipeline (CV)](#medical-imaging-pipeline-cv)
- [Blood Analytics Dashboard](#blood-analytics-dashboard)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)

---

## Overview

**Nidaan** addresses two critical gaps in healthcare diagnostics:

| Problem | Solution |
|---------|----------|
| Manual interpretation of medical scans is slow and error-prone | Automated multi-disease classification across 5 imaging modalities using EfficientNet-B3 |
| Blood test results are hard for patients to interpret | Interactive analytics dashboard with 12 clinical visualizations, anomaly detection, and risk scoring |

The platform is built as a **full-stack application** — a Next.js web frontend backed by PyTorch inference models and a Python analytics engine, deployable as a unified experience.

---

## Key Features

### Medical Imaging (CV Pipeline)
- **5 specialist models** — Chest X-Ray (NIH), Brain Tumor (MRI), COVID-19 (Radiography), Malaria (Cell), Bone Fractures (X-Ray)
- **EfficientNet-B3 backbone** with custom classification heads
- **Two-phase training** — frozen backbone warmup followed by full fine-tune with cosine annealing
- **Class-balanced sampling** via `WeightedRandomSampler` for imbalanced medical datasets
- **Mixed-precision training** with `GradScaler` for faster convergence
- **Stratified train/val/test splits** ensuring representative evaluation
- **Inference-ready** — `load_model_for_inference()` + `predict()` for direct frontend integration

### Blood Analytics Dashboard
- **Organ Panel Summary** — at-a-glance status cards per organ system
- **Reference Range Bars** — patient values mapped against clinical normal ranges
- **Correlation Heatmap** — 20-biomarker Pearson correlation matrix with group separators
- **Distribution Plots** — violin + KDE plots stratified by disease
- **Patient Radar Chart** — multi-patient comparison across 8 biomarkers
- **Longitudinal Trends** — 3-visit biomarker trajectory tracking
- **Anomaly Detection** — Isolation Forest flagging 8% outlier patients
- **Composite Risk Score** — weighted 0–100 risk gauge across 12 biomarkers
- **PCA Clustering** — 2D patient scatter colored by disease phenotype
- **Population Percentile Rank** — age/gender-matched cohort comparison
- **What-If Simulator** — medication, diet, and lifestyle scenario modeling
- **Biomarker Causal Graph** — clinically grounded DAG of biomarker-disease pathways

### Web Platform
- **Next.js 16** with App Router and TypeScript
- **AI Chat Interface** — conversational medical assistant
- **Image Analysis** — upload and classify medical images in-browser
- **Voice Input** — dual-engine speech recognition (Web Speech API + Whisper)
- **Auth** — NextAuth.js integration
- **GSAP animations** and cinematic UI with dark theme

---

## Architecture

```
                          Nidaan Platform
                 ┌──────────────────────────────┐
                 │        Next.js Frontend       │
                 │   Chat · Image Upload · Voice  │
                 └──────────┬───────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
   ┌─────────────────┐        ┌─────────────────────┐
   │  CV Pipeline     │        │  Blood Analytics     │
   │                  │        │                      │
   │  Upload Image    │        │  Patient Data (CSV)  │
   │       ↓          │        │       ↓              │
   │  EfficientNet-B3 │        │  20 Biomarkers       │
   │       ↓          │        │       ↓              │
   │  5 Disease Models│        │  12 Visualizations   │
   │       ↓          │        │       ↓              │
   │  Diagnosis JSON  │        │  Risk Score + Report │
   └─────────────────┘        └─────────────────────┘
```

### CV Pipeline Flow
```
Image Upload → Preprocessing (300×300) → EfficientNet-B3 → Softmax → Top-K Predictions
```

### Analytics Pipeline Flow
```
Blood Panel CSV → Synthetic Data Engine → 20 Biomarkers → Isolation Forest
                                                         → PCA Clustering
                                                         → Risk Scoring
                                                         → 12 Visualizations
```

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 16, React 19, TypeScript 5, Tailwind CSS 4, GSAP |
| **CV / Deep Learning** | PyTorch, EfficientNet-B3 (timm), torchvision, torchmetrics |
| **Data Analytics** | pandas, NumPy, SciPy, scikit-learn (Isolation Forest, PCA, StandardScaler) |
| **Visualization** | matplotlib, seaborn, Plotly (interactive gauges, radar, scatter) |
| **Graph Analysis** | NetworkX (causal DAG construction) |
| **Auth** | NextAuth.js v5 |
| **Voice** | Web Speech API, OpenAI Whisper |
| **Image Export** | Kaleido (Plotly static export) |

---

## Project Structure

```
Nidaan/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth/[...nextauth]/    # NextAuth route handler
│   │   │   └── voice/transcribe/      # Whisper transcription endpoint
│   │   ├── chat/                      # AI chat interface
│   │   ├── login/                     # Authentication page
│   │   ├── page.tsx                   # Landing page
│   │   ├── layout.tsx                 # Root layout
│   │   └── globals.css                # Global styles
│   ├── components/
│   │   ├── dashboard/
│   │   │   ├── ChatTab.tsx            # Chat interface
│   │   │   ├── ImageAnalysisTab.tsx   # Image upload + classification
│   │   │   ├── Sidebar.tsx            # Navigation
│   │   │   └── Waveform.tsx           # Audio waveform visualization
│   │   ├── AboutSection.tsx
│   │   ├── CapabilitiesSection.tsx
│   │   ├── FooterSection.tsx
│   │   ├── HoverGrid.tsx
│   │   ├── TextScramble.tsx
│   │   └── SessionProvider.tsx
│   ├── hooks/
│   │   ├── useSessions.ts
│   │   └── useVoiceInput.ts
│   └── auth.ts                        # Auth configuration
├── public/media/                      # Static assets
├── Nidaan_CV.ipynb                    # Medical imaging classifier notebook
├── nidaan_blood_analytics.ipynb       # Blood analytics notebook
├── nidaan_blood_analytics.py          # Standalone analytics script
├── package.json
├── next.config.ts
├── tsconfig.json
└── .env.example
```

---

## Getting Started

### Prerequisites

- **Node.js** ≥ 18
- **Python** ≥ 3.10
- **pip** (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/Gun4shot/Nidaan.git
cd Nidaan

# Install frontend dependencies
npm install

# Install Python dependencies
pip install torch torchvision timm torchmetrics tqdm matplotlib seaborn scikit-learn Pillow
pip install plotly scipy networkx kaleido pandas numpy

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your credentials

# Start development server
npm run dev
```

### Running the Blood Analytics (Standalone)

```bash
python nidaan_blood_analytics.py
```

Outputs 12 publication-quality visualizations to `nidaan_outputs/`:
```
01_organ_panel_summary.png       107 KB
02_reference_range_bars.png       76 KB
03_correlation_heatmap.png       208 KB
04_distribution_plots.png        381 KB
05_radar_chart.png               183 KB
06_trend_lines.png               265 KB
07_anomaly_detection.png         273 KB
08_risk_score_gauge.png          137 KB
09_pca_clustering.png            302 KB
10_population_percentile.png      60 KB
11_what_if_simulator.png         105 KB
12_causal_graph.png              374 KB
```

### Running the CV Pipeline

Open `Nidaan_CV.ipynb` in **Google Colab** (requires T4 GPU):

1. Set your Kaggle credentials when prompted
2. Run all cells — downloads 5 datasets, trains 5 EfficientNet-B3 models
3. Trained weights saved to `/content/model_weights/`
4. Use `load_model_for_inference()` + `predict()` for inference

---

## Medical Imaging Pipeline (CV)

### Datasets

| Disease | Source | Modality | Classes |
|---------|--------|----------|---------|
| Chest X-Ray | NIH Clinical Center | X-Ray | 14 pathologies |
| Brain Tumor | Masoud Nickparvar | MRI | 4 tumor types |
| COVID-19 | Tawsifur Rahman | Radiography | 4 classes |
| Malaria | Arunava | Cell Microscopy | 2 (Parasitized/Normal) |
| Bone Fracture | Madushani Rodrigo | X-Ray | Fracture/Normal |

### Training Configuration

| Parameter | Phase 1 (Head Warmup) | Phase 2 (Full Fine-Tune) |
|-----------|----------------------|--------------------------|
| Epochs | 5 | 25 (early stop patience=7) |
| Learning Rate | 1e-3 | 1e-4 (backbone), 1e-3 (head) |
| Optimizer | AdamW (weight_decay=1e-4) | AdamW (weight_decay=1e-4) |
| Scheduler | OneCycleLR | CosineAnnealingWarmRestarts |
| Input Size | 300×300 | 300×300 |
| Batch Size | 32 | 32 |
| Label Smoothing | 0.1 | 0.1 |
| Gradient Clipping | max_norm=1.0 | max_norm=1.0 |

### Model Architecture

```
EfficientNet-B3 (pretrained)
    ↓
BatchNorm1d(1536)
    ↓
Dropout(0.4)
    ↓
Linear(1536 → 512) + SiLU
    ↓
BatchNorm1d(512)
    ↓
Dropout(0.2)
    ↓
Linear(512 → num_classes)
```

---

## Blood Analytics Dashboard

### Biomarker Groups

| Group | Biomarkers |
|-------|-----------|
| **Liver Enzymes** | ALT, AST, ALP, GGT, Bilirubin |
| **Kidney** | Creatinine, BUN, UricAcid |
| **Blood Count** | Hemoglobin, WBC, Platelets, RBC, MCV |
| **Vitamins** | Vitamin D, Vitamin B12, Ferritin, Folate |
| **Metabolic** | Glucose, HbA1c, Cholesterol, Triglycerides |

### Risk Score Weights

The composite risk score (0–100) uses clinically-informed weights:

```
ALT (12%) · Glucose (12%) · AST (10%) · HbA1c (10%)
Bilirubin (8%) · Creatinine (8%) · Cholesterol (8%)
Hemoglobin (7%) · Triglycerides (7%) · Ferritin (7%)
Vitamin D (6%) · Vitamin B12 (5%)
```

### Anomaly Detection

- **Algorithm:** Isolation Forest (contamination=8%)
- **Dimensionality:** StandardScaler → 20 biomarkers
- **Visualization:** PCA 2D projection + score distribution

---

## API Reference

### Image Classification

```http
POST /predict
Content-Type: multipart/form-data

file: <image>
```

**Response:**
```json
{
  "prediction": "Parasitized",
  "confidence": 97.3,
  "top_k": [
    {"class": "Parasitized", "confidence": 97.3},
    {"class": "Uninfected", "confidence": 2.7}
  ]
}
```

### Voice Transcription

```http
POST /api/voice/transcribe
Content-Type: multipart/form-data

audio: <audio_file>
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Disclaimer

> **Nidaan is a research and educational project.** It is not a certified medical device and should not be used for actual clinical diagnosis. All disease classifications and risk scores are for demonstration purposes only. Always consult qualified healthcare professionals for medical decisions.

---

<div align="center">

**Built for healthcare innovation**

[Next.js](https://nextjs.org/) · [PyTorch](https://pytorch.org/) · [scikit-learn](https://scikit-learn.org/) · [Plotly](https://plotly.com/python/)

</div>
