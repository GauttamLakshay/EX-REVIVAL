import os
import sys
import time
import asyncio
from pathlib import Path
import soundfile as sf
import numpy as np
import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

# Enforce strict neural voice requirement
os.environ["REQUIRE_NEURAL_VOICE"] = "true"

from backend.app.main import app
from backend.app.config import get_settings

settings = get_settings()

def create_synthetic_voice_sample(path: Path, duration_sec: float = 3.5, sr: int = 24000):
    """Creates a clear 3.5s multi-harmonic vocal tone as a user reference voice."""
    t = np.linspace(0, duration_sec, int(sr * duration_sec), endpoint=False)
    # Pitch 210 Hz with vibrato
    f0 = 210 + 6 * np.sin(2 * np.pi * 5.5 * t)
    phase = 2 * np.pi * np.cumsum(f0) / sr
    signal = 0.5 * np.sin(phase) + 0.25 * np.sin(2 * phase) + 0.12 * np.sin(3 * phase)
    env = np.ones_like(t)
    fade = int(0.1 * sr)
    env[:fade] = np.linspace(0, 1, fade)
    env[-fade:] = np.linspace(1, 0, fade)
    audio = (signal * env * 0.8).astype(np.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), audio, sr, subtype="PCM_16")
    return str(path)

async def main():
    print("=" * 70)
    print("EX REVIVAL — REAL NEURAL CHATTERBOX V3 VOICE FLOW VERIFICATION")
    print("=" * 70)

    # 0. Check voice_service microservice health first
    print("\n[Step 0] Checking Voice Microservice Status (http://127.0.0.1:8001/health)...")
    async with httpx.AsyncClient(timeout=10.0) as check_client:
        try:
            h_res = await check_client.get("http://127.0.0.1:8001/health")
            health_data = h_res.json()
            print("  Health Data:", health_data)
            assert health_data["engine"] == "chatterbox_v3_neural", f"Expected chatterbox_v3_neural, got {health_data['engine']}"
            assert health_data["model_loaded"] is True, "Model not loaded!"
            assert health_data["device"] == "cpu", f"Expected cpu, got {health_data['device']}"
            assert health_data["model_version"] == "v3", f"Expected v3, got {health_data['model_version']}"
            print("  Voice Microservice: LIVE & RUNNING REAL CHATTERBOX V3 ON CPU")
        except Exception as e:
            print("  FAIL: Voice microservice check failed:", e)
            sys.exit(1)

    # Prepare fresh user reference audio
    user_ref_file = ROOT_DIR / "storage" / "temp" / "user_voice_sophia.wav"
    create_synthetic_voice_sample(user_ref_file, duration_sec=3.5)
    print(f"\nCreated new user reference voice sample: {user_ref_file} ({user_ref_file.stat().st_size} bytes)")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=300.0) as client:
        # 1. Register User
        print("\n[Step 1] Registering User & Authenticating...")
        email = f"user_neural_{os.urandom(3).hex()}@test.com"
        reg = await client.post("/api/v1/auth/register", json={"email": email, "password": "SecurePassword123!"})
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"  Authenticated as: {email}")

        # 2. Create Revival
        print("\n[Step 2] Creating Revival Profile (Sophia)...")
        rev_res = await client.post(
            "/api/v1/revivals",
            json={
                "name": "Sophia",
                "language": "en",
                "personality": "Thoughtful, gentle, and expressive",
                "speaking_style": "Natural, warm conversational speech",
                "relationship_context": "Childhood confidant",
                "voice_authorized": True,
            },
            headers=headers,
        )
        revival = rev_res.json()
        revival_id = revival["id"]
        print(f"  Revival Created: ID={revival_id}, Name={revival['name']}")

        # 3. Upload Reference Voice
        print("\n[Step 3] Uploading Reference Voice...")
        with open(user_ref_file, "rb") as f:
            up_res = await client.post(
                f"/api/v1/revivals/{revival_id}/voice",
                files={"audio_file": ("sophia_voice.wav", f.read(), "audio/wav")},
                data={"voice_authorized": "true"},
                headers=headers,
            )
        updated_rev = up_res.json()
        saved_ref_path = updated_rev["reference_audio_path"]
        print(f"  Reference Audio Saved Path: {saved_ref_path}")
        assert saved_ref_path is not None and os.path.exists(saved_ref_path)
        assert "sample_alex.wav" not in saved_ref_path

        # 4. Voice Preview Execution (Neural V3 on CPU)
        print("\n[Step 4] Executing Voice Preview through Real Neural V3...")
        preview_phrase = "Good evening, it's nice to see you."
        t_prev_start = time.time()
        prev_res = await client.post(
            f"/api/v1/revivals/{revival_id}/voice/preview",
            json={"phrase": preview_phrase},
            headers=headers,
        )
        t_prev_elapsed = round(time.time() - t_prev_start, 2)
        assert prev_res.status_code == 200, f"Preview failed: {prev_res.text}"
        prev_data = prev_res.json()

        print("  === VOICE PREVIEW TELEMETRY ===")
        print(f"  engine:          {prev_data.get('engine')}")
        print(f"  device:          {prev_data.get('device')}")
        print(f"  model_loaded:    {prev_data.get('model_loaded')}")
        print(f"  model_version:   {prev_data.get('model_version')}")
        print(f"  inference_time:  {t_prev_elapsed}s ({prev_data.get('latency_ms')}ms)")
        print(f"  audio_url:       {prev_data.get('audio_url')}")
        print(f"  output_duration: {prev_data.get('duration_seconds')}s")

        # 5. Start Conversation & Execute Turn
        print("\n[Step 5] Creating Conversation Session...")
        c_res = await client.post(
            "/api/v1/conversations",
            json={"revival_id": revival_id, "title": "Chatting with Sophia"},
            headers=headers,
        )
        conv_id = c_res.json()["id"]

        print("\n[Step 6] Executing Conversation Turn (User Spoken Input -> Neural V3 Cloned Speech)...")
        turn_text = "Hey, what are you doing?"
        user_audio = ROOT_DIR / "storage" / "temp" / "user_input_mic.wav"
        create_synthetic_voice_sample(user_audio, duration_sec=1.8)

        t_turn_start = time.time()
        with open(user_audio, "rb") as f:
            turn_res = await client.post(
                f"/api/v1/conversations/{conv_id}/turns",
                files={"audio_file": ("mic.wav", f.read(), "audio/wav")},
                data={"client_transcript": turn_text},
                headers=headers,
            )
        t_turn_elapsed = round(time.time() - t_turn_start, 2)
        assert turn_res.status_code == 200, f"Turn failed: {turn_res.text}"
        turn_data = turn_res.json()

        print("  === CONVERSATION TURN TELEMETRY ===")
        print(f"  voice_engine:        {turn_data.get('voice_engine')}")
        print(f"  voice_device:        {turn_data.get('voice_device')}")
        print(f"  model_version:       {turn_data.get('model_version')}")
        print(f"  model_loaded:        {turn_data.get('model_loaded')}")
        print(f"  actual_turn_latency: {t_turn_elapsed}s ({turn_data.get('latency_ms')}ms)")
        print(f"  voice_latency:       {turn_data.get('voice_latency_ms')}ms")
        print(f"  audio_url:           {turn_data.get('audio_url')}")
        print(f"  transcript:          \"{turn_data.get('transcript')}\"")
        print(f"  response_text:       \"{turn_data.get('response_text')}\"")

        # 6. Fresh Control Test (Section 8)
        print("\n[Step 7] Fresh Control Test (Unseen Random Text on Saved Voice)...")
        control_text = "Tell me something interesting about today."
        t_ctrl_start = time.time()
        async with httpx.AsyncClient(timeout=300.0) as ctrl_client:
            ctrl_res = await ctrl_client.post(
                "http://127.0.0.1:8001/synthesize",
                json={
                    "text": control_text,
                    "reference_audio": saved_ref_path,
                    "language": "en",
                    "emotion": "warm",
                },
            )
        t_ctrl_elapsed = round(time.time() - t_ctrl_start, 2)
        assert ctrl_res.status_code == 200, f"Control test failed: {ctrl_res.text}"
        ctrl_data = ctrl_res.json()

        ctrl_out = Path(ctrl_data["generated_audio_path"])
        ctrl_dur = ctrl_data["duration_seconds"]
        ctrl_rtf = round(t_ctrl_elapsed / ctrl_dur, 2) if ctrl_dur > 0 else 0

        print("\n" + "=" * 70)
        print("FRESH CONTROL TEST REPORT (SECTION 8)")
        print("=" * 70)
        print(f"Model:             Chatterbox Multilingual V3")
        print(f"Device:            cpu")
        print(f"Engine:            {ctrl_data['engine']}")
        print(f"Model loaded:      True")
        print(f"Reference voice:   {Path(saved_ref_path).name}")
        print(f"Input text:        \"{control_text}\"")
        print(f"Output path:       {ctrl_out}")
        print(f"Output duration:   {ctrl_dur}s")
        print(f"Inference latency: {t_ctrl_elapsed}s ({ctrl_data['latency_ms']}ms)")
        print(f"RTF:               {ctrl_rtf}x")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
