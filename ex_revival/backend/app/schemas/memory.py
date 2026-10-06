from datetime import datetime
from pydantic import BaseModel, Field


class MemoryCreateRequest(BaseModel):
    memory_text: str = Field(..., min_length=2, max_length=1000)
    importance: str = Field(default="medium", pattern="^(high|medium|low)$")


class MemoryResponse(BaseModel):
    id: str
    revival_id: str
    memory_text: str
    importance: str
    created_at: datetime

    model_config = {"from_attributes": True}
