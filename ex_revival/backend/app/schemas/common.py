from typing import Optional, Any
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    environment: str
    database: str
    stt_provider: str
    llm_provider: str
    voice_engine: str
    mock_ai: bool
    stt_status: Optional[str] = "available"
    llm_status: Optional[str] = "available"
    voice_status: Optional[str] = "available"
    stt_model: Optional[str] = None
    llm_model: Optional[str] = None
