from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from voice_service.app.config import settings
from voice_service.app.schemas import SynthesizeRequest, SynthesizeResponse
from voice_service.app.inference import synthesizer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: hardware and model confirmation
    telemetry = synthesizer.get_health_telemetry()
    print(f"[Voice Service] Active Engine: {telemetry['engine']} on {telemetry['device']}")
    if telemetry.get("gpu_name"):
        print(f"[Voice Service] GPU: {telemetry['gpu_name']}")
    yield


app = FastAPI(
    title="EX REVIVAL — Chatterbox Voice Service",
    description="Dedicated GPU microservice for Resemble AI Chatterbox Multilingual V3 voice synthesis",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Returns service health and live GPU hardware telemetry.
    Strictly distinguishes between real neural Chatterbox and acoustic fallback.
    """
    return synthesizer.get_health_telemetry()


@app.get("/gpu")
async def gpu_telemetry():
    """Detailed GPU compute and VRAM telemetry."""
    return synthesizer.get_health_telemetry()


@app.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(payload: SynthesizeRequest):
    """Synthesizes text into speech using reference audio clone on GPU."""
    try:
        audio_path, duration, latency_ms, engine_used = synthesizer.synthesize(
            text=payload.text,
            reference_audio_path=payload.reference_audio,
            language=payload.language or "en",
            emotion=payload.emotion or "neutral",
        )
        return SynthesizeResponse(
            status="success",
            generated_audio_path=audio_path,
            duration_seconds=duration,
            sample_rate=synthesizer.sample_rate,
            latency_ms=latency_ms,
            engine=engine_used,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice synthesis error: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("voice_service.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
