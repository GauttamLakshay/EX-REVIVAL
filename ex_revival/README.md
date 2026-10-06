# EX REVIVAL — AI Voice-Recreated Conversational Experience

> Voice-first AI application where emotional presence meets neural voice cloning.

---

## 1. Overview
EX REVIVAL is a voice-first AI conversational platform. Users upload or record an authorized reference voice sample, configure the character's persona, speaking nuance, and relationship context, and engage in real-time spoken dialogue with fluid speech-to-text, context-aware LLM reasoning, and neural voice synthesis powered by Chatterbox Multilingual V3.

```
USER SPEAKS (Mic)
      ↓
SPEECH-TO-TEXT (STT)
      ↓
LLM REASONING (+ Personality & Long-Term Memories)
      ↓
RESPONSE TEXT
      ↓
CHATTERBOX VOICE SYNTHESIS (Reference Voice Sample)
      ↓
USER HEARS RESPONSE (Playback)
```

---

## 2. Monorepo Architecture

```text
ex_revival/
├── frontend/             # Flutter + Dart client application
├── backend/              # FastAPI AI orchestration backend
├── voice_service/        # Chatterbox GPU voice synthesis microservice
├── storage/              # Local storage for reference & generated audio
├── docs/                 # Architectural specifications and diagrams
├── scripts/              # Setup, utility, and runner scripts
├── .gitignore
├── README.md
└── docker-compose.yml
```

### Architectural Diagram

```
                 FLUTTER APP (Audio In / Audio Out)
                               │
                             HTTPS
                               │
                               ▼
                      FASTAPI ORCHESTRATOR
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
    STT Service           LLM Service          Voice Engine
(Whisper/Cloud/Mock)   (OpenAI/Gemini/Mock)          │
                                                     ▼
                                            Chatterbox Service
                                               (GPU / FastAPI)
                                                     │
                                            ┌────────┴────────┐
                                            │ Database: PG/SQL│
                                            │ Storage: S3/Disk│
                                            └─────────────────┘
```

---

## 3. Requirements
- **Python**: 3.10+ (Tested on Python 3.11 - 3.13)
- **Flutter**: 3.22+ / 3.41+
- **Docker & Docker Compose**: Optional for containerized deployment
- **FFmpeg**: Required for audio transcoding and validation

---

## 4. Quick Start (Development)

### A. Backend Setup
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### B. Voice Service Setup
```bash
cd voice_service
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### C. Frontend Setup
```bash
cd frontend
flutter pub get
flutter run
```

---

## 5. Environment Variables

### Backend (`backend/.env`)
| Variable | Description | Default |
|---|---|---|
| `APP_ENV` | Application environment (`development` / `production`) | `development` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite+aiosqlite:///./ex_revival.db` |
| `JWT_SECRET` | Secret key for JWT signing | `super_secret_jwt_key...` |
| `VOICE_SERVICE_URL` | Chatterbox microservice URL | `http://localhost:8001` |
| `STT_PROVIDER` | STT provider (`whisper`, `openai`, `mock`) | `mock` |
| `LLM_PROVIDER` | LLM provider (`openai`, `gemini`, `mock`) | `mock` |
| `STORAGE_PROVIDER` | Audio storage (`local`, `s3`) | `local` |
| `MOCK_AI` | Fallback flag for development without GPU | `true` |

### Voice Service (`voice_service/.env`)
| Variable | Description | Default |
|---|---|---|
| `PORT` | Listening port | `8001` |
| `MODEL_DEVICE` | Compute device (`cpu`, `cuda`) | `cpu` |
| `USE_MOCK_FALLBACK` | Safe fallback if model weights missing | `true` |

---

## 6. API Documentation
Once the backend is running, interactive API documentation is accessible at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 7. Automated Testing
Run the comprehensive test suite:
```bash
cd backend
pytest -v
```

---

## 8. License & Safety Notice
EX REVIVAL requires explicit authorization before utilizing any human voice sample. Ethical AI safety controls are enforced at creation time.
