from typing import Optional, List
from pydantic import BaseModel, Field


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize into speech")
    reference_audio: str = Field(..., description="Path or identifier to the reference voice audio sample")
    language: Optional[str] = Field(default="en", description="Target spoken language code (e.g. en, hi, es)")
    emotion: Optional[str] = Field(default="neutral", description="Target emotional tone (e.g. warm, caring, funny, sad, excited)")
    exaggeration: Optional[float] = Field(default=0.70, description="Prosodic expressiveness and pitch range (0.3-1.0)")
    cfg_weight: Optional[float] = Field(default=0.65, description="Classifier-Free Guidance weight for reference accent/timbre fidelity (0.3-1.0)")
    temperature: Optional[float] = Field(default=0.80, description="Sampling randomness and expressiveness stability (0.5-1.0)")
    pitch_shift_semitones: Optional[float] = Field(default=0.0, description="Acoustic pitch offset in semitones (-4.0 to +4.0)")
    tempo_scale: Optional[float] = Field(default=1.0, description="Speaking tempo multiplier (0.75 to 1.25)")


class SynthesizeResponse(BaseModel):
    status: str = "success"
    generated_audio_path: str
    duration_seconds: float
    sample_rate: int
    latency_ms: int
    engine: str = "chatterbox_v3"


class VoiceAnalyzeRequest(BaseModel):
    reference_audio: str = Field(..., description="Path to reference audio file to analyze")


class VoiceAnalyzeResponse(BaseModel):
    status: str = "success"
    duration_seconds: float
    sample_rate: int
    base_pitch_hz: float
    pitch_std_hz: float
    pitch_range_hz: List[float]
    mean_energy_rms: float
    estimated_wpm: int
    detected_arousal: float
    inferred_baseline_emotion: str
    resting_pitch_hz: float
    resting_wpm: int
