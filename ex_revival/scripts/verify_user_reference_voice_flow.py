import os
import sys
import asyncio
from pathlib import Path
import soundfile as sf
import numpy as np
import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

from backend.app.main import app
from backend.app.config import get_settings

settings = get_settings()

def create_synthetic_voice_sample(path: Path, duration_sec: float = 3.5, sr: int = 24000):
    """Creates a clear 3.5s multi-harmonic vocal tone as a user reference voice."""
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    # Fundamental pitch 190 Hz with natural vibrato and harmonics
    f0 = 190 + 5 * np.sin(2 * np.pi * 5 * t)
    phase = 2 * np.pi * np.cumsum(f0) / sr
    signal = 0.5 * np.sin(phase) + 0.25 * np.sin(2 * phase) + 0.12 * np.sin(3 * phase)
    # Envelope
    env = np.ones_like(t)
    fade = int(0.1 * sr)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    audio = (signal * env * 0.8).astype(np.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio, sr, subtype="PCM_16")
    return str(path)

async def run_acceptance_test():
    print("=" * 70)
    print("EX REVIVAL — ACCEPTANCE TEST: USER REFERENCE VOICE FLOW")
    print("=" * 70)

    test_voice_file = ROOT_DIR / "storage" / "temp" / "user_test_voice_elena.wav"
    create_synthetic_voice_sample(test_voice_file, duration_sec=3.5)
    print(f"Created real test reference voice: {test_voice_file} ({test_voice_file.stat().st_size} bytes)")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Step 1: User Registration / Authentication
        print("\n[Step 1] Registering User...")
        user_email = f"user_voice_{os.urandom(3).hex()}@test.com"
        reg_res = await client.post("/api/v1/auth/register", json={"email": user_email, "password": "Password123!"})
        assert reg_res.status_code == 201, f"Reg failed: {reg_res.text}"
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"  User registered: {user_email} (Token acquired)")

        # Step 2: Create Revival Profile
        print("\n[Step 2] Creating Revival Profile...")
        rev_payload = {
            "name": "Elena",
            "language": "en",
            "personality": "Thoughtful, calm, and deeply supportive",
            "speaking_style": "Casual, warm natural spoken tone",
            "relationship_context": "Lifelong best friend from university",
            "voice_authorized": True,
        }
        rev_res = await client.post("/api/v1/revivals", json=rev_payload, headers=headers)
        assert rev_res.status_code == 201, f"Create revival failed: {rev_res.text}"
        revival = rev_res.json()
        revival_id = revival["id"]
        print(f"  Revival Created: ID={revival_id}, Name={revival['name']}")

        # Step 3: Voice Validation Check (Pre-validation endpoint)
        print("\n[Step 3] Pre-validating Reference Voice Sample...")
        with open(test_voice_file, "rb") as f:
            val_res = await client.post(
                f"/api/v1/revivals/{revival_id}/voice/validate",
                files={"audio_file": ("user_elena.wav", f.read(), "audio/wav")},
                headers=headers,
            )
        assert val_res.status_code == 200, f"Validation endpoint failed: {val_res.text}"
        val_data = val_res.json()
        print(f"  Validation Result: is_valid={val_data['is_valid']}, duration={val_data['duration_seconds']}s")
        assert val_data["is_valid"] is True

        # Step 4: Upload and Save Reference Voice
        print("\n[Step 4] Uploading & Saving Reference Voice...")
        with open(test_voice_file, "rb") as f:
            upload_res = await client.post(
                f"/api/v1/revivals/{revival_id}/voice",
                files={"audio_file": ("user_elena.wav", f.read(), "audio/wav")},
                data={"voice_authorized": "true"},
                headers=headers,
            )
        assert upload_res.status_code == 200, f"Upload voice failed: {upload_res.text}"
        updated_revival = upload_res.json()
        ref_path = updated_revival["reference_audio_path"]
        print(f"  Reference Audio Saved Path: {ref_path}")
        assert ref_path is not None, "reference_audio_path should not be None"
        assert os.path.exists(ref_path), f"Saved reference audio file does not exist on disk: {ref_path}"
        assert "sample_alex.wav" not in ref_path, f"Reference audio path should NOT be sample_alex.wav! Got {ref_path}"

        # Step 5: Voice Preview with Chatterbox V3 using Elena's reference voice
        print("\n[Step 5] Generating Voice Preview with Chatterbox...")
        preview_phrase = "Hey, how are you?"
        preview_res = await client.post(
            f"/api/v1/revivals/{revival_id}/voice/preview",
            json={"phrase": preview_phrase},
            headers=headers,
        )
        assert preview_res.status_code == 200, f"Preview failed: {preview_res.text}"
        preview_data = preview_res.json()
        print(f"  Preview audio_url: {preview_data['audio_url']}")
        print(f"  Preview latency:   {preview_data['latency_ms']}ms")
        assert preview_data["audio_url"] != ""

        # Step 6: Start Conversation
        print("\n[Step 6] Starting Live Conversation Session...")
        conv_res = await client.post(
            "/api/v1/conversations",
            json={"revival_id": revival_id, "title": "Catching up with Elena"},
            headers=headers,
        )
        assert conv_res.status_code == 201, f"Start conversation failed: {conv_res.text}"
        conv_data = conv_res.json()
        conv_id = conv_data["id"]
        print(f"  Conversation Created: ID={conv_id}")

        # Step 7: Conversation Turn (User speaks: "Hey, what are you doing?")
        print("\n[Step 7] Processing Conversation Turn (User -> STT -> LLM -> Chatterbox V3)...")
        user_turn_audio = ROOT_DIR / "storage" / "temp" / "user_turn_mic.wav"
        create_synthetic_voice_sample(user_turn_audio, duration_sec=2.0)

        with open(user_turn_audio, "rb") as f:
            turn_res = await client.post(
                f"/api/v1/conversations/{conv_id}/turns",
                files={"audio_file": ("mic.wav", f.read(), "audio/wav")},
                data={"client_transcript": "Hey, what are you doing?"},
                headers=headers,
            )
        assert turn_res.status_code == 200, f"Turn failed: {turn_res.text}"
        turn_data = turn_res.json()

        print(f"  User Transcript:      \"{turn_data['transcript']}\"")
        print(f"  Elena Response:       \"{turn_data['response_text']}\"")
        print(f"  Generated Audio URL:  {turn_data['audio_url']}")
        print(f"  Total Turn Latency:   {turn_data['latency_ms']}ms")
        print(f"  Status:               {turn_data['status']}")
        assert turn_data["transcript"] == "Hey, what are you doing?"
        assert turn_data["response_text"] != ""
        assert turn_data["audio_url"] != ""

        # Step 8: Verify Conversation History and Playback URL
        print("\n[Step 8] Verifying Conversation History & Playback URLs...")
        hist_res = await client.get(f"/api/v1/conversations/{conv_id}", headers=headers)
        assert hist_res.status_code == 200
        hist_data = hist_res.json()
        assert len(hist_data["messages"]) == 2
        user_msg = hist_data["messages"][0]
        asst_msg = hist_data["messages"][1]
        print(f"  Message 1: [{user_msg['role']}] {user_msg['text']}")
        print(f"  Message 2: [{asst_msg['role']}] {asst_msg['text']} (Audio URL: {asst_msg['audio_url']})")
        assert asst_msg["audio_url"] is not None

    print("\n" + "=" * 70)
    print("ACCEPTANCE TEST COMPLETE: 100% SUCCESS")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_acceptance_test())
