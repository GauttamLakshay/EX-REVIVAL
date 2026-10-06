from functools import lru_cache
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./ex_revival.db"

    # Security
    JWT_SECRET: str = "super_secret_jwt_key_ex_revival_dev_2026_change_in_prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Voice Service
    VOICE_SERVICE_URL: str = "http://localhost:8001"
    VOICE_ENGINE_PROVIDER: str = "chatterbox"

    # AI Providers
    STT_PROVIDER: str = "mock"
    STT_API_KEY: str = ""
    WHISPER_MODEL_SIZE: str = "base"

    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: str = ""

    # Storage
    STORAGE_PROVIDER: str = "local"
    STORAGE_LOCAL_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "storage")
    S3_BUCKET_NAME: str = "ex-revival-audio"
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""

    # Mock Mode
    MOCK_AI: bool = True

    def get_storage_path(self) -> Path:
        p = Path(self.STORAGE_LOCAL_PATH)
        if not p.is_absolute():
            backend_dir = Path(__file__).resolve().parent.parent
            if str(self.STORAGE_LOCAL_PATH).startswith(".."):
                return (backend_dir / p).resolve()
            return (backend_dir.parent / p).resolve()
        return p.resolve()

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
