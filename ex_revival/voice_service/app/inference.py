import os
import time
import uuid
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import numpy as np
import soundfile as sf
from voice_service.app.config import settings
from voice_service.app.affect_shaper import affect_shaper

logger = logging.getLogger("chatterbox.inference")
logging.basicConfig(level=logging.INFO)


class ChatterboxSynthesizer:
    """
    Official Resemble AI Chatterbox Multilingual V3 Integration.
    Uses official `chatterbox.mtl_tts.ChatterboxMultilingualTTS`.
    Strictly distinguishes between real neural inference and development fallback.
    """

    def __init__(self):
        self.sample_rate = settings.SAMPLE_RATE
        self.checkpoint_path = settings.get_checkpoint_path()
        self.is_loaded = False
        self.model = None
        self.device = "cpu"
        self.device_type = "cpu"
        self.cuda_available = False
        self.gpu_name = None
        self.engine = "acoustic_fallback"
        self.model_version = None

        self._setup_hardware()
        self._load_official_model()

        if self.is_loaded and settings.WARMUP_ON_STARTUP:
            self.warmup()

    def _setup_hardware(self):
        """Discovers PyTorch CUDA / MPS runtime and configures target device with priority CUDA -> MPS -> CPU."""
        try:
            import torch
            has_cuda = torch.cuda.is_available()
            has_mps = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
            self.cuda_available = has_cuda

            target_device = (os.environ.get("VOICE_DEVICE") or settings.MODEL_DEVICE).lower()
            if target_device in ["cuda", "gpu"] or (target_device == "auto" and has_cuda):
                if has_cuda:
                    dev_idx = min(settings.CUDA_DEVICE_INDEX, torch.cuda.device_count() - 1)
                    self.device = f"cuda:{dev_idx}"
                    self.device_type = "cuda"
                    self.gpu_name = torch.cuda.get_device_name(dev_idx)
                    logger.info(f"[Chatterbox Hardware] CUDA Device: {self.gpu_name} ({self.device})")
                else:
                    logger.warning("[Chatterbox Hardware] CUDA requested but not available. Defaulting to CPU.")
                    self.device = "cpu"
                    self.device_type = "cpu"
            elif target_device == "mps" or (target_device == "auto" and has_mps):
                self.device = "mps"
                self.device_type = "mps"
                logger.info("[Chatterbox Hardware] Device set to Apple Silicon MPS.")
            else:
                self.device = "cpu"
                self.device_type = "cpu"
                logger.info("[Chatterbox Hardware] Device set to CPU.")
        except ImportError:
            self.cuda_available = False
            self.device = "cpu"
            self.device_type = "cpu"
            logger.info("[Chatterbox Hardware] PyTorch not installed on host. CPU mode.")

    def _load_official_model(self):
        """
        Loads the official Resemble AI Chatterbox Multilingual V3 model.
        Format:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model="v3")
        """
        try:
            import torch
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS

            logger.info(f"[Chatterbox] Loading official ChatterboxMultilingualTTS (t3_model='v3') on {self.device}...")
            t0 = time.time()
            self.model = ChatterboxMultilingualTTS.from_pretrained(
                device=self.device,
                t3_model="v3"
            )
            load_time = round(time.time() - t0, 2)
            self.is_loaded = True
            self.engine = "chatterbox_v3_neural"
            self.model_version = "v3"
            if hasattr(self.model, "sr"):
                self.sample_rate = self.model.sr

            logger.info(f"[Chatterbox] Official neural model successfully loaded in {load_time}s on {self.device}.")
            return
        except ImportError as imp_err:
            logger.warning(f"[Chatterbox] Official 'chatterbox' package or submodules not found ({imp_err}).")
        except Exception as load_err:
            logger.warning(f"[Chatterbox] Official model initialization failed: {load_err}")

        # Model is NOT loaded
        self.is_loaded = False
        self.model_version = None
        is_production = os.environ.get("APP_ENV", "").lower() == "production" or os.environ.get("MOCK_AI", "").lower() == "false"
        if not settings.USE_MOCK_FALLBACK or is_production:
            self.engine = "unavailable"
            raise RuntimeError(
                "Official Chatterbox Multilingual V3 neural model failed to load "
                "and fallback is disabled in production mode."
            )
        self.engine = "acoustic_fallback"
        logger.info("[Chatterbox] Running with acoustic synthesis engine fallback (Development Mode).")

    def warmup(self):
        """Runs a 1-turn warmup generation to pre-allocate CUDA memory and compile kernels."""
        if not self.is_loaded or self.device_type != "cuda":
            return
        try:
            import torch
            logger.info("[Chatterbox] Executing GPU warmup turn...")
            t0 = time.time()
            # Synthesize short warmup utterance
            temp_ref = settings.get_storage_path() / "temp" / "warmup_tone.wav"
            temp_ref.parent.mkdir(parents=True, exist_ok=True)
            t = np.linspace(0, 2.0, self.sample_rate, endpoint=False)
            tone = (np.sin(2 * np.pi * 200 * t) * 0.5).astype(np.float32)
            sf.write(str(temp_ref), tone, self.sample_rate)

            self.synthesize(text="Hello.", reference_audio_path=str(temp_ref))
            if temp_ref.exists():
                temp_ref.unlink()

            torch.cuda.synchronize()
            ms = int((time.time() - t0) * 1000)
            allocated = round(torch.cuda.memory_allocated(self.device) / (1024 ** 2), 1)
            logger.info(f"[Chatterbox] GPU warmup completed in {ms}ms. VRAM allocated: {allocated}MB.")
        except Exception as e:
            logger.warning(f"[Chatterbox] Warmup skipped: {e}")

    def get_health_telemetry(self) -> Dict[str, Any]:
        """
        Returns health status strictly distinguishing between real neural Chatterbox
        and development acoustic fallback.
        """
        telemetry = {
            "status": "ok",
            "device": str(self.device),
            "cuda_available": self.cuda_available,
            "gpu_name": self.gpu_name,
            "model_loaded": self.is_loaded,
            "engine": self.engine,
            "model_version": self.model_version,
            "sample_rate": self.sample_rate,
        }
        if self.cuda_available and self.device_type == "cuda":
            try:
                import torch
                dev_idx = int(self.device.split(":")[-1]) if ":" in self.device else 0
                props = torch.cuda.get_device_properties(dev_idx)
                telemetry["vram_total_mb"] = round(props.total_memory / (1024 ** 2), 1)
                telemetry["vram_allocated_mb"] = round(torch.cuda.memory_allocated(dev_idx) / (1024 ** 2), 1)
                telemetry["vram_reserved_mb"] = round(torch.cuda.memory_reserved(dev_idx) / (1024 ** 2), 1)
            except Exception:
                pass
        return telemetry

    def synthesize(
        self,
        text: str,
        reference_audio_path: str,
        language: str = "en",
        emotion: str = "neutral",
        exaggeration: float = 0.70,
        cfg_weight: float = 0.65,
        temperature: float = 0.80,
        pitch_shift_semitones: float = 0.0,
        tempo_scale: float = 1.0,
    ) -> Tuple[str, float, int, str]:
        """
        Synthesizes text conditioned on reference audio prompt.
        Supports affect retargeting (pitch shifting, tempo scaling, and spectral shaping).
        Returns: (output_wav_path, duration_seconds, latency_ms, engine_name)
        """
        start_time = time.time()
        storage_base = settings.get_storage_path()
        output_dir = storage_base / "generated_audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_filename = f"chatterbox_{uuid.uuid4().hex[:12]}.wav"
        output_path = output_dir / output_filename

        ref_path = self._resolve_audio_path(reference_audio_path, storage_base)

        # 1. Official Neural Model Generation
        if self.is_loaded and self.model is not None:
            try:
                import torch
                # Call official Chatterbox Multilingual V3 generate method with prosody & accent controls
                wav = self.model.generate(
                    text=text,
                    language_id=language or "en",
                    audio_prompt_path=str(ref_path),
                    exaggeration=exaggeration,
                    cfg_weight=cfg_weight,
                    temperature=temperature,
                )

                if isinstance(wav, torch.Tensor):
                    wav_data = wav.detach().cpu().float().numpy().squeeze()
                else:
                    wav_data = np.asarray(wav, dtype=np.float32).squeeze()

                sr = getattr(self.model, "sr", self.sample_rate)

                # Affect Retargeting & Post-Processing (Pitch shift, tempo scale, spectral affect shaping, peak normalization)
                wav_data = affect_shaper.retarget_waveform(
                    wav_data=wav_data,
                    sample_rate=sr,
                    pitch_shift_semitones=pitch_shift_semitones,
                    tempo_scale=tempo_scale,
                    emotion=emotion,
                )

                sf.write(str(output_path), wav_data, sr, subtype="PCM_16")
                duration = round(len(wav_data) / sr, 2)
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"[Chatterbox Neural V3] Synthesized {duration}s "
                    f"(emotion='{emotion}', exaggeration={exaggeration}, cfg={cfg_weight}, pitch_shift={pitch_shift_semitones}) "
                    f"in {elapsed_ms}ms on {self.device}."
                )
                return str(output_path), duration, elapsed_ms, "chatterbox_v3_neural"

            except Exception as neural_err:
                logger.error(f"[Chatterbox Neural] Generation failed: {neural_err}")
                is_prod = os.environ.get("APP_ENV", "").lower() == "production" or os.environ.get("MOCK_AI", "").lower() == "false"
                if not settings.USE_MOCK_FALLBACK or is_prod:
                    raise RuntimeError(f"Chatterbox neural inference failed: {neural_err}")
                logger.warning("[Chatterbox] Falling back to acoustic synthesis engine.")

        # 2. Strict Production Guard
        is_prod = os.environ.get("APP_ENV", "").lower() == "production" or os.environ.get("MOCK_AI", "").lower() == "false"
        if not self.is_loaded and (not settings.USE_MOCK_FALLBACK or is_prod):
            raise RuntimeError(
                "Official Chatterbox Multilingual V3 neural model is not loaded. "
                "Silent fallback to acoustic synthesis is prohibited in production mode."
            )

        # 3. Development Acoustic Fallback
        out_p, dur, ms = self._synthesize_acoustic(text, ref_path, output_path, start_time)
        return out_p, dur, ms, "acoustic_fallback"

    def analyze_voice(self, reference_audio_path: str) -> Dict[str, Any]:
        """Analyzes reference voice audio to extract acoustic metrics and affect bias."""
        storage_base = settings.get_storage_path()
        ref_path = self._resolve_audio_path(reference_audio_path, storage_base)
        return affect_shaper.analyze_acoustic_affect(str(ref_path))

    def _resolve_audio_path(self, reference_audio_path: str, storage_base: Path) -> Path:
        """Resolves reference audio file path."""
        ref_path = Path(reference_audio_path)
        if not ref_path.is_absolute():
            cand = storage_base / reference_audio_path
            if cand.exists():
                return cand
            cand_ref = storage_base / "reference_audio" / reference_audio_path
            if cand_ref.exists():
                return cand_ref
        return ref_path

    def _synthesize_acoustic(
        self,
        text: str,
        ref_path: Path,
        output_path: Path,
        start_time: float,
    ) -> Tuple[str, float, int]:
        """Acoustic pitch-modulated synthesis for local development/testing without GPU."""
        base_pitch = 160.0
        if ref_path.exists():
            try:
                ref_data, ref_sr = sf.read(str(ref_path), dtype="float32")
                if ref_data.ndim > 1:
                    ref_data = np.mean(ref_data, axis=1)
                corr = np.correlate(
                    ref_data[:min(len(ref_data), ref_sr * 2)],
                    ref_data[:min(len(ref_data), ref_sr * 2)],
                    mode="full"
                )
                corr = corr[len(corr) // 2:]
                min_lag = int(ref_sr / 350)
                max_lag = int(ref_sr / 80)
                if len(corr) > max_lag:
                    peak_lag = min_lag + np.argmax(corr[min_lag:max_lag])
                    if peak_lag > 0:
                        est_pitch = ref_sr / peak_lag
                        if 75.0 <= est_pitch <= 400.0:
                            base_pitch = float(est_pitch)
            except Exception as e:
                logger.warning(f"[Chatterbox Acoustic] Pitch estimation: {e}")

        words = text.strip().split()
        num_words = max(len(words), 1)
        target_duration = max(1.2, num_words * 0.32 + 0.25)
        num_samples = int(target_duration * self.sample_rate)

        t = np.linspace(0, target_duration, num_samples, endpoint=False)
        prosody = np.sin(2 * np.pi * 0.8 * t) * (base_pitch * 0.08)
        f0 = base_pitch + prosody

        phase = 2 * np.pi * np.cumsum(f0) / self.sample_rate
        voice_wave = (
            0.6 * np.sin(phase) +
            0.3 * np.sin(2 * phase) +
            0.15 * np.sin(3 * phase) +
            0.08 * np.sin(4 * phase)
        )

        syllable_rate = 4.0
        envelope = np.clip(np.sin(2 * np.pi * syllable_rate * t), 0.1, 1.0)
        fade_samples = int(0.08 * self.sample_rate)
        window = np.ones(num_samples)
        window[:fade_samples] = np.linspace(0, 1, fade_samples)
        window[-fade_samples:] = np.linspace(1, 0, fade_samples)

        synthesized = voice_wave * envelope * window
        synthesized = (synthesized / (np.max(np.abs(synthesized)) + 1e-6)) * 0.84

        sf.write(str(output_path), synthesized.astype(np.float32), self.sample_rate, subtype="PCM_16")
        elapsed_ms = int((time.time() - start_time) * 1000)
        return str(output_path), round(target_duration, 2), elapsed_ms


synthesizer = ChatterboxSynthesizer()
