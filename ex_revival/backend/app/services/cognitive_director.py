import json
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("ex_revival.director")


class CognitiveDirector:
    """
    Real-Time Emotional State Machine & Acoustic Prosody Director.
    Solves the 'Emotional Trapping' problem:
    Decouples transient conversation affect from the reference audio's baseline mood.
    Directs the LLM scriptwriter and Chatterbox acoustic synthesizer dynamically on every turn.
    """

    def analyze_turn_affect(
        self,
        transcript: str,
        recent_history: List[Dict[str, str]],
        personality_dna_raw: Optional[str] = None,
        language: str = "en",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Analyzes conversational context and returns:
        (acting_prompt_injection, acoustic_controls)
        """
        dna = {}
        if personality_dna_raw:
            try:
                dna = json.loads(personality_dna_raw)
            except Exception:
                pass

        ref_bias = dna.get("reference_affect_bias", {})
        ref_arousal = float(ref_bias.get("detected_arousal", 0.55))
        is_ref_hyped = ref_arousal > 0.65

        # Detect Conversational Affect Category
        text = (transcript or "").lower().strip()
        category = self._classify_turn_category(text, recent_history)

        # Compute Acoustic Neural Controls
        acoustic_controls = self._compute_acoustic_controls(category, is_ref_hyped)

        # Build Acting Instructions for the LLM
        acting_instructions = self._build_acting_instructions(category, dna, language)

        logger.info(
            f"[Cognitive Director] Turn category: '{category}' | "
            f"Acoustic steering: exaggeration={acoustic_controls['exaggeration']}, "
            f"cfg={acoustic_controls['cfg_weight']}, pitch_shift={acoustic_controls['pitch_shift_semitones']}st, "
            f"tempo={acoustic_controls['tempo_scale']}x"
        )

        return acting_instructions, acoustic_controls

    def _classify_turn_category(self, text: str, recent_history: List[Dict[str, str]]) -> str:
        """Classifies the emotional temperature and intent of the turn."""
        # 1. Sadness / Grief / Vulnerability / Hurt / Exhaustion
        sad_indicators = [
            "अकेला", "अकेली", "अकेलापन", "उदास", "दुखी", "रोना", "रो ", "रोता", "रोती",
            "बुरा", "दर्द", "परेशान", "टूट", "थक", "तकलीफ", "छोड़", "खराब", "याद आ रही",
            "sad", "crying", "cry", "broke up", "breakup", "broken", "hurt",
            "lonely", "alone", "miss you", "miss her", "miss him", "depressed",
            "anxious", "pain", "tired of everything", "worst day", "bad day",
            "exhausted", "hopeless", "ro raha", "ro rahi", "dukhi", "udas",
            "chhod diya", "chhod ke", "khatam ho gaya", "dard", "pareshan",
            "mood kharab", "akela", "akeli", "roona", "rona",
        ]
        if any(w in text for w in sad_indicators):
            return "sadness_comfort"

        # 2. Tender Intimacy / Affection
        tender_indicators = [
            "प्यार", "याद", "पास", "सुकून", "ख्याल", "गले", "मोहब्बत", "साथ",
            "love you", "pyar", "pyaar", "miss you", "hug", "kiss", "cute",
            "sweet", "close to you", "remember when we", "yaad aati hai",
            "apna khayal", "care for you", "pass aao", "sukoon",
        ]
        if any(w in text for w in tender_indicators):
            return "tender_intimacy"

        # 3. Celebration / Hyped / Achievement / Joy
        hyped_indicators = [
            "जीत", "सिलेक्शन", "पार्टी", "खुश", "खुशी", "मज़ा", "कमाल", "बधाई", "पास हो गया", "मस्त",
            "won", "crushed it", "passed", "got selected", "hired", "promoted",
            "congrats", "celebrate", "party", "excited", "happy", "great news",
            "best day", "mazza aa gaya", "kamaal", "jeet gaya", "jeet gayi",
            "selection ho gaya", "khushi", "party de", "mithai",
        ]
        if any(w in text for w in hyped_indicators):
            return "celebration_hyped"

        # 4. Playful Banter / Teasing / Sarcasm
        playful_indicators = [
            "पागल", "झूठ", "मज़ाक", "नौटंकी", "चुप", "अरे यार",
            "haha", "lol", "lmao", "kya yaar", "pagal", "chup", "jhooth",
            "kidding", "joke", "funny", "sach bol", "bata na", "nautanki",
        ]
        if any(w in text for w in playful_indicators):
            return "playful_banter"

        # Default: Warm, Grounded Natural Conversation
        return "calm_grounding"

    def _compute_acoustic_controls(self, category: str, is_ref_hyped: bool) -> Dict[str, Any]:
        """
        Derives neural synthesis parameters:
        Disentangles acoustic invariants from the reference clip's temporary mood.
        """
        if category == "sadness_comfort":
            # Low exaggeration suppresses wild pitch spikes into a quiet, heavy chest resonance
            # If reference clip was excited, drop cfg_weight to 0.48 to detach from the excited energy!
            return {
                "emotion": "sad",
                "exaggeration": 0.38,
                "cfg_weight": 0.48 if is_ref_hyped else 0.54,
                "temperature": 0.65,
                "pitch_shift_semitones": -2.2,
                "tempo_scale": 0.82,
            }
        elif category == "tender_intimacy":
            return {
                "emotion": "warm_tender",
                "exaggeration": 0.48,
                "cfg_weight": 0.55,
                "temperature": 0.70,
                "pitch_shift_semitones": -1.0,
                "tempo_scale": 0.90,
            }
        elif category == "celebration_hyped":
            return {
                "emotion": "excited",
                "exaggeration": 0.85,
                "cfg_weight": 0.74,
                "temperature": 0.80,
                "pitch_shift_semitones": +1.5,
                "tempo_scale": 1.12,
            }
        elif category == "playful_banter":
            return {
                "emotion": "playful",
                "exaggeration": 0.72,
                "cfg_weight": 0.68,
                "temperature": 0.78,
                "pitch_shift_semitones": +0.5,
                "tempo_scale": 1.02,
            }
        else:  # calm_grounding
            return {
                "emotion": "caring",
                "exaggeration": 0.65,
                "cfg_weight": 0.65,
                "temperature": 0.75,
                "pitch_shift_semitones": 0.0,
                "tempo_scale": 1.0,
            }

    def _build_acting_instructions(self, category: str, dna: Dict[str, Any], language: str) -> str:
        """Constructs explicit prompt guidance for the LLM voice actor."""
        idiolect = dna.get("idiolect", {})
        favored_markers = idiolect.get("favored_discourse_markers", [])
        markers_str = ", ".join([f'"{m}"' for m in favored_markers[:4]]) if favored_markers else ""

        is_hindi = (language or "").lower().startswith("hi")

        if category == "sadness_comfort":
            if is_hindi:
                return (
                    "ACTING DIRECTION — CURRENT EMOTIONAL PHASE: DEEP EMPATHY & SADNESS / CONSOLING.\n"
                    "- The user is feeling down, vulnerable, or hurt. DO NOT SOUND CHEERFUL, ENERGETIC, OR CANNED.\n"
                    "- Speak in a quiet, soft, vulnerable tone with real pauses.\n"
                    "- Use ellipsis '...' strategically to create genuine breathing hesitations (e.g. 'सुनो ना... मुझे समझ नहीं आ रहा क्या बोलूँ... पर मैं तुम्हारे साथ हूँ।').\n"
                    "- AVOID exclamation marks (!) or hype slang like 'arre yaar mast'. Use soft caring markers like 'सुनो ना...', 'बस...'.\n"
                    "- Keep it short, genuine, and grounded: 1 to 2 comforting spoken sentences in authentic Devanagari script."
                )
            else:
                return (
                    "ACTING DIRECTION — CURRENT EMOTIONAL PHASE: DEEP EMPATHY & SADNESS / CONSOLING.\n"
                    "- The user is feeling down, hurt, or vulnerable. DO NOT SOUND CHEERFUL OR CANNED.\n"
                    "- Speak in a quiet, soft, gentle tone with genuine breath pauses.\n"
                    "- Use ellipsis '...' to indicate emotional hesitations and deep breathing pauses (e.g. 'Listen... I don't even know what to say... but I am right here with you.').\n"
                    "- AVOID exclamation marks (!) or high-energy cheerfulness.\n"
                    "- Keep it short and deeply comforting: 1 to 2 spoken sentences."
                )

        elif category == "tender_intimacy":
            if is_hindi:
                return (
                    "ACTING DIRECTION — CURRENT EMOTIONAL PHASE: TENDER INTIMACY & WARMTH.\n"
                    "- Speak softly, like a late-night close call.\n"
                    "- Use soft commas and micro-pauses '...' to make the delivery intimate and unhurried.\n"
                    "- Write in authentic conversational Devanagari script with personal warmth."
                )
            else:
                return (
                    "ACTING DIRECTION — CURRENT EMOTIONAL PHASE: TENDER INTIMACY & WARMTH.\n"
                    "- Speak softly and warmly, like an intimate late-night phone call.\n"
                    "- Use commas and ellipsis '...' to create relaxed, gentle cadence."
                )

        elif category == "celebration_hyped":
            if is_hindi:
                return (
                    "ACTING DIRECTION — CURRENT EMOTIONAL PHASE: CELEBRATORY & EXCITED.\n"
                    "- Celebrate with the user! Sound proud, thrilled, and full of lively energy!\n"
                    "- Use exclamation marks (!) for punchy pitch rises (e.g. 'अरे सच में?! मुझे तो पहले से पता था तू कर दिखाएगा!').\n"
                    "- Speak with fast, energetic momentum in authentic Devanagari script."
                )
            else:
                return (
                    "ACTING DIRECTION — CURRENT EMOTIONAL PHASE: CELEBRATORY & EXCITED.\n"
                    "- Celebrate with the user! Sound genuinely proud, hyped, and energized!\n"
                    "- Use exclamation marks (!) for lively energy and pitch peaks.\n"
                    "- Keep momentum punchy and enthusiastic."
                )

        elif category == "playful_banter":
            if is_hindi:
                return (
                    "ACTING DIRECTION — CURRENT EMOTIONAL PHASE: PLAYFUL BANTER & TEASING.\n"
                    "- Have fun, tease them lightheartedly, and banter like real best friends.\n"
                    f"- You can naturally weave in conversational fillers like {markers_str or 'अरे यार, सुनो'}.\n"
                    "- Keep it quick, witty, and candid in authentic Devanagari script."
                )
            else:
                return (
                    "ACTING DIRECTION — CURRENT EMOTIONAL PHASE: PLAYFUL BANTER & TEASING.\n"
                    "- Banter playfully like real close friends. Tease them with affection and humor.\n"
                    "- Keep it witty, quick, and natural."
                )

        else:  # calm_grounding
            if is_hindi:
                return (
                    "ACTING DIRECTION — CURRENT EMOTIONAL PHASE: WARM CONVERSATIONAL FLOW.\n"
                    "- Speak naturally with relaxed warmth and authentic rhythm.\n"
                    f"- Naturally use conversational markers like {markers_str or 'हाँ, सुनो'}.\n"
                    "- 1 to 2 spoken sentences in authentic Devanagari script."
                )
            else:
                return (
                    "ACTING DIRECTION — CURRENT EMOTIONAL PHASE: WARM CONVERSATIONAL FLOW.\n"
                    "- Speak naturally with relaxed warmth and authentic presence.\n"
                    "- 1 to 2 spoken sentences."
                )


cognitive_director = CognitiveDirector()
