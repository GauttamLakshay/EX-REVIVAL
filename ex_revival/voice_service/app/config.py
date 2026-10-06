from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_STORAGE = str(PROJECT_ROOT / "storage")


class VoiceServiceSettings(BaseSettings):
    PORT: int = 8001
    HOST: str = "0.0.0.0"

    # Inference & Hardware Acceleration
    MODEL_DEVICE: str = "auto"          # "cuda", "cpu", or "auto"
    CUDA_DEVICE_INDEX: int = 0          # Target GPU index (0 for first GPU)
    USE_FP16: bool = True               # Half-precision FP16 for NVIDIA Tensor Cores
    WARMUP_ON_STARTUP: bool = True      # Run dry inference to pre-allocate CUDA cache
    USE_MOCK_FALLBACK: bool = True       # Fallback to acoustic synthesis if weights/CUDA missing

    # Model Artifacts & HuggingFace
    MODEL_CHECKPOINT_PATH: str = "./models/chatterbox_v3"
    MODEL_REPO_ID: str = "ResembleAI/chatterbox"
    HF_TOKEN: str = ""
    AUTO_DOWNLOAD_WEIGHTS: bool = False

    # Audio Parameters
    STORAGE_PATH: str = DEFAULT_STORAGE
    SAMPLE_RATE: int = 24000
    MAX_AUDIO_LENGTH_SECONDS: float = 30.0

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_storage_path(self) -> Path:
        p = Path(self.STORAGE_PATH)
        if not p.is_absolute():
            voice_dir = Path(__file__).resolve().parent.parent
            if str(self.STORAGE_PATH).startswith(".."):
                return (voice_dir / p).resolve()
            return (PROJECT_ROOT / p).resolve()
        return p.resolve()

    def get_checkpoint_path(self) -> Path:
        p = Path(self.MODEL_CHECKPOINT_PATH)
        if not p.is_absolute():
            voice_dir = Path(__file__).resolve().parent.parent
            return (voice_dir / p).resolve()
        return p.resolve()


settings = VoiceServiceSettings()
