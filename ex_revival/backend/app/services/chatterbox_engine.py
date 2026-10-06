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
        self.timeout = 60.0

    async def synthesize(
        self,
        text: str,
        reference_audio_path: str,
        language: Optional[str] = "en",
        emotion: Optional[str] = "neutral",
    ) -> str:
        """
        Synthesizes speech using Chatterbox Multilingual V3.
        First attempts HTTP request to standalone voice_service microservice.
        Falls back seamlessly to local engine if microservice is offline.
        """
        payload = {
            "text": text,
            "reference_audio": reference_audio_path,
            "language": language or "en",
            "emotion": emotion or "neutral",
        }

        # 1. Try external GPU microservice
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(f"{self.service_url}/synthesize", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["generated_audio_path"]
                elif settings.APP_ENV == "production" and not settings.MOCK_AI:
                    raise RuntimeError(f"Voice microservice returned error ({resp.status_code}): {resp.text}")
        except Exception as e:
            if settings.APP_ENV == "production" and not settings.MOCK_AI:
                raise RuntimeError(f"Voice service microservice unreachable in production mode: {str(e)}")
            pass

        # 2. Local in-process synthesis fallback (development only)
        if settings.APP_ENV == "production" and not settings.MOCK_AI:
            raise RuntimeError("External GPU voice microservice required in production mode. Silent fallback is prohibited.")
        try:
            from voice_service.app.inference import synthesizer
            res = synthesizer.synthesize(
                text=text,
                reference_audio_path=reference_audio_path,
                language=language or "en",
                emotion=emotion or "neutral",
            )
            return res[0]
        except Exception as local_err:
            raise RuntimeError(f"Chatterbox voice synthesis failed: {str(local_err)}")


chatterbox_engine = ChatterboxVoiceEngine()
