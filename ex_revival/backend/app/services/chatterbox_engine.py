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
        except Exception as e:
            # Fallback to local in-process Chatterbox synthesizer
            pass

        # 2. Local in-process synthesis fallback
        try:
            from voice_service.app.inference import synthesizer
            audio_path, duration, latency_ms = synthesizer.synthesize(
                text=text,
                reference_audio_path=reference_audio_path,
                language=language or "en",
                emotion=emotion or "neutral",
            )
            return audio_path
        except Exception as local_err:
            raise RuntimeError(f"Chatterbox voice synthesis failed: {str(local_err)}")


chatterbox_engine = ChatterboxVoiceEngine()
