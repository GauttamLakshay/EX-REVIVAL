import json
import logging
from typing import Dict, Any, Optional
import httpx
from google import genai
from google.genai import types

from app.config import get_settings

logger = logging.getLogger("ex_revival.personality")
settings = get_settings()


class PersonalityService:
    """
    Personality & Behavioral DNA Profiler.
    Extracts acoustic invariants, reference affect bias, and idiolect traits
    so the character can synthesize any emotion (excited, sad, tender, angry)
    without being trapped in the reference clip's temporary mood.
    """

    def __init__(self):
        self.voice_service_url = settings.VOICE_SERVICE_URL.rstrip("/")

    async def analyze_acoustic_baseline(self, audio_path: str) -> Dict[str, Any]:
        """Calls Voice Service to extract physical F0, tempo, and arousal metrics."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.voice_service_url}/analyze-voice",
                    json={"reference_audio": audio_path},
                )
                if resp.status_code == 200:
                    return resp.json()
                logger.warning(f"[Personality] Voice analysis returned status {resp.status_code}: {resp.text}")
        except Exception as e:
            logger.warning(f"[Personality] Failed to contact voice service for analysis: {e}")

        # Fallback baseline
        return {
            "status": "fallback",
            "base_pitch_hz": 180.0,
            "pitch_std_hz": 35.0,
            "pitch_range_hz": [110.0, 260.0],
            "mean_energy_rms": 0.08,
            "estimated_wpm": 130,
            "detected_arousal": 0.55,
            "inferred_baseline_emotion": "neutral",
            "resting_pitch_hz": 180.0,
            "resting_wpm": 130,
        }

    async def extract_personality_dna(
        self,
        audio_path: str,
        language: str = "en",
        character_name: str = "Companion",
        personality_desc: str = "",
        speaking_style_desc: str = "",
    ) -> Dict[str, Any]:
        """
        Creates a complete Personality DNA profile combining:
        1. Acoustic Invariants (resting pitch, pitch elasticity, tempo)
        2. Reference Affect Bias (detects if the reference audio was recorded in excitement)
        3. Idiolect Fingerprint (Devanagari fillers, verbal tics, pause tendencies)
        """
        # Step 1: Acoustic DSP extraction
        acoustic = await self.analyze_acoustic_baseline(audio_path)

        # Step 2: Gemini Cognitive Profiling
        gemini_api_key = settings.GEMINI_API_KEY
        gemini_profile = {}
        if gemini_api_key:
            try:
                client = genai.Client(api_key=gemini_api_key)
                prompt = f"""You are an elite phonetics and conversational psychologist.
Analyze the following persona and acoustic metrics to generate a behavioral Idiolect & Speaking DNA profile.

CHARACTER DETAILS:
- Name: {character_name}
- Configured Personality: {personality_desc}
- Configured Speaking Style: {speaking_style_desc}
- Language: {language}

MEASURED ACOUSTIC METRICS FROM REFERENCE AUDIO:
- Base Pitch (F0): {acoustic.get('base_pitch_hz')} Hz
- Pitch Dynamic Variance: {acoustic.get('pitch_std_hz')} Hz
- Pitch Range: {acoustic.get('pitch_range_hz')} Hz
- Speaking Tempo: {acoustic.get('estimated_wpm')} WPM
- Detected Arousal / Excitement in reference clip: {acoustic.get('detected_arousal')} (0.0=subdued to 1.0=hyped)
- Inferred Reference Mood: {acoustic.get('inferred_baseline_emotion')}

Return ONLY a valid JSON object with this exact schema:
{{
  "speaking_archetype": "brief description of their conversational vibe",
  "favored_discourse_markers": ["list of 3-5 authentic conversational catchphrases or fillers matching the language, e.g. for Hindi: अरे यार, सुनो ना, सच में, बिल्कुल"],
  "hesitation_style": "description of how they pause or take breaths (e.g. micro_pauses, thoughtful_drifts, rapid_bursts)",
  "sadness_expression_guide": "how they sound when sad/consoling (e.g. softens voice, drops pitch, pauses with ellipsis, trailing sentences)",
  "excitement_expression_guide": "how they sound when excited/happy (e.g. animated, punchy, exclamations, fast cadence)",
  "vocal_register": "deep_chest | warm_mid | bright_head"
}}
"""
                resp = await client.aio.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        response_mime_type="application/json",
                    ),
                )
                if resp.text:
                    gemini_profile = json.loads(resp.text)
            except Exception as e:
                logger.warning(f"[Personality] Gemini cognitive profiling failed: {e}")

        # Default fallbacks if LLM profiling was skipped or failed
        if not gemini_profile:
            is_hindi = (language or "").lower().startswith("hi")
            gemini_profile = {
                "speaking_archetype": personality_desc or "Warm and natural conversationalist",
                "favored_discourse_markers": (
                    ["अरे यार", "सुनो ना", "सच में", "हाँ बिल्कुल"]
                    if is_hindi
                    else ["you know", "honestly", "listen", "totally"]
                ),
                "hesitation_style": "micro_pauses",
                "sadness_expression_guide": "Softens voice, long pauses with ellipsis, gentle falling tone",
                "excitement_expression_guide": "Lively pitch bursts, exclamation marks, rapid affirmations",
                "vocal_register": "warm_mid",
            }

        # Combine into complete Personality DNA
        personality_dna = {
            "version": "1.0",
            "character_name": character_name,
            "language": language,
            "acoustic_invariants": {
                "resting_pitch_hz": acoustic.get("resting_pitch_hz", 180.0),
                "resting_wpm": acoustic.get("resting_wpm", 120),
                "pitch_std_hz": acoustic.get("pitch_std_hz", 35.0),
                "vocal_register": gemini_profile.get("vocal_register", "warm_mid"),
            },
            "reference_affect_bias": {
                "detected_arousal": acoustic.get("detected_arousal", 0.55),
                "inferred_emotion": acoustic.get("inferred_baseline_emotion", "neutral"),
                "base_pitch_hz": acoustic.get("base_pitch_hz", 180.0),
                "measured_wpm": acoustic.get("estimated_wpm", 120),
            },
            "idiolect": {
                "speaking_archetype": gemini_profile.get("speaking_archetype", "Natural human"),
                "favored_discourse_markers": gemini_profile.get("favored_discourse_markers", []),
                "hesitation_style": gemini_profile.get("hesitation_style", "micro_pauses"),
                "sadness_expression_guide": gemini_profile.get("sadness_expression_guide", ""),
                "excitement_expression_guide": gemini_profile.get("excitement_expression_guide", ""),
            },
        }

        return personality_dna


personality_service = PersonalityService()
