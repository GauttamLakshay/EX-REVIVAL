# EX REVIVAL — Architecture & System Design

## 1. Overview
EX REVIVAL is a voice-first AI conversational platform that resurrects emotional, high-fidelity conversational interactions through voice cloning and dynamic character synthesis. Users provide an authorized voice sample, customize the character's persona and memory context, and converse naturally in real-time through spoken speech.

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
 (Whisper/Cloud/Mock)  (OpenAI/Gemini/Mock)          │
                                                     ▼
                                            Chatterbox Service
                                               (GPU / FastAPI)
```

## 2. Audio Pipeline Flow
1. **User Speaks**: Flutter records input using microphone audio stream and uploads via multipart POST.
2. **STT (Speech-to-Text)**: Audio is transcribed with word-level/sentence-level accuracy.
3. **Context Builder**: Combines Revival character attributes, speaking style, relationship context, short-term recent conversation turns, and top-k relevant long-term memories.
4. **LLM Generation**: Prompt is executed to produce emotional, concise spoken dialogue.
5. **Chatterbox Synthesis**: Response text + reference audio sample is fed into Chatterbox Multilingual V3 to synthesize identical timbre, prosody, and emotion.
6. **Playback & Persistence**: Audio is stored in object storage/filesystem; turn metadata and latency metrics are saved in the relational database, and audio URL is returned for immediate playback.

## 3. Technology Stack
- **Frontend**: Flutter (Dart), Provider state management, JustAudio / Record plugins, Custom Audio Waveforms.
- **Backend Orchestrator**: Python 3.11+, FastAPI, SQLAlchemy Async, Pydantic v2, SQLite (dev) / PostgreSQL (prod).
- **Voice Service**: FastAPI standalone service wrapping Chatterbox Multilingual V3 neural synthesis.
- **Speech-to-Text**: Pluggable provider abstraction (`WhisperSTT`, `OpenAISTT`, `MockSTT`).
- **LLM**: Pluggable provider abstraction (`OpenAILLM`, `GeminiLLM`, `MockLLM`).
- **Database**: PostgreSQL (prod) / SQLite (dev) with UUID keys and relationship constraints.
- **Storage**: Local filesystem (dev) / AWS S3 or MinIO (prod).
