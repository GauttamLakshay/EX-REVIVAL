from fastapi import APIRouter
from app.config import get_settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health and provider configuration check."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment=settings.APP_ENV,
        database="sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql",
        stt_provider=settings.STT_PROVIDER,
        llm_provider=settings.LLM_PROVIDER,
        voice_engine=settings.VOICE_ENGINE_PROVIDER,
        mock_ai=settings.MOCK_AI,
    )
