import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Settings
from app.services.stt_service import (
    STTService,
    GeminiSTTService,
    OpenAISTTService,
    MockSTTService,
    get_stt_service,
)
from app.services.llm_service import (
    LLMService,
    GeminiLLMService,
    OpenAILLMService,
    MockLLMService,
    get_llm_service,
)


# 1. Missing API Key unit tests
def test_gemini_stt_missing_api_key():
    with pytest.raises(RuntimeError, match="STT_CONFIGURATION_ERROR"):
        GeminiSTTService(api_key="")


def test_gemini_llm_missing_api_key():
    with pytest.raises(RuntimeError, match="LLM_CONFIGURATION_ERROR"):
        GeminiLLMService(api_key="")


# 2. Provider selection tests
def test_provider_selection_mock_mode():
    test_settings = Settings(
        MOCK_AI=True,
        STT_PROVIDER="mock",
        LLM_PROVIDER="mock",
    )
    with patch("app.services.stt_service.get_settings", return_value=test_settings), \
         patch("app.services.llm_service.get_settings", return_value=test_settings):
        stt = get_stt_service()
        llm = get_llm_service()
        assert isinstance(stt, MockSTTService)
        assert isinstance(llm, MockLLMService)


def test_provider_selection_real_gemini_missing_key_fails():
    test_settings = Settings(
        MOCK_AI=False,
        STT_PROVIDER="gemini",
        LLM_PROVIDER="gemini",
        GEMINI_API_KEY="",
    )
    with patch("app.services.stt_service.get_settings", return_value=test_settings):
        with pytest.raises(RuntimeError, match="STT_CONFIGURATION_ERROR"):
            get_stt_service()

    with patch("app.services.llm_service.get_settings", return_value=test_settings):
        with pytest.raises(RuntimeError, match="LLM_CONFIGURATION_ERROR"):
            get_llm_service()


def test_provider_selection_real_gemini_prohibits_mock_provider():
    test_settings = Settings(
        MOCK_AI=False,
        STT_PROVIDER="mock",
        LLM_PROVIDER="mock",
    )
    with patch("app.services.stt_service.get_settings", return_value=test_settings):
        with pytest.raises(RuntimeError, match="STT_CONFIGURATION_ERROR"):
            get_stt_service()

    with patch("app.services.llm_service.get_settings", return_value=test_settings):
        with pytest.raises(RuntimeError, match="LLM_CONFIGURATION_ERROR"):
            get_llm_service()


def test_provider_selection_real_gemini_with_key():
    test_settings = Settings(
        MOCK_AI=False,
        STT_PROVIDER="gemini",
        LLM_PROVIDER="gemini",
        GEMINI_API_KEY="test_valid_key_12345",
        GEMINI_STT_MODEL="gemini-3.5-transcribe",
        GEMINI_LLM_MODEL="gemini-3.8-flash",
    )
    with patch("app.services.stt_service.get_settings", return_value=test_settings), \
         patch("app.services.llm_service.get_settings", return_value=test_settings), \
         patch("app.services.stt_service.genai.Client"), \
         patch("app.services.llm_service.genai.Client"):
        stt = get_stt_service()
        llm = get_llm_service()
        assert isinstance(stt, GeminiSTTService)
        assert isinstance(llm, GeminiLLMService)
        assert stt.model == "gemini-3.5-transcribe"
        assert llm.model == "gemini-3.8-flash"


# 3. GeminiSTTService unit tests
@pytest.mark.asyncio
async def test_gemini_stt_successful_transcript():
    with patch("app.services.stt_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Hey, what are you doing?"
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        stt_service = GeminiSTTService(api_key="test_key", model="gemini-3.5-transcribe")
        fake_wav = b"RIFF" + b"\x00" * 100

        transcript, latency_ms = await stt_service.transcribe(
            audio_bytes=fake_wav,
            filename="user_speech.wav",
            language="en",
        )

        assert transcript == "Hey, what are you doing?"
        assert latency_ms >= 0
        mock_client.aio.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_gemini_stt_provider_failure():
    with patch("app.services.stt_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("API connection timeout"))
        mock_client_cls.return_value = mock_client

        stt_service = GeminiSTTService(api_key="test_key", model="gemini-3.5-transcribe")
        fake_wav = b"RIFF" + b"\x00" * 100

        with pytest.raises(RuntimeError, match="STT_FAILED"):
            await stt_service.transcribe(
                audio_bytes=fake_wav,
                filename="user_speech.wav",
            )


# 4. GeminiLLMService unit tests
@pytest.mark.asyncio
async def test_gemini_llm_successful_response():
    with patch("app.services.llm_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "I'm just taking a walk and listening to the city. What about you?"
        mock_response.candidates = []
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        llm_service = GeminiLLMService(api_key="test_key", model="gemini-3.8-flash")

        response_text, latency_ms = await llm_service.generate(
            prompt="You are Alex...",
            user_message="Hey, what are you doing?",
        )

        assert response_text == "I'm just taking a walk and listening to the city. What about you?"
        assert latency_ms >= 0
        mock_client.aio.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_gemini_llm_provider_failure():
    with patch("app.services.llm_service.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("Google Quota Exceeded"))
        mock_client_cls.return_value = mock_client

        llm_service = GeminiLLMService(api_key="test_key", model="gemini-3.8-flash")

        with pytest.raises(RuntimeError, match="LLM_FAILED"):
            await llm_service.generate(
                prompt="You are Alex...",
                user_message="Hey, what are you doing?",
            )
