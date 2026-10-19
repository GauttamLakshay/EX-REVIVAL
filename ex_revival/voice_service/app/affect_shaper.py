import logging
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np
import soundfile as sf
import librosa
from scipy import signal

logger = logging.getLogger("voice_service.affect_shaper")


class AffectShaper:
    """
    Affect Decoupling & Neural Prosody Retargeting Engine.
    Enables cross-emotional voice synthesis:
    e.g., transforming a voice conditioning sample recorded in excitement
    into a quiet, vulnerable, melancholic, or gentle voice without losing
    the speaker's physiological throat identity and native accent.
    """

    @staticmethod
    def analyze_acoustic_affect(audio_path: str) -> Dict[str, Any]:
        """
        Analyzes reference audio to extract:
        - Fundamental frequency (F0) baseline and variance
        - Speech energy (RMS)
        - Syllable rate / estimated tempo
        - Measured reference affect bias (arousal, valence, excitement level)
        """
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Reference audio not found: {audio_path}")

        y, sr = librosa.load(str(path), sr=24000, mono=True)
        duration_sec = len(y) / sr

        # 1. Pitch Tracking via Autocorrelation / YIN
        f0 = librosa.yin(y, fmin=65, fmax=450, sr=sr)
        # Filter unvoiced frames (yin returns fmin or unvoiced frames with flat values)
        valid_f0 = f0[(f0 > 75) & (f0 < 420)]

        if len(valid_f0) > 0:
            mean_f0 = float(np.median(valid_f0))
            std_f0 = float(np.std(valid_f0))
            min_f0 = float(np.percentile(valid_f0, 5))
            max_f0 = float(np.percentile(valid_f0, 95))
        else:
            mean_f0 = 160.0
            std_f0 = 25.0
            min_f0 = 120.0
            max_f0 = 210.0

        # 2. Energy (RMS)
        rms = librosa.feature.rms(y=y)[0]
        mean_rms = float(np.mean(rms))
        peak_rms = float(np.max(rms)) if len(rms) > 0 else 0.1

        # 3. Speech Activity & Tempo Estimation
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)
        estimated_wpm = int(tempo[0]) if len(tempo) > 0 else 130
        estimated_wpm = max(70, min(240, estimated_wpm))

        # 4. Affect Bias Derivation
        # Higher F0 standard deviation + elevated pitch + high RMS = High Arousal (Excitement)
        # Low F0 std + low RMS = Low Arousal (Calm / Subdued / Sad)
        pitch_variability_ratio = std_f0 / (mean_f0 + 1e-6)
        
        # Arousal score from 0.0 (deeply somber) to 1.0 (hyper-excited)
        arousal_score = np.clip(
            (pitch_variability_ratio - 0.12) / 0.25 * 0.5 + (mean_rms / 0.15) * 0.5,
            0.10,
            0.98,
        )

        inferred_emotion = "neutral"
        if arousal_score > 0.70:
            inferred_emotion = "excited"
        elif arousal_score < 0.35:
            inferred_emotion = "calm"

        return {
            "status": "success",
            "duration_seconds": round(duration_sec, 2),
            "sample_rate": sr,
            "base_pitch_hz": round(mean_f0, 1),
            "pitch_std_hz": round(std_f0, 1),
            "pitch_range_hz": [round(min_f0, 1), round(max_f0, 1)],
            "mean_energy_rms": round(mean_rms, 4),
            "estimated_wpm": estimated_wpm,
            "detected_arousal": round(float(arousal_score), 2),
            "inferred_baseline_emotion": inferred_emotion,
            # Normalization offsets to arrive at resting neutral
            "resting_pitch_hz": round(mean_f0 - (arousal_score - 0.5) * 35.0, 1),
            "resting_wpm": int(estimated_wpm / (1.0 + (arousal_score - 0.5) * 0.4)),
        }

    @staticmethod
    def retarget_waveform(
        wav_data: np.ndarray,
        sample_rate: int,
        pitch_shift_semitones: float = 0.0,
        tempo_scale: float = 1.0,
        emotion: str = "neutral",
    ) -> np.ndarray:
        """
        Applies DSP retargeting:
        - Glottal pitch shifting (lowers F0 for sorrow/intimacy, raises for cheer)
        - Cadence stretching (slower deliberate pacing for sad turns)
        - Spectral damping / presence shaping (softer breath leakage for sad/intimate turns)
        - Peak normalization (-1.0 dB = 0.90) for full mobile speaker presence
        """
        out = wav_data.copy()

        # 1. Pitch Shifting if requested
        if abs(pitch_shift_semitones) > 0.1:
            try:
                # Limit pitch shift to safe acoustic boundaries [-4.0, +3.5]
                clamped_shift = max(-4.0, min(3.5, pitch_shift_semitones))
                out = librosa.effects.pitch_shift(
                    y=out,
                    sr=sample_rate,
                    n_steps=clamped_shift,
                )
            except Exception as e:
                logger.warning(f"[AffectShaper] Pitch shift failed: {e}")

        # 2. Tempo Scaling if requested (0.75x to 1.25x)
        if abs(tempo_scale - 1.0) > 0.04:
            try:
                clamped_rate = max(0.75, min(1.25, tempo_scale))
                out = librosa.effects.time_stretch(y=out, rate=clamped_rate)
            except Exception as e:
                logger.warning(f"[AffectShaper] Time stretch failed: {e}")

        # 3. Spectral Affect Shaping (Glottal Damping vs Presence)
        emo = (emotion or "").lower()
        if any(w in emo for w in ["sad", "melancholy", "grief", "whisper", "tender", "consoling"]):
            try:
                # Apply gentle 2nd order Butterworth low-pass filter at 5800 Hz
                # Simulates reduced vocal cord tension and intimate proximity breathiness
                nyquist = sample_rate / 2.0
                cutoff = min(5800.0, nyquist - 200.0)
                b, a = signal.butter(2, cutoff / nyquist, btype="low")
                out = signal.lfilter(b, a, out)
            except Exception as filter_err:
                logger.warning(f"[AffectShaper] Low-pass filter failed: {filter_err}")

        elif any(w in emo for w in ["excited", "celebratory", "hyped", "energetic"]):
            try:
                # Gentle presence shelf (boost 2.5kHz - 5kHz slightly for clarity)
                nyquist = sample_rate / 2.0
                b, a = signal.butter(2, 2800.0 / nyquist, btype="high")
                highs = signal.lfilter(b, a, out)
                out = out + 0.12 * highs  # subtle +1 dB air/presence
            except Exception as filter_err:
                logger.warning(f"[AffectShaper] High-shelf boost failed: {filter_err}")

        # 4. Final Peak Normalization to -1.0 dB (0.90)
        max_val = np.max(np.abs(out)) + 1e-6
        if max_val > 0.001:
            out = (out / max_val) * 0.90

        return out.astype(np.float32)


affect_shaper = AffectShaper()
