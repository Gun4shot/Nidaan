# Nidaan

AI-powered medical intelligence platform. Free, open source, 13 languages. No sign-up, no tracking, no ads.

## What is this

Nidaan is a medical AI web application that provides:

- **AI Consultation** — Chat with a fine-tuned medical LLM grounded in WHO, CDC, and NHS guidelines
- **Image Analysis** — Upload medical images (X-rays, scans) for AI-assisted diagnostics
- **Blood Analytics** — Generate 12 visualizations from blood test datasets (organ panels, correlation heatmaps, anomaly detection, risk scores, PCA clustering)
- **Voice Input** — Speak your symptoms in any of 13 supported languages via Web Speech API + Whisper fallback
- **Health Tracking** — Medications, vitals, appointments, EHR export

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, TypeScript |
| Styling | Vanilla CSS, Hanken Grotesk, Material Symbols |
| Animation | GSAP (ScrollTrigger, clip-path reveals, text scramble) |
| Auth | NextAuth.js v5 with Google OAuth |
| Voice | Web Speech API (primary) + Whisper via HuggingFace (fallback) |
| State | React hooks + localStorage (sessions, patient data, preferences) |
| Analytics Backend | Python Flask API, matplotlib, plotly, scikit-learn, seaborn |
| Design System | Obsidian Mono (extreme minimalism, black/white, sharp edges) |

## Project Structure

```
├── src/
│   ├── app/
│   │   ├── page.tsx                 # Landing page (HoverGrid animations)
│   │   ├── login/page.tsx           # Google OAuth login
│   │   ├── chat/page.tsx            # Dashboard (Consult, Imaging, Analytics)
│   │   └── api/
│   │       ├── auth/[...nextauth]/  # NextAuth Google provider
│   │       └── voice/transcribe/    # Whisper transcription proxy
│   ├── components/
│   │   ├── HoverGrid.tsx            # Landing with GSAP scroll animations
│   │   ├── AboutSection.tsx         # Scroll snap section with text scramble
│   │   ├── TextScramble.tsx         # Animated text reveal component
│   │   └── dashboard/
│   │       ├── Sidebar.tsx          # Collapsible session list (resizable)
│   │       ├── ChatTab.tsx          # Consult chat with voice input
│   │       ├── ImageAnalysisTab.tsx # Split view (resizable) + chat
│   │       ├── AnalyticsTab.tsx     # Python backend integration
│   │       ├── PatientIntake.tsx    # Patient info modal (name, age, gender)
│   │       └── Waveform.tsx         # Audio frequency visualizer
│   ├── hooks/
│   │   ├── useSessions.ts           # Session CRUD + localStorage
│   │   └── useVoiceInput.ts         # Dual voice engine hook
│   └── auth.ts                      # NextAuth configuration
├── backend/
│   └── server.py                    # Flask API for blood analytics
├── nidaan_blood_analytics.py        # Python data pipeline (2000 patients, 12 viz)
└── public/media/                    # Images, videos, backgrounds
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+ (for analytics backend)
- Google Cloud Console OAuth credentials

### 1. Clone

```bash
git clone https://github.com/Gun4shot/Nidaan.git
cd Nidaan
```

### 2. Install Frontend

```bash
npm install
```

### 3. Install Python Dependencies

```bash
pip install flask flask-cors numpy pandas matplotlib seaborn plotly scikit-learn scipy networkx kaleido
```

### 4. Environment Variables

Copy `.env.example` to `.env.local`:

```bash
cp .env.example .env.local
```

Fill in:

```
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
NEXTAUTH_SECRET=run-openssl-rand-base64-32
NEXTAUTH_URL=http://localhost:3000
HUGGINGFACE_TOKEN=hf_your_token_here
```

**Google OAuth setup:**
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Set Authorized redirect URI: `http://localhost:3000/api/auth/callback/google`

**HuggingFace token (for voice fallback):**
1. Go to https://huggingface.co/settings/tokens
2. Create a free Read token

### 5. Run

```bash
# Terminal 1 — Frontend
npm run dev

# Terminal 2 — Analytics backend (optional)
python backend/server.py
```

Open http://localhost:3000

## Features

### Landing Page
- GSAP scroll animations with clip-path image reveals
- Scroll snap sections (landing, about, footer)
- Background video crossfade on scroll
- Text scramble animation on about section
- Film grain overlay

### Dashboard
- **3 tabs**: Consult, Imaging, Analytics
- **Tab switcher** with sliding pill indicator
- **Dark mode** toggle (persisted in localStorage)
- **Collapsible sidebar** with resizable width
- **Session management**: create, rename (right-click), delete
- **Patient intake modal**: name, age, gender on new session
- **Settings panel**: language, voice input, notifications
- **Profile panel**: Google account info, sign out

### Consult Tab
- Chat interface with message bubbles
- Voice input (real-time transcription, words appear as you speak)
- Copy button on message hover
- Welcome message personalized with patient name

### Imaging Tab
- 50/50 resizable split (drag handle between panels)
- Image upload with thumbnail strip
- 3 view modes: Single, Grid, Compare
- Zoom controls
- Image removal (toolbar button + thumbnail X button)
- Voice input on the chat panel
- Copy button on messages

### Analytics Tab
- Upload CSV dataset or load existing
- Python backend generates 12 visualizations:
  - Organ Panel Summary
  - Reference Range Bars
  - Correlation Heatmap
  - Distribution Plots (violin + KDE)
  - Patient Radar Chart
  - Trend Lines Over Time
  - Anomaly Detection (Isolation Forest)
  - Composite Risk Score Gauge
  - PCA Clustering
  - Population Percentile Rank
  - What-If Simulator
  - Biomarker Causal Graph (DAG)
- Download individual PNGs or all as ZIP
- Download dataset CSV
- State persists across tab switches

### Voice Input
- **Web Speech API**: browser-native, real-time interim transcription
- **Whisper fallback**: HuggingFace free inference API for unsupported browsers/languages
- Waveform visualization during recording
- Works on both Consult and Imaging tabs

## Design System

Obsidian Mono — extreme minimalism:

- **Colors**: `#000000` background, `#ffffff` foreground, `#808080` muted
- **Font**: Hanken Grotesk (all weights)
- **Icons**: Material Symbols Outlined
- **Corners**: Sharp (0px), no shadows, flat layering
- **Labels**: 11px, 600 weight, 0.15em letter-spacing, uppercase
- **Dark mode**: `#121414` background, `#e3e2e2` text, full component coverage

## License

Apache 2.0 — use it, modify it, deploy it, share it. Free forever.
