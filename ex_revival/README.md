# EX REVIVAL — The Affect-Disentangled Personality & Neural Voice Copier

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Flutter-3.22+-02569B.svg?logo=flutter)](https://flutter.dev)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.6.0-EE4C2C.svg?logo=pytorch)](https://pytorch.org)
[![Chatterbox Multilingual V3](https://img.shields.io/badge/TTS-Chatterbox%20V3-7928CA.svg)](https://github.com/resemble-ai/chatterbox)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **EX REVIVAL** is a voice-first conversational AI monorepo that transcends traditional robotic voice cloning. By mathematically disentangling **Physiological Vocal Invariants** (throat geometry, native accent phonemes) from **Transient Affect States** (excitement, sadness, intimacy), EX REVIVAL clones a living human personality — capable of whispering, crying, comforting, or bantering with authentic pacing and emotional weight, regardless of the mood of the reference audio sample.

---

## 🌟 Key Breakthroughs

### 1. The Emotional Trapping Problem — Solved
Traditional zero-shot TTS models bake in whatever mood was present in the 15-second reference audio. If a user uploads an audio note of someone laughing or excited, naive cloning will render even heartbreaking or somber dialogue with a manic, robotic cheerfulness (*"The Agent Redhead Problem"*).

**The EX REVIVAL Solution: The Disentanglement Architecture**
* **Physiological Invariants (Layer 1):** Vocal tract geometry, formant frequencies ($F_1, F_2, F_3$), resting fundamental pitch ($F_0$), and native articulatory phonetics. These **never change**, even when sobbing or screaming.
* **Transient Affect (Layer 2):** Current emotional phase. Dynamically modulates glottal closure (breathiness), pitch excursion ($F_0$ delta), cadence, pause distribution, and syllable duration.
* **Result:** From a single 20-second clip recorded in high excitement, EX REVIVAL authentically synthesizes their genuine quiet, vulnerable, melancholic sad voice with their exact throat, skull resonance, and accent.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   THE AFFECT DISENTANGLEMENT ENGINE                    │
├───────────────────────────────────┬────────────────────────────────────┤
│ 1. Physiological Throat Identity  │ 2. Real-Time Emotional Director    │
│    • Vocal tract length & formants│    • Pitch level (F0 shifts ±40 Hz)│
│    • Native accent & tongue stops │    • Syllable speed (WPM scaling)  │
│    • Dental 'त' vs English 't'    │    • Glottal breath leakage (sighs)│
│    ⚡ INVARIANT ACROSS EMOTIONS    │    ⚡ DYNAMICALLY MODULATED BY MOOD │
└───────────────────────────────────┴────────────────────────────────────┘
```

### 2. Native Indic & Devanagari Phonetic Engine
When generating Hindi/Hinglish speech, Romanized text (`"tum kaise ho"`) defaults TTS tokenizers to Western aspirated alveolar plosives (`/tʰ/`), sounding like a foreign robot. EX REVIVAL enforces automated Devanagari phonetic routing (`"तुम कैसे हो"`), activating authentic native Indian dental phonemes (soft dental `/t̪/` in `तुम`), nasalized matras, and authentic subcontinent cadence.

### 3. The Cognitive Director (Real-Time Emotional State Machine)
Every conversation turn is analyzed for emotional context:
* **Sadness / Comfort:** Flattens pitch variance (`exaggeration: 0.38`), drops guidance (`cfg_weight: 0.48`) to detach from excited reference energy, shifts pitch into chest register (`-2.2` semitones), and slows tempo by 18%.
* **Celebration / Hyped:** Boosts pitch dynamics (`exaggeration: 0.85`), tightens guidance (`cfg_weight: 0.74`), and accelerates tempo.
* **Script Acting:** Injects ellipsis micro-pauses (`...`) to create genuine biological inhalations and hesitations.

---

## 🏗 System Architecture

```mermaid
flowchart TD
    subgraph Client["Flutter Mobile Application (Android / iOS)"]
        UI["Voice Call / Chat UI"] --> Rec["Audio Recorder (Opus/WAV)"]
        Play["Audio Player + Reactive Visualizer"] <-- URL["Streamed Audio URL"]
    end

    subgraph Backend["FastAPI Cognitive Orchestrator (:8000)"]
        STT["STT Service (Gemini 3.5 Transcribe / Whisper)"]
        Mem["Long-Term Episodic Memory Service"]
        Director["Cognitive Emotional Director"]
        LLM["Screenwriter LLM (Gemini 3.1 / GPT-4o)"]
        Profile["Personality DNA Service"]
        DB[("SQLite / PostgreSQL Database")]

        Rec --> STT
        STT --> Director
        Director & Mem --> LLM
        LLM --> Engine["Chatterbox Engine Client"]
        Profile <--> DB
    end

    subgraph VoiceService["Chatterbox Neural Microservice (:8001)"]
        V3["Official Chatterbox Multilingual V3"]
        DSP["AffectShaper (F0 Retargeting, Glottal Damping)"]
        Watermark["Perth Invisible Audio Watermarking"]

        Engine --> V3
        V3 --> DSP
        DSP --> Watermark
        Watermark --> Output["Storage (:8000/storage/...)"]
    end

    Output --> URL
```

---

## 📂 Monorepo Structure

```text
ex_revival/
├── backend/                  # FastAPI Core Orchestrator
│   ├── app/
│   │   ├── api/v1/           # Auth, Revivals, Conversations, Memories, Health
│   │   ├── models/           # SQLAlchemy ORM (Revival, User, Message, VoiceAsset)
│   │   ├── schemas/          # Pydantic v2 validation contracts
│   │   ├── services/
│   │   │   ├── cognitive_director.py   # Real-time affect & prosody state machine
│   │   │   ├── personality_service.py  # Behavioral & acoustic DNA profiler
│   │   │   ├── chatterbox_engine.py    # Voice microservice client
│   │   │   ├── llm_service.py          # Script acting & Devanagari prompt engine
│   │   │   ├── stt_service.py          # Multilingual speech transcription
│   │   │   ├── audio_service.py        # FIR anti-aliased resampling & DSP
│   │   │   └── memory_service.py       # Vector/episodic memory retrieval
│   │   └── config.py         # Type-safe environment settings
│   └── tests/                # Automated pytest suite
│
├── voice_service/            # Chatterbox Neural Voice Microservice
│   ├── app/
│   │   ├── affect_shaper.py  # DSP pitch shifting, glottal filter & F0 analyzer
│   │   ├── inference.py      # Resemble AI Chatterbox Multilingual V3 runner
│   │   ├── schemas.py        # Microservice request/response contracts
│   │   └── main.py           # FastAPI server on port 8001
│   └── models/               # Neural checkpoints (.pt, .safetensors)
│
├── frontend/                 # Flutter Cross-Platform Application
│   ├── lib/
│   │   ├── core/             # Theme, animations, API routing
│   │   ├── models/           # Dart data models (Revival, Conversation, Message)
│   │   ├── providers/        # State management (Conversation, Auth, Revival)
│   │   ├── screens/          # Call screen, Revival creator, History
│   │   ├── services/         # Audio recording, playback, REST client
│   │   └── widgets/          # Interactive waveform player, pulsing mic
│   └── pubspec.yaml
│
├── storage/                  # Audio storage (reference_audio, generated_audio)
└── scripts/                  # Automated setup, verification & benchmark scripts
```

---

## 🚀 Quick Start Guide

### Prerequisites
* **Python**: 3.10 to 3.13
* **Flutter SDK**: 3.22+
* **FFmpeg**: Required for audio normalization
* **CUDA GPU** (Optional): Voice service runs on CUDA or CPU with auto-detection.

---

### Step 1: Voice Microservice Setup

```bash
cd voice_service
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# Download Chatterbox V3 weights (or use official auto-download):
python ../scripts/download_chatterbox_weights.py

# Start voice microservice on port 8001:
uvicorn voice_service.app.main:app --host 0.0.0.0 --port 8001
```

---

### Step 2: Backend Orchestrator Setup

```bash
cd backend
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# Configure your environment:
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (and optional JWT_SECRET)

# Launch backend API on port 8000:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Step 3: Mobile Frontend Setup

```bash
cd frontend
flutter pub get

# Connect Android device or start emulator:
flutter run
```

*For physical Android devices over USB, enable ADB reverse port forwarding:*
```bash
adb reverse tcp:8000 tcp:8000
adb reverse tcp:8001 tcp:8001
```

---

## ⚙️ Environment Configuration

### Backend (`backend/.env`)

```ini
APP_ENV=development
DEBUG=true
PORT=8000
HOST=0.0.0.0

# Database
DATABASE_URL=sqlite+aiosqlite:///./ex_revival.db

# Authentication
JWT_SECRET=super_secret_jwt_key_change_in_prod
ACCESS_TOKEN_EXPIRE_MINUTES=525600

# Voice Service Microservice
VOICE_SERVICE_URL=http://localhost:8001
VOICE_ENGINE_PROVIDER=chatterbox

# AI Providers
STT_PROVIDER=gemini
GEMINI_STT_MODEL=gemini-3.5-transcribe
LLM_PROVIDER=gemini
GEMINI_LLM_MODEL=gemini-3.1-flash-lite
GEMINI_API_KEY=your_gemini_api_key_here

MOCK_AI=false
```

---

## 🧪 Benchmark Verification

Run the end-to-end cross-emotional test suite:

```bash
cd backend
pytest tests/ -v
```

### Acoustic Disentanglement Benchmark Results
Measured from a single high-energy reference voice sample (`tsunami`):

| Test Condition | Emotion Phase | Base $F_0$ | $F_0$ Std Dev | Exaggeration | CFG Weight | Audio Output |
|---|---|---|---|---|---|---|
| **Original Audio Note** | Excited / Hyped | 276.0 Hz | 70.5 Hz | — | — | Baseline Reference |
| **Consoling / Sad Turn** | `sadness_comfort` | **243.3 Hz** | **48.4 Hz** | **0.38** | **0.48** | Quiet, intimate, chest tone |
| **Celebratory Turn** | `celebration_hyped`| **284.1 Hz** | **78.2 Hz** | **0.85** | **0.74** | High-energy, punchy lilt |

---

## 🛡 Ethics, Safety & Audio Watermarking

1. **Explicit Voice Rights Authorization:** Every Revival profile requires explicit user consent before a reference audio sample can be synthesized.
2. **Perth Invisible Watermarking:** All generated audio waveforms are embedded with imperceptible Perth neural watermarks directly at the vocoder level to protect against unauthorized spoofing.
3. **No Impersonation Clause:** Prompts enforce strict psychological companionship boundaries and prohibit legal/financial impersonation.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
