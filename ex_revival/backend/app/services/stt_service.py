import os
import io
import time
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union
import httpx
from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger("ex_revival.stt")


def _detect_mime_type(filename: str, audio_bytes: bytes) -> str:
    fn = filename.lower()
    if fn.endswith(".mp3"):
        return "audio/mp3"
    elif fn.endswith(".ogg") or fn.endswith(".opus"):
        return "audio/ogg"
    elif fn.endswith(".m4a") or fn.endswith(".aac"):
        return "audio/mp4"
    elif fn.endswith(".webm"):
        return "audio/webm"
    elif fn.endswith(".flac"):
        return "audio/flac"
    elif audio_bytes.startswith(b"RIFF"):
        return "audio/wav"
    elif audio_bytes.startswith(b"ID3") or audio_bytes.startswith(b"\xff\xfb") or audio_bytes.startswith(b"\xff\xf3"):
        return "audio/mp3"
    elif audio_bytes.startswith(b"OggS"):
        return "audio/ogg"
    elif audio_bytes.startswith(b"\x1a\x45\xdf\xa3"):
        return "audio/webm"
    return "audio/wav"


class STTService(ABC):
    @abstractmethod
    async def transcribe(
        self,
        audio_input: Optional[Union[bytes, str]] = None,
        filename: str = "audio.wav",
        language: Optional[str] = "en",
        audio_bytes: Optional[bytes] = None,
        audio_path: Optional[str] = None,
    ) -> Tuple[str, int]:
        """
        Transcribes audio to text.
        Accepts raw audio_bytes or audio_path / filename.
        Returns: (transcript, latency_ms)
        """
        pass


class GeminiSTTService(STTService):
    def __init__(self, api_key: str, model: str = "gemini-3.5-transcribe"):
        if not api_key:
            raise RuntimeError("STT_CONFIGURATION_ERROR: GEMINI_API_KEY is required for GeminiSTTService")
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=self.api_key)

    async def transcribe(
        self,
        audio_input: Optional[Union[bytes, str]] = None,
        filename: str = "audio.wav",
        language: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        audio_path: Optional[str] = None,
    ) -> Tuple[str, int]:
        start = time.time()

        # Resolve raw bytes from whichever argument was passed
        raw_bytes = audio_bytes
        if raw_bytes is None and audio_input is not None:
            if isinstance(audio_input, bytes):
                raw_bytes = audio_input
            elif isinstance(audio_input, str):
                if os.path.exists(audio_input):
                    with open(audio_input, "rb") as f:
                        raw_bytes = f.read()
                    filename = os.path.basename(audio_input)
                else:
                    raise RuntimeError(f"STT_FAILED: Audio file not found: {audio_input}")
        elif raw_bytes is None and audio_path is not None:
            if os.path.exists(audio_path):
                with open(audio_path, "rb") as f:
                    raw_bytes = f.read()
                filename = os.path.basename(audio_path)
            else:
                raise RuntimeError(f"STT_FAILED: Audio file not found: {audio_path}")

        if not raw_bytes or len(raw_bytes) == 0:
            raise RuntimeError("STT_FAILED: No audio data provided for transcription")

        mime_type = _detect_mime_type(filename, raw_bytes)

        prompt_instruction = (
            "Accurately transcribe the spoken audio verbatim. "
            "Return ONLY the transcribed text. "
            "Do not output markdown formatting, quotation marks, timestamps, speaker labels, or introductory commentary. "
            "Properly recognize speech in English, Hindi, and Hinglish/code-switching."
        )
        if language and language.lower() not in ("auto", "none", "", "en"):
            prompt_instruction += f" Expected language context: {language}."

        audio_part = types.Part.from_bytes(data=raw_bytes, mime_type=mime_type)
        contents = [audio_part, prompt_instruction]
        config = types.GenerateContentConfig(
            temperature=0.0,
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            transcript = ""
            if response.candidates:
                for cand in response.candidates:
                    if cand.content and cand.content.parts:
                        for p in cand.content.parts:
                            trans_obj = getattr(p, "audio_transcription", None)
                            if trans_obj and getattr(trans_obj, "text", None):
                                transcript += trans_obj.text
                            elif p.text:
                                transcript += p.text
            if not transcript and response.text:
                transcript = response.text
            transcript = transcript.strip()
            if (transcript.startswith('"') and transcript.endswith('"')) or (transcript.startswith("'") and transcript.endswith("'")):
                transcript = transcript[1:-1].strip()
            latency_ms = int((time.time() - start) * 1000)
            return transcript, latency_ms
        except Exception as e:
            err_str = str(e)
            if ("404" in err_str or "not found" in err_str.lower() or "NOT_FOUND" in err_str or "503" in err_str or "UNAVAILABLE" in err_str) and self.model != "gemini-3.1-flash-lite":
                logger.warning(f"STT Model '{self.model}' unavailable or not found; falling back to gemini-3.1-flash-lite: {e}")
                try:
                    fallback_response = await self.client.aio.models.generate_content(
                        model="gemini-3.1-flash-lite",
                        contents=contents,
                        config=config,
                    )
                    transcript = ""
                    if fallback_response.candidates:
                        for cand in fallback_response.candidates:
                            if cand.content and cand.content.parts:
                                for p in cand.content.parts:
                                    trans_obj = getattr(p, "audio_transcription", None)
                                    if trans_obj and getattr(trans_obj, "text", None):
                                        transcript += trans_obj.text
                                    elif p.text:
                                        transcript += p.text
                    if not transcript and fallback_response.text:
                        transcript = fallback_response.text
                    transcript = transcript.strip()
                    if (transcript.startswith('"') and transcript.endswith('"')) or (transcript.startswith("'") and transcript.endswith("'")):
                        transcript = transcript[1:-1].strip()
                    latency_ms = int((time.time() - start) * 1000)
                    return transcript, latency_ms
                except Exception as fb_err:
                    raise RuntimeError(f"STT_FAILED: Gemini STT transcription failed: {fb_err}")
            raise RuntimeError(f"STT_FAILED: Gemini STT error: {e}")


class OpenAISTTService(STTService):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def transcribe(
        self,
        audio_input: Optional[Union[bytes, str]] = None,
        filename: str = "audio.wav",
        language: Optional[str] = "en",
        audio_bytes: Optional[bytes] = None,
        audio_path: Optional[str] = None,
    ) -> Tuple[str, int]:
        start = time.time()
        raw_bytes = audio_bytes or (audio_input if isinstance(audio_input, bytes) else None)
        if raw_bytes is None and audio_path and os.path.exists(audio_path):
            with open(audio_path, "rb") as f:
                raw_bytes = f.read()
            filename = os.path.basename(audio_path)
        elif raw_bytes is None and isinstance(audio_input, str) and os.path.exists(audio_input):
            with open(audio_input, "rb") as f:
                raw_bytes = f.read()
            filename = os.path.basename(audio_input)

        if not raw_bytes:
            raise RuntimeError("STT_FAILED: No audio bytes provided")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {"file": (filename, raw_bytes, "audio/wav")}
        data = {"model": "whisper-1"}
        if language:
            data["language"] = language

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, files=files, data=data)
            if resp.status_code != 200:
                raise RuntimeError(f"STT_FAILED: OpenAI STT error ({resp.status_code}): {resp.text}")
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
        audio_input: Optional[Union[bytes, str]] = None,
        filename: str = "audio.wav",
        language: Optional[str] = "en",
        audio_bytes: Optional[bytes] = None,
        audio_path: Optional[str] = None,
    ) -> Tuple[str, int]:
        start = time.time()
        await asyncio.sleep(0.08)
        transcript = self._sample_transcripts[self._counter % len(self._sample_transcripts)]
        self._counter += 1
        latency_ms = int((time.time() - start) * 1000)
        return transcript, latency_ms


def get_stt_service() -> STTService:
    settings = get_settings()
    provider = (settings.STT_PROVIDER or "mock").lower()

    if not settings.MOCK_AI:
        if provider == "mock":
            raise RuntimeError(
                "STT_CONFIGURATION_ERROR: MOCK_AI is false but STT_PROVIDER is set to 'mock'. A real provider must be configured."
            )
        if provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise RuntimeError(
                    "STT_CONFIGURATION_ERROR: GEMINI_API_KEY is required when STT_PROVIDER='gemini' and MOCK_AI is false."
                )
            return GeminiSTTService(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_STT_MODEL)
        elif provider == "openai":
            if not settings.STT_API_KEY:
                raise RuntimeError(
                    "STT_CONFIGURATION_ERROR: STT_API_KEY is required when STT_PROVIDER='openai' and MOCK_AI is false."
                )
            return OpenAISTTService(api_key=settings.STT_API_KEY)
        else:
            raise RuntimeError(
                f"STT_CONFIGURATION_ERROR: Unsupported STT provider '{provider}' when MOCK_AI is false."
            )

    # When MOCK_AI is true:
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiSTTService(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_STT_MODEL)
    elif provider == "openai" and settings.STT_API_KEY:
        return OpenAISTTService(api_key=settings.STT_API_KEY)
    elif provider == "mock":
        return MockSTTService()

    return MockSTTService()


def _lazy_stt_service() -> STTService:
    try:
        return get_stt_service()
    except Exception:
        return MockSTTService()


stt_service = _lazy_stt_service()
