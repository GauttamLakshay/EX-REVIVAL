import io
import pytest
import numpy as np
import soundfile as sf


def generate_wav(duration: float = 2.0, sample_rate: int = 24000) -> bytes:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = (0.4 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    bio = io.BytesIO()
    sf.write(bio, tone, sample_rate, format="WAV")
    return bio.getvalue()


@pytest.mark.asyncio
async def test_conversation_complete_ai_pipeline(client):
    # 1. Register User
    reg = await client.post("/api/v1/auth/register", json={"email": "pipeline@test.com", "password": "securepass123"})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Alex Revival
    rev_payload = {
        "name": "Alex",
        "language": "en",
        "personality": "Funny + caring",
        "speaking_style": "Casual",
        "relationship_context": "Best friend",
        "voice_authorized": True,
    }
    rev_resp = await client.post("/api/v1/revivals", json=rev_payload, headers=headers)
    rev_id = rev_resp.json()["id"]

    # 3. Upload Reference Voice for Alex
    ref_audio = generate_wav(duration=3.0)
    files = {"audio_file": ("alex_voice.wav", ref_audio, "audio/wav")}
    await client.post(f"/api/v1/revivals/{rev_id}/voice", files=files, headers=headers)

    # 4. Add a long-term memory
    mem_resp = await client.post(
        f"/api/v1/revivals/{rev_id}/memories",
        json={"memory_text": "User was selected for a hackathon.", "importance": "high"},
        headers=headers,
    )
    assert mem_resp.status_code == 201

    # 5. Create Conversation
    conv_resp = await client.post(
        "/api/v1/conversations",
        json={"revival_id": rev_id, "title": "Catching up with Alex"},
        headers=headers,
    )
    assert conv_resp.status_code == 201
    conv_id = conv_resp.json()["id"]

    # 6. Execute Section 40 Acceptance Test Turn:
    # User says: "Hey, what are you doing?"
    user_speech = generate_wav(duration=2.0)
    turn_files = {"audio_file": ("user_mic.wav", user_speech, "audio/wav")}
    turn_data = {"client_transcript": "Hey, what are you doing?"}

    turn_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/turns",
        files=turn_files,
        data=turn_data,
        headers=headers,
    )
    assert turn_resp.status_code == 200
    turn_data = turn_resp.json()

    assert turn_data["transcript"] == "Hey, what are you doing?"
    assert "chilling" in turn_data["response_text"].lower() or "nothing much" in turn_data["response_text"].lower()
    assert turn_data["audio_url"] != ""
    assert turn_data["latency_ms"] > 0
    assert turn_data["status"] == "completed"

    # 7. Check that turn was persisted in conversation history
    get_conv = await client.get(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert get_conv.status_code == 200
    conv_data = get_conv.json()
    assert len(conv_data["messages"]) == 2
    assert conv_data["messages"][0]["role"] == "user"
    assert conv_data["messages"][0]["text"] == "Hey, what are you doing?"
    assert conv_data["messages"][1]["role"] == "assistant"
    assert conv_data["messages"][1]["audio_url"] is not None

    # 8. Test memory retrieval in subsequent turn
    turn2_data = {"client_transcript": "Do you remember the hackathon?"}
    turn2_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/turns",
        data=turn2_data,
        headers=headers,
    )
    assert turn2_resp.status_code == 200
    t2 = turn2_resp.json()
    assert t2["transcript"] == "Do you remember the hackathon?"

    # Verify conversation now has 4 messages
    get_conv2 = await client.get(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert len(get_conv2.json()["messages"]) == 4


@pytest.mark.asyncio
async def test_conversation_errors_and_ownership(client):
    reg = await client.post("/api/v1/auth/register", json={"email": "err_user@test.com", "password": "password123"})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    rev = await client.post("/api/v1/revivals", json={"name": "NoVoice", "language": "en"}, headers=headers)
    rev_id = rev.json()["id"]

    conv = await client.post("/api/v1/conversations", json={"revival_id": rev_id}, headers=headers)
    conv_id = conv.json()["id"]

    # Turn without reference voice sample returns 400
    turn_resp = await client.post(
        f"/api/v1/conversations/{conv_id}/turns",
        data={"client_transcript": "Hello"},
        headers=headers,
    )
    assert turn_resp.status_code == 400
    assert "reference voice" in turn_resp.json()["detail"].lower()
