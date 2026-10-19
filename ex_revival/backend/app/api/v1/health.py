from fastapi import APIRouter
from app.config import get_settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health and provider configuration check."""
    settings = get_settings()

    stt_prov = (settings.STT_PROVIDER or "mock").lower()
    llm_prov = (settings.LLM_PROVIDER or "mock").lower()

    # Determine STT status
    if settings.MOCK_AI:
        stt_status = "available" if stt_prov == "mock" else ("available" if settings.GEMINI_API_KEY or settings.STT_API_KEY else "configured")
    else:
        if stt_prov == "gemini":
            stt_status = "available" if bool(settings.GEMINI_API_KEY) else "failed"
        elif stt_prov == "openai":
            stt_status = "available" if bool(settings.STT_API_KEY) else "failed"
        elif stt_prov == "mock":
            stt_status = "failed"
        else:
            stt_status = "configured"

    # Determine LLM status
    if settings.MOCK_AI:
        llm_status = "available" if llm_prov == "mock" else ("available" if settings.GEMINI_API_KEY or settings.LLM_API_KEY else "configured")
    else:
        if llm_prov == "gemini":
            llm_status = "available" if bool(settings.GEMINI_API_KEY) else "failed"
        elif llm_prov == "openai":
            llm_status = "available" if bool(settings.LLM_API_KEY) else "failed"
        elif llm_prov == "mock":
            llm_status = "failed"
        else:
            llm_status = "configured"

    # Determine Voice status
    voice_status = "available"
    try:
        from app.services.chatterbox_engine import chatterbox_engine
        telem = await chatterbox_engine.get_health_telemetry()
        if not telem or not telem.get("model_loaded"):
            voice_status = "configured"
    except Exception:
        voice_status = "configured"

    stt_model = settings.GEMINI_STT_MODEL if stt_prov == "gemini" else ("whisper-1" if stt_prov == "openai" else "mock-stt")
    llm_model = settings.GEMINI_LLM_MODEL if llm_prov == "gemini" else (settings.LLM_MODEL if llm_prov == "openai" else "mock-llm")

    return HealthResponse(
        status="ok",
        version="1.0.0",
        environment=settings.APP_ENV,
        database="sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql",
        stt_provider=settings.STT_PROVIDER,
        llm_provider=settings.LLM_PROVIDER,
        voice_engine=settings.VOICE_ENGINE_PROVIDER,
        mock_ai=settings.MOCK_AI,
        stt_status=stt_status,
        llm_status=llm_status,
        voice_status=voice_status,
        stt_model=stt_model,
        llm_model=llm_model,
    )
