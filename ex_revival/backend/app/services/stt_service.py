import io
import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple
import httpx
from app.config import get_settings

settings = get_settings()


class STTService(ABC):
    @abstractmethod
    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = "en",
    ) -> Tuple[str, int]:
        """
        Transcribes audio bytes to text.
        Returns: (transcript, latency_ms)
        """
        pass


class OpenAISTTService(STTService):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = "en",
    ) -> Tuple[str, int]:
        start = time.time()
        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {"file": (filename, audio_bytes, "audio/wav")}
        data = {"model": "whisper-1"}
        if language:
            data["language"] = language

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, files=files, data=data)
            if resp.status_code != 200:
                raise RuntimeError(f"OpenAI STT error ({resp.status_code}): {resp.text}")
            transcript = resp.json().get("text", "")
            latency_ms = int((time.time() - start) * 1000)
            return transcript, latency_ms


class MockSTTService(STTService):
    def __init__(self):
        self._sample_transcripts = [
            "Hey, how are you?",
            "What are you up to today?",
            "I missed hearing your voice.",
            "Can you tell me about the project you were working on?",
            "It's so good to talk to you again.",
        ]
        self._counter = 0

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        language: Optional[str] = "en",
    ) -> Tuple[str, int]:
        start = time.time()
        # Realistic slight processing latency simulation
        time.sleep(0.08)
        # Select transcript deterministically or in cycle
        transcript = self._sample_transcripts[self._counter % len(self._sample_transcripts)]
        self._counter += 1
        latency_ms = int((time.time() - start) * 1000)
        return transcript, latency_ms


def get_stt_service() -> STTService:
    provider = settings.STT_PROVIDER.lower()
    if provider == "openai" and settings.STT_API_KEY:
        return OpenAISTTService(api_key=settings.STT_API_KEY)
    return MockSTTService()


stt_service = get_stt_service()
