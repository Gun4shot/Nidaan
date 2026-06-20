# MedAI — Flutter Frontend

AI-powered medical assistant mobile application. Connects to a FastAPI backend
serving Llama 3 (chat), a disease ML classifier, and a computer vision model.

---

## Project Structure

```
mobile/lib/
├── core/
│   ├── constants/   app_constants.dart   — API URLs, keys, config
│   └── theme/       app_theme.dart       — colors, typography, Material 3 theme
│
├── models/
│   ├── chat_model.dart       ChatMessage, MessageRole, MessageStatus
│   ├── disease_model.dart    Symptom, DiseaseResult, DiagnosisReport
│   └── scan_model.dart       ScanResult, ScanType
│
├── services/
│   ├── api_service.dart       Single HTTP gateway (Dio) — chat, predict, scan
│   └── websocket_service.dart WebSocket streaming client for live LLM tokens
│
├── providers/
│   ├── chat_provider.dart     Riverpod StateNotifier — chat + streaming state
│   └── diagnosis_provider.dart  disease prediction + scan upload state
│
├── screens/
│   ├── root_scaffold.dart    Bottom nav shell (IndexedStack)
│   ├── home/                 Dashboard + quick-access cards
│   ├── chat/                 Streaming AI chat (ChatGPT-style)
│   ├── diagnosis/            Symptom picker + ranked disease results
│   ├── scan/                 Image upload + AI vision result
│   ├── history/              Past chats & diagnoses (tabbed)
│   └── profile/              Settings, stats, sign out
│
├── widgets/
│   ├── chat_bubble.dart      Message bubbles with typing animation
│   └── shared_widgets.dart   GradientButton, ConfidenceBar, SeverityBadge,
│                             SectionHeader, StateCard
└── main.dart
```

---

## Setup

### 1. Install dependencies
```bash
cd mobile
flutter pub get
```

### 2. Configure backend URL
Edit `lib/core/constants/app_constants.dart`:

```dart
static const String baseUrl = 'http://10.0.2.2:8000'; // Android emulator
// static const String baseUrl = 'http://localhost:8000'; // iOS simulator
// static const String baseUrl = 'https://your-api.com'; // Production
```

### 3. Run
```bash
flutter run
```

---

## Architecture

```
Flutter App
     │
     │  HTTPS (Dio) + WebSocket
     ▼
FastAPI Backend
     │
 ┌───┴─────────────────┐
 │                     │
 ▼                     ▼
LLM Service       Vision + ML
(Llama 3 chat)   (CNN/ViT classify)
```

**Rule:** Frontend never calls the model directly.
`Frontend → Backend → Model` always.

---

## Key Design Decisions

### State Management: Riverpod
- `chatProvider`      — `StateNotifier<ChatState>`
- `diagnosisProvider` — `StateNotifier<DiagnosisState>`
- `scanProvider`      — `StateNotifier<ScanState>`

No `setState()` spaghetti. Every screen reads from its provider.

### Chat: WebSocket Streaming
- `WebSocketService` connects to `/ws/chat`
- Backend streams tokens one by one
- `ChatNotifier` appends tokens to the streaming message in real-time
- `[END]` sentinel marks completion

### Request States
Every async operation cycles through:
`idle → loading → streaming/success → error`

UI reacts to each state: skeleton → indicator → result → error card.

---

## API Endpoints (FastAPI)

| Method | Path       | Description               |
|--------|------------|---------------------------|
| POST   | /chat      | Non-streaming chat fallback|
| WS     | /ws/chat   | Streaming token delivery  |
| POST   | /predict   | Disease prediction        |
| POST   | /scan      | Medical image upload      |
| GET    | /history   | User chat/diagnosis history|
| GET    | /health    | Backend health check      |

---

## Color Palette

| Token          | Hex       | Usage                       |
|----------------|-----------|-----------------------------|
| background     | `#0A0E1A` | Scaffold bg (near-black navy)|
| surface        | `#111827` | Card backgrounds             |
| surfaceElevated| `#1C2539` | Input fields, raised panels  |
| primary        | `#1A7FE8` | Medical blue — CTAs          |
| accent         | `#00D4C8` | Bioluminescent cyan — active |
| accentGreen    | `#22C55E` | Healthy / success            |
| accentWarning  | `#F59E0B` | Caution / moderate severity  |
| accentDanger   | `#EF4444` | Critical / severe            |

---

## Next Steps

- [ ] Implement authentication (JWT + `auth_service.dart`)
- [ ] Wire history screen to `GET /history`
- [ ] Add push notifications for long-running predictions
- [ ] Enable local chat persistence with Hive
- [ ] Add markdown rendering to chat bubbles (flutter_markdown)
- [ ] Add pull-to-refresh on history
- [ ] Write widget tests for providers
