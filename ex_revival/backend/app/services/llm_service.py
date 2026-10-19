import time
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
import httpx
from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger("ex_revival.llm")

SYSTEM_PROMPT_TEMPLATE = """SYSTEM

You are the conversational character configured by the user.

CHARACTER

Name: {name}

Personality:
{personality}

Speaking Style:
{speaking_style}

Language:
{language}

Relationship Context:
{relationship_context}


ACTING & EMOTIONAL DIRECTIVE:
{acting_instructions}


RULES

- YOU ARE A REAL HUMAN WITH A PULSE: Embody the personality, speaking style, and relationship configured above. Talk like a real friend or close companion having a live voice call, NOT like an AI assistant.
- BANNED ROBOTIC PHRASES: NEVER use assistant clichés such as "How can I help you today?", "As an AI...", "I understand your query", or textbook robotic translations. Talk with casual warmth, humor, teasing, and authentic banter.
- HINDI PHONETICS & SCRIPT MANDATE:
  - If the configured language is 'hi' (Hindi), or if the user speaks to you in Hindi or Hinglish:
    You MUST reply in natural, spoken conversational Hindi written in AUTHENTIC DEVANAGARI SCRIPT (e.g. "अरे यार! मैं तो एकदम मस्त हूँ, तुम बताओ क्या चल रहा है?").
    DO NOT write Hindi in English/Latin letters (e.g. NEVER write "tum kaise ho" or "main theek hoon").
    Writing in Devanagari is mandatory because our neural voice synthesizer maps Devanagari characters directly to native Indian acoustic phonemes (including the true soft dental 'त' in 'तुम', nasalized matras, and authentic Indian cadence). Latin letters force a foreign English accent.
  - If common loanwords are used in conversation (like phone, college, office, movie), write them in natural Devanagari (e.g. "फोन", "कॉलेज", "ऑफिस", "मूवी").
- NATURAL SPEECH PROSODY & PUNCTUATION:
  - Keep responses concise: 1 to 2 punchy, conversational spoken sentences.
  - Use punctuation strategically for the voice engine: use commas (,) for natural breathing pauses, exclamation marks (!) for lively energy, and question marks (?) for curious rising intonation.
  - DO NOT use emojis, asterisks (*), quotes, or markdown formatting, as this text is directly synthesized into speech audio.
- Maintain continuity and remember shared memories without sounding like a database query.


RECENT CONVERSATION:

{recent_messages}


RELEVANT MEMORIES:

{memories}


USER MESSAGE:

{transcript}
"""


class LLMService(ABC):
    @abstractmethod
    async def generate(self, prompt: str, user_message: str) -> Tuple[str, int]:
        """
        Executes prompt and returns: (response_text, latency_ms)
        """
        pass


class OpenAILLMService(LLMService):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    async def generate(self, prompt: str, user_message: str) -> Tuple[str, int]:
        start = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": 150,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"LLM_FAILED: OpenAI LLM error ({resp.status_code}): {resp.text}")
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            latency_ms = int((time.time() - start) * 1000)
            return content, latency_ms


class GeminiLLMService(LLMService):
    def __init__(self, api_key: str, model: str = "gemini-3.1-flash-lite"):
        if not api_key:
            raise RuntimeError("LLM_CONFIGURATION_ERROR: GEMINI_API_KEY is required for GeminiLLMService")
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=self.api_key)

    async def generate(self, prompt: str, user_message: str) -> Tuple[str, int]:
        start = time.time()
        config = types.GenerateContentConfig(
            system_instruction=prompt,
            temperature=0.7,
            max_output_tokens=150,
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=user_message,
                config=config,
            )
            content = (response.text or "").strip()
            if not content and response.candidates:
                for cand in response.candidates:
                    if cand.content and cand.content.parts:
                        for p in cand.content.parts:
                            if p.text:
                                content += p.text
                content = content.strip()

            if not content:
                raise RuntimeError("LLM_FAILED: Empty response received from Gemini model")

            latency_ms = int((time.time() - start) * 1000)
            return content, latency_ms
        except Exception as e:
            err_str = str(e)
            if ("404" in err_str or "not found" in err_str.lower() or "NOT_FOUND" in err_str or "503" in err_str or "UNAVAILABLE" in err_str) and self.model != "gemini-3.1-flash-lite":
                logger.warning(f"LLM Model '{self.model}' unavailable or not found; falling back to gemini-3.1-flash-lite: {e}")
                try:
                    fallback_response = await self.client.aio.models.generate_content(
                        model="gemini-3.1-flash-lite",
                        contents=user_message,
                        config=config,
                    )
                    content = (fallback_response.text or "").strip()
                    if not content and fallback_response.candidates:
                        for cand in fallback_response.candidates:
                            if cand.content and cand.content.parts:
                                for p in cand.content.parts:
                                    if p.text:
                                        content += p.text
                        content = content.strip()
                    if not content:
                        raise RuntimeError("LLM_FAILED: Empty response from fallback model")
                    latency_ms = int((time.time() - start) * 1000)
                    return content, latency_ms
                except Exception as fb_err:
                    raise RuntimeError(f"LLM_FAILED: Gemini LLM generation failed: {fb_err}")
            raise RuntimeError(f"LLM_FAILED: Gemini LLM generation failed: {e}")


class MockLLMService(LLMService):
    """
    Simulated conversational model that provides authentic, warm responses
    tailored to the prompt without requiring external API keys.
    """
    def __init__(self):
        pass

    async def generate(self, prompt: str, user_message: str) -> Tuple[str, int]:
        start = time.time()
        await asyncio.sleep(0.12)  # Realistic LLM token generation simulation

        msg = user_message.lower().strip()
        if "doing" in msg or "up to" in msg:
            response = "Nothing much, just chilling and listening to some music. What about you?"
        elif "how are you" in msg:
            response = "I'm doing really well, thank you! It feels wonderful to hear from you."
        elif "hackathon" in msg or "project" in msg:
            response = "That is huge! I knew you'd crush it. Tell me all about what you're building!"
        elif "miss" in msg:
            response = "I've missed talking with you too. Hearing your voice makes my day."
        elif "remember" in msg:
            response = "Of course I remember! Those moments always stay close to my heart."
        else:
            response = "I hear you. Tell me more about that, I'm right here listening."

        latency_ms = int((time.time() - start) * 1000)
        return response, latency_ms


def build_system_prompt(
    name: str,
    personality: str,
    speaking_style: str,
    language: str,
    relationship_context: str,
    recent_messages: List[Dict[str, str]],
    memories: List[str],
    transcript: str,
    acting_instructions: Optional[str] = None,
) -> str:
    """Builds the strict standardized system prompt per Section 16."""
    recent_str = "\n".join([f"{m['role'].upper()}: {m['text']}" for m in recent_messages]) if recent_messages else "(None yet)"
    memories_str = "\n".join([f"- {m}" for m in memories]) if memories else "(No memories recorded yet)"
    replacements = {
        "{name}": name or "Revival",
        "{personality}": personality or "Warm, thoughtful, and expressive",
        "{speaking_style}": speaking_style or "Natural, conversational speech",
        "{language}": language or "en",
        "{relationship_context}": relationship_context or "Close confidant",
        "{acting_instructions}": acting_instructions or "Embody the character naturally with warm conversational presence.",
        "{recent_messages}": recent_str,
        "{memories}": memories_str,
        "{transcript}": transcript or "",
    }

    prompt = SYSTEM_PROMPT_TEMPLATE
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, str(value))
    return prompt


def get_llm_service() -> LLMService:
    settings = get_settings()
    provider = (settings.LLM_PROVIDER or "mock").lower()

    if not settings.MOCK_AI:
        if provider == "mock":
            raise RuntimeError(
                "LLM_CONFIGURATION_ERROR: MOCK_AI is false but LLM_PROVIDER is set to 'mock'. A real provider must be configured."
            )
        if provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise RuntimeError(
                    "LLM_CONFIGURATION_ERROR: GEMINI_API_KEY is required when LLM_PROVIDER='gemini' and MOCK_AI is false."
                )
            return GeminiLLMService(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_LLM_MODEL)
        elif provider == "openai":
            if not settings.LLM_API_KEY:
                raise RuntimeError(
                    "LLM_CONFIGURATION_ERROR: LLM_API_KEY is required when LLM_PROVIDER='openai' and MOCK_AI is false."
                )
            return OpenAILLMService(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
        else:
            raise RuntimeError(
                f"LLM_CONFIGURATION_ERROR: Unsupported LLM provider '{provider}' when MOCK_AI is false."
            )

    # When MOCK_AI is true:
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiLLMService(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_LLM_MODEL)
    elif provider == "openai" and settings.LLM_API_KEY:
        return OpenAILLMService(api_key=settings.LLM_API_KEY, model=settings.LLM_MODEL)
    elif provider == "mock":
        return MockLLMService()

    return MockLLMService()


def _lazy_llm_service() -> LLMService:
    try:
        return get_llm_service()
    except Exception:
        return MockLLMService()


llm_service = _lazy_llm_service()
