from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_STORAGE = str(PROJECT_ROOT / "storage")


class VoiceServiceSettings(BaseSettings):
    PORT: int = 8001
    HOST: str = "0.0.0.0"
    MODEL_DEVICE: str = "cpu"
    STORAGE_PATH: str = DEFAULT_STORAGE
    USE_MOCK_FALLBACK: bool = True
    MODEL_CHECKPOINT_PATH: str = "./models/chatterbox_v3"

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


settings = VoiceServiceSettings()

