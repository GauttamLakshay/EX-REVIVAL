from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from voice_service.app.config import settings
from voice_service.app.schemas import SynthesizeRequest, SynthesizeResponse
from voice_service.app.inference import synthesizer

app = FastAPI(
    title="EX REVIVAL — Chatterbox Voice Service",
    description="Dedicated microservice for Chatterbox Multilingual V3 voice synthesis",
    version="1.0.0",
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
    return {
        "status": "ok",
        "service": "chatterbox_voice_service",
        "device": settings.MODEL_DEVICE,
        "is_model_loaded": synthesizer.is_loaded,
        "sample_rate": synthesizer.sample_rate,
    }


@app.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(payload: SynthesizeRequest):
    """Synthesizes text into speech using reference audio clone."""
    try:
        audio_path, duration, latency_ms = synthesizer.synthesize(
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
            engine="chatterbox_v3" if synthesizer.is_loaded else "chatterbox_v3_acoustic",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice synthesis error: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("voice_service.app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
