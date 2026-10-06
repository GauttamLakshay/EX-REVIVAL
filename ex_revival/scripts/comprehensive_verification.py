import os
import sys
import time
import json
import asyncio
from pathlib import Path
import soundfile as sf
import numpy as np
import httpx

# Ensure paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "backend"))

async def test_all():
    results = {}
    print("=" * 60)
    print("EX REVIVAL — COMPREHENSIVE VERIFICATION & REALITY CHECK")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. REAL CHATTERBOX INFERENCE CHECK
    # ---------------------------------------------------------
    print("\n--- 1. REAL CHATTERBOX INFERENCE CHECK ---")
    torch_available = False
    cuda_available = False
    chatterbox_pkg_available = False
    weights_available = False

    try:
        import torch
        torch_available = True
        cuda_available = torch.cuda.is_available()
    except ImportError:
        pass

    try:
        import chatterbox
        chatterbox_pkg_available = True
    except ImportError:
        pass

    model_dir = ROOT_DIR / "voice_service" / "models" / "chatterbox_v3"
    weights_available = model_dir.exists() and any(model_dir.iterdir())

    print(f"PyTorch available: {torch_available}")
    print(f"CUDA available: {cuda_available}")
    print(f"Chatterbox package: {chatterbox_pkg_available}")
    print(f"Model weights present: {weights_available}")

    # Now run synthesis via voice_service inference
    from voice_service.app.inference import synthesizer
    ref_audio_path = str(ROOT_DIR / "storage" / "reference_audio" / "sample_alex.wav")
    
    # Check if sample_alex.wav exists, else check storage
    if not Path(ref_audio_path).exists():
        cand = ROOT_DIR / "storage" / "sample_alex.wav"
        if cand.exists():
            ref_audio_path = str(cand)

    print(f"Testing reference audio: {ref_audio_path} (exists: {Path(ref_audio_path).exists()})")

    t0 = time.time()
    out_path, dur, latency = synthesizer.synthesize(
        text="Hey, how are you?",
        reference_audio_path=ref_audio_path,
        language="en",
        emotion="neutral"
    )
    t_end = time.time()
    actual_latency = int((t_end - t0) * 1000)

    # Inspect generated audio file
    out_file = Path(out_path)
    file_exists = out_file.exists()
    is_playable = False
    audio_dur = 0.0
    rms = 0.0
    if file_exists:
        try:
            data, sr = sf.read(str(out_file))
            audio_dur = len(data) / sr
            is_playable = True
            rms = float(np.sqrt(np.mean(data ** 2)))
        except Exception as e:
            print("Audio read error:", e)

    results["chatterbox"] = {
        "model_loaded": synthesizer.is_loaded,
        "torch_available": torch_available,
        "cuda_available": cuda_available,
        "output_path": str(out_path),
        "output_duration": round(audio_dur, 2),
        "inference_latency_ms": actual_latency,
        "file_exists": file_exists,
        "is_playable": is_playable,
        "is_silent": rms < 1e-4,
        "rms": round(rms, 4)
    }
    print("Chatterbox Synthesis Result:")
    print(json.dumps(results["chatterbox"], indent=2))

    # ---------------------------------------------------------
    # 2. VOICE SERVICE HTTP API VERIFICATION
    # ---------------------------------------------------------
    print("\n--- 2. VOICE SERVICE HTTP API VERIFICATION ---")
    from voice_service.app.main import app as voice_app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=voice_app), base_url="http://test") as client:
        health_res = await client.get("/health")
        print("Voice service /health:", health_res.status_code, health_res.json())

        syn_payload = {
            "text": "Hey, how are you doing today?",
            "reference_audio": ref_audio_path,
            "language": "en",
            "emotion": "neutral"
        }
        syn_res = await client.post("/synthesize", json=syn_payload)
        print("Voice service /synthesize:", syn_res.status_code, syn_res.json())
        results["voice_service"] = {
            "health_status": health_res.status_code,
            "synthesize_status": syn_res.status_code,
            "synthesize_response": syn_res.json()
        }

    # ---------------------------------------------------------
    # 3. BACKEND TO VOICE SERVICE COMMUNICATION
    # ---------------------------------------------------------
    print("\n--- 3. BACKEND CHATTERBOX ENGINE INTEGRATION ---")
    from app.services.chatterbox_engine import chatterbox_engine
    engine_out = await chatterbox_engine.synthesize(
        text="Testing orchestrator synthesis",
        reference_audio_path=ref_audio_path
    )
    print(f"Chatterbox engine returned path: {engine_out}")
    print(f"File exists: {Path(engine_out).exists()}")
    results["engine_integration"] = {
        "output_path": engine_out,
        "exists": Path(engine_out).exists()
    }

    # ---------------------------------------------------------
    # 4. COMPLETE PIPELINE LATENCY & EXECUTION
    # ---------------------------------------------------------
    print("\n--- 4. COMPLETE AI PIPELINE EXECUTION ---")
    from app.services.stt_service import stt_service
    from app.services.llm_service import llm_service, build_system_prompt

    # Read reference audio bytes for STT
    audio_bytes = Path(ref_audio_path).read_bytes()
    t_stt_0 = time.time()
    transcript, stt_lat = await stt_service.transcribe(audio_bytes, "user_audio.wav")
    t_stt_end = time.time()

    prompt = build_system_prompt(
        name="Alex",
        personality="Warm, caring, reflective",
        speaking_style="Casual, slow-paced",
        language="en",
        relationship_context="Close childhood friend",
        recent_messages=[],
        memories=["We watched the meteor shower from the rooftop in July."],
        transcript=transcript
    )

    t_llm_0 = time.time()
    llm_resp, llm_lat = await llm_service.generate(prompt, transcript)
    t_llm_end = time.time()

    t_voice_0 = time.time()
    gen_audio_path = await chatterbox_engine.synthesize(llm_resp, ref_audio_path)
    t_voice_end = time.time()

    total_latency_ms = int((time.time() - t_stt_0) * 1000)

    results["pipeline"] = {
        "transcript": transcript,
        "llm_response": llm_resp,
        "generated_audio_path": gen_audio_path,
        "stt_latency_ms": int((t_stt_end - t_stt_0) * 1000),
        "llm_latency_ms": int((t_llm_end - t_llm_0) * 1000),
        "voice_latency_ms": int((t_voice_end - t_voice_0) * 1000),
        "total_latency_ms": total_latency_ms
    }
    print("Pipeline Execution Result:")
    print(json.dumps(results["pipeline"], indent=2))

    # ---------------------------------------------------------
    # 5. BACKEND API HEALTH & SWAGGER VERIFICATION
    # ---------------------------------------------------------
    print("\n--- 5. BACKEND API HEALTH & DOCS ---")
    from app.main import app as backend_app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=backend_app), base_url="http://test") as client:
        health_res = await client.get("/api/v1/health")
        docs_res = await client.get("/docs")
        openapi_res = await client.get("/openapi.json")

        print("Backend /api/v1/health:", health_res.status_code, health_res.json())
        print("Backend /docs status:", docs_res.status_code)
        print("Backend /openapi.json status:", openapi_res.status_code)

        results["api"] = {
            "health_status": health_res.status_code,
            "health_body": health_res.json(),
            "docs_status": docs_res.status_code,
            "openapi_status": openapi_res.status_code,
            "openapi_title": openapi_res.json().get("info", {}).get("title")
        }

    # Save summary
    out_json = ROOT_DIR / "verification_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAll verification tasks completed. Saved to {out_json}")

if __name__ == "__main__":
    asyncio.run(test_all())
