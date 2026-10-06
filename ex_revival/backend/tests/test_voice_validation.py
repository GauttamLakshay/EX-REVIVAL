import io
import pytest
import numpy as np
import soundfile as sf
from app.services.audio_service import AudioService, AudioValidationError


def generate_wav(duration: float = 2.0, sample_rate: int = 44100, amplitude: float = 0.5) -> bytes:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = (amplitude * np.sin(2 * np.pi * 300 * t)).astype(np.float32)
    bio = io.BytesIO()
    sf.write(bio, tone, sample_rate, format="WAV")
    return bio.getvalue()


def test_valid_voice_recording():
    raw_wav = generate_wav(duration=3.0, sample_rate=44100, amplitude=0.4)
    norm_bytes, meta = AudioService.validate_and_normalize(raw_wav)
    assert meta["duration_seconds"] == 3.0
    assert meta["sample_rate"] == 24000
    assert not meta["has_silence"]
    assert not meta["has_clipping"]
    assert len(norm_bytes) > 0


def test_empty_recording():
    with pytest.raises(AudioValidationError, match="empty or corrupted"):
        AudioService.validate_and_normalize(b"")


def test_invalid_format():
    corrupted_bytes = b"NOT_A_VALID_AUDIO_HEADER" + b"\x00" * 200
    with pytest.raises(AudioValidationError, match="Invalid audio format"):
        AudioService.validate_and_normalize(corrupted_bytes)


def test_too_short_recording():
    short_wav = generate_wav(duration=0.4, sample_rate=44100)
    with pytest.raises(AudioValidationError, match="too short"):
        AudioService.validate_and_normalize(short_wav)


def test_silent_sample():
    # Amplitude near zero
    silent_wav = generate_wav(duration=2.0, sample_rate=44100, amplitude=0.00001)
    with pytest.raises(AudioValidationError, match="too quiet or mostly silence"):
        AudioService.validate_and_normalize(silent_wav)


def test_large_upload_exceeds_limit():
    large_dummy_bytes = b"0" * (AudioService.MAX_FILE_SIZE_BYTES + 1024)
    with pytest.raises(AudioValidationError, match="exceeds maximum size"):
        AudioService.validate_and_normalize(large_dummy_bytes)


@pytest.mark.asyncio
async def test_api_voice_validation_endpoint(client):
    # Register and create revival
    reg = await client.post("/api/v1/auth/register", json={"email": "voice_user@test.com", "password": "pass123456"})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    rev = await client.post("/api/v1/revivals", json={"name": "VoiceTest", "language": "en"}, headers=headers)
    rev_id = rev.json()["id"]

    # 1. Validate endpoint with valid audio
    valid_wav = generate_wav(duration=2.5, sample_rate=22050, amplitude=0.5)
    files = {"audio_file": ("test.wav", valid_wav, "audio/wav")}
    val_resp = await client.post(f"/api/v1/revivals/{rev_id}/voice/validate", files=files, headers=headers)
    assert val_resp.status_code == 200
    assert val_resp.json()["is_valid"] is True
    assert val_resp.json()["duration_seconds"] == 2.5

    # 2. Upload reference voice endpoint
    files2 = {"audio_file": ("ref.wav", valid_wav, "audio/wav")}
    data2 = {"voice_authorized": "true"}
    up_resp = await client.post(f"/api/v1/revivals/{rev_id}/voice", files=files2, data=data2, headers=headers)
    assert up_resp.status_code == 200
    updated_rev = up_resp.json()
    assert updated_rev["reference_audio_path"] is not None
    assert updated_rev["voice_authorized"] is True
    assert len(updated_rev["voice_assets"]) == 1

    # 3. Voice Preview endpoint
    prev_resp = await client.post(
        f"/api/v1/revivals/{rev_id}/voice/preview",
        json={"phrase": "Hello, this is a test preview."},
        headers=headers,
    )
    assert prev_resp.status_code == 200
    assert "audio_url" in prev_resp.json()
