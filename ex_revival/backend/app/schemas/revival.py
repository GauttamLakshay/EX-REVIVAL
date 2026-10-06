from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class RevivalCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    language: str = Field(default="en", max_length=50)
    personality: str = Field(default="", max_length=2000)
    speaking_style: str = Field(default="", max_length=2000)
    relationship_context: str = Field(default="", max_length=2000)
    voice_authorized: bool = Field(default=False, description="Explicit user confirmation of voice rights")


class RevivalUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    language: Optional[str] = Field(None, max_length=50)
    personality: Optional[str] = Field(None, max_length=2000)
    speaking_style: Optional[str] = Field(None, max_length=2000)
    relationship_context: Optional[str] = Field(None, max_length=2000)
    voice_authorized: Optional[bool] = None


class VoiceAssetResponse(BaseModel):
    id: str
    revival_id: str
    storage_path: str
    duration_seconds: float
    sample_rate: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RevivalResponse(BaseModel):
    id: str
    user_id: str
    name: str
    language: str
    personality: str
    speaking_style: str
    relationship_context: str
    reference_audio_path: Optional[str] = None
    voice_authorized: bool
    created_at: datetime
    updated_at: datetime
    voice_assets: List[VoiceAssetResponse] = []

    model_config = {"from_attributes": True}


class VoiceValidateResponse(BaseModel):
    is_valid: bool
    duration_seconds: float
    sample_rate: int
    channels: int
    has_silence: bool
    has_clipping: bool
    message: str


class VoicePreviewRequest(BaseModel):
    phrase: str = Field(..., min_length=1, max_length=300)


class VoicePreviewResponse(BaseModel):
    audio_url: str
    phrase: str
    duration_seconds: float
    latency_ms: int
