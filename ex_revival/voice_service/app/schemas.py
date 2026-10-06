from typing import Optional
from pydantic import BaseModel, Field


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize into speech")
    reference_audio: str = Field(..., description="Path or identifier to the reference voice audio sample")
    language: Optional[str] = Field(default="en", description="Target spoken language code (e.g. en, hi, es)")
    emotion: Optional[str] = Field(default="neutral", description="Target emotional tone (e.g. warm, caring, funny)")


class SynthesizeResponse(BaseModel):
    status: str = "success"
    generated_audio_path: str
    duration_seconds: float
    sample_rate: int
    latency_ms: int
    engine: str = "chatterbox_v3"
