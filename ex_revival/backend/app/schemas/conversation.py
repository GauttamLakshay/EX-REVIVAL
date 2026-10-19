from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    revival_id: str
    title: Optional[str] = "New Conversation"


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    text: str
    audio_path: Optional[str] = None
    audio_url: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: str
    revival_id: str
    title: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    messages: List[MessageResponse] = []

    model_config = {"from_attributes": True}


class TurnResponse(BaseModel):
    turn_id: str
    conversation_id: str
    transcript: str
    response_text: str
    audio_url: str
    latency_ms: int
    stt_latency_ms: int = 0
    llm_latency_ms: int = 0
    voice_latency_ms: int = 0
    total_latency_ms: Optional[int] = None
    voice_engine: Optional[str] = "chatterbox_v3_neural"
    voice_device: Optional[str] = "cpu"
    model_version: Optional[str] = "v3"
    model_loaded: Optional[bool] = True
    status: str = "completed"
