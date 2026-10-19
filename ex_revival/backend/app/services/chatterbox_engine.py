import os
import time
from typing import Optional
from pathlib import Path
import httpx
from app.config import get_settings
from app.services.voice_engine import VoiceEngine

settings = get_settings()


class ChatterboxVoiceEngine(VoiceEngine):
    def __init__(self):
        self.service_url = settings.VOICE_SERVICE_URL.rstrip("/")
        self.timeout = 300.0  # Allow up to 5 minutes for CPU neural inference
        self.last_telemetry: Optional[dict] = None

    async def get_health_telemetry(self) -> dict:
        """Queries the standalone voice microservice for live model and hardware telemetry."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.service_url}/health")
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            return {
                "status": "error",
                "device": "unknown",
                "model_loaded": False,
                "engine": "unavailable",
                "model_version": None,
                "sample_rate": 0,
                "detail": str(e),
            }

    async def synthesize(
        self,
        text: str,
        reference_audio_path: str,
        language: Optional[str] = "en",
        emotion: Optional[str] = "neutral",
        exaggeration: Optional[float] = 0.72,
        cfg_weight: Optional[float] = 0.68,
        temperature: Optional[float] = 0.80,
        pitch_shift_semitones: Optional[float] = 0.0,
        tempo_scale: Optional[float] = 1.0,
    ) -> str:
        """
        Synthesizes speech using Chatterbox Multilingual V3.
        Communicates with the standalone voice microservice with affect retargeting.
        """
        payload = {
            "text": text,
            "reference_audio": reference_audio_path,
            "language": language or "en",
            "emotion": emotion or "neutral",
            "exaggeration": exaggeration if exaggeration is not None else 0.72,
            "cfg_weight": cfg_weight if cfg_weight is not None else 0.68,
            "temperature": temperature if temperature is not None else 0.80,
            "pitch_shift_semitones": pitch_shift_semitones if pitch_shift_semitones is not None else 0.0,
            "tempo_scale": tempo_scale if tempo_scale is not None else 1.0,
        }

        # 1. External voice microservice (primary neural path)
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.service_url}/synthesize", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    self.last_telemetry = data
                    return data["generated_audio_path"]
                else:
                    raise RuntimeError(f"Voice microservice returned error ({resp.status_code}): {resp.text}")
        except Exception as e:
            # If production, or if strict neural voice is required, fail loudly
            if settings.APP_ENV == "production" or not settings.MOCK_AI or os.environ.get("REQUIRE_NEURAL_VOICE") == "true":
                raise RuntimeError(f"Neural voice microservice unreachable or failed: {str(e)}")

        # 2. Local fallback only when explicitly permitted in development mode
        if os.environ.get("REQUIRE_NEURAL_VOICE") == "true":
            raise RuntimeError("REQUIRE_NEURAL_VOICE is enabled; acoustic fallback is strictly prohibited.")

        try:
            from voice_service.app.inference import synthesizer
            res = synthesizer.synthesize(
                text=text,
                reference_audio_path=reference_audio_path,
                language=language or "en",
                emotion=emotion or "neutral",
            )
            self.last_telemetry = {
                "status": "fallback",
                "generated_audio_path": res[0],
                "duration_seconds": res[1],
                "latency_ms": res[2],
                "engine": res[3] if len(res) > 3 else "acoustic_fallback",
            }
            return res[0]
        except Exception as local_err:
            raise RuntimeError(f"Chatterbox voice synthesis failed: {str(local_err)}")


chatterbox_engine = ChatterboxVoiceEngine()
