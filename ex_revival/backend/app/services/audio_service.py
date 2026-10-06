import io
import math
from typing import Tuple, Dict, Any
import numpy as np
import soundfile as sf


class AudioValidationError(Exception):
    pass


class AudioService:
    MIN_DURATION_SECONDS = 1.0
    MAX_DURATION_SECONDS = 120.0
    MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
    TARGET_SAMPLE_RATE = 24000  # Optimal for Chatterbox / HiFi TTS

    @classmethod
    def validate_and_normalize(cls, audio_bytes: bytes, filename: str = "voice.wav") -> Tuple[bytes, Dict[str, Any]]:
        """
        Validates file size, formats, duration, silence, clipping,
        and normalizes audio to mono, 24kHz, peak-normalized PCM WAV.
        """
        if len(audio_bytes) > cls.MAX_FILE_SIZE_BYTES:
            raise AudioValidationError(f"Audio file exceeds maximum size of {cls.MAX_FILE_SIZE_BYTES // (1024*1024)} MB")

        if len(audio_bytes) < 100:
            raise AudioValidationError("Audio file is empty or corrupted")

        try:
            bio = io.BytesIO(audio_bytes)
            data, sample_rate = sf.read(bio, dtype="float32")
        except Exception as e:
            raise AudioValidationError(f"Invalid audio format or unreadable stream: {str(e)}")

        # Calculate channels and shape
        if data.ndim == 1:
            channels = 1
            samples = data
        else:
            channels = data.shape[1]
            # Convert multi-channel to mono by averaging channels
            samples = np.mean(data, axis=1)

        total_samples = len(samples)
        duration_seconds = total_samples / float(sample_rate)

        if duration_seconds < cls.MIN_DURATION_SECONDS:
            raise AudioValidationError(
                f"Audio is too short ({duration_seconds:.1f}s). Minimum required duration is {cls.MIN_DURATION_SECONDS}s."
            )

        if duration_seconds > cls.MAX_DURATION_SECONDS:
            raise AudioValidationError(
                f"Audio is too long ({duration_seconds:.1f}s). Maximum allowed duration is {cls.MAX_DURATION_SECONDS}s."
            )

        # Detect clipping: proportion of samples that exceed 0.999 amplitude
        clipping_threshold = 0.999
        clipped_samples = np.sum(np.abs(samples) >= clipping_threshold)
        clipping_ratio = clipped_samples / float(total_samples)
        has_clipping = bool(clipping_ratio > 0.05)  # More than 5% clipped

        # Detect silence: RMS amplitude below -45dB
        rms = np.sqrt(np.mean(samples ** 2)) if total_samples > 0 else 0.0
        db_level = 20 * math.log10(rms + 1e-9)
        has_silence = bool(db_level < -42.0)

        if has_silence:
            raise AudioValidationError(
                "Audio sample is too quiet or mostly silence. Please record closer to the microphone."
            )

        # Normalize amplitude (peak normalization to -1.0dB = ~0.89 max amplitude)
        peak = np.max(np.abs(samples))
        if peak > 0:
            target_peak = 0.891
            normalized_samples = samples * (target_peak / peak)
        else:
            normalized_samples = samples

        # Resample to TARGET_SAMPLE_RATE if different
        target_rate = cls.TARGET_SAMPLE_RATE
        if sample_rate != target_rate:
            # Resample using linear interpolation or scipy resample
            new_num_samples = int(len(normalized_samples) * (target_rate / sample_rate))
            x_old = np.linspace(0, 1, len(normalized_samples))
            x_new = np.linspace(0, 1, new_num_samples)
            normalized_samples = np.interp(x_new, x_old, normalized_samples).astype(np.float32)

        # Write normalized audio to bytes
        out_bio = io.BytesIO()
        sf.write(out_bio, normalized_samples, target_rate, format="WAV", subtype="PCM_16")
        normalized_bytes = out_bio.getvalue()

        metadata = {
            "duration_seconds": round(duration_seconds, 2),
            "sample_rate": target_rate,
            "original_sample_rate": sample_rate,
            "channels": 1,
            "has_silence": has_silence,
            "has_clipping": has_clipping,
            "rms_db": round(db_level, 2),
        }

        return normalized_bytes, metadata


audio_service = AudioService()
