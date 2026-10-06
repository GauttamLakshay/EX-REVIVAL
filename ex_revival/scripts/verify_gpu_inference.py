#!/usr/bin/env python3
"""
EX REVIVAL — Official Resemble AI Chatterbox Multilingual V3 GPU Diagnostics.
Verifies the exact neural pipeline:
CUDA Available -> Package Imported -> Official Model Loaded on CUDA -> Audio Accepted -> Neural Generation -> Output WAV.
"""

import sys
import time
from pathlib import Path
import soundfile as sf
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "voice_service"))


def run_diagnostics():
    print("=" * 70)
    print("EX REVIVAL — CHATTERBOX V3 OFFICIAL NEURAL INFERENCE AUDIT")
    print("=" * 70)

    # Step 1: CUDA Check
    print("\n[Step 1/6] Checking CUDA runtime...")
    torch_available = False
    cuda_available = False
    device_name = "cpu"

    try:
        import torch
        torch_available = True
        cuda_available = torch.cuda.is_available()
        print(f"  PyTorch Installed: {torch.__version__}")
        print(f"  CUDA Available: {cuda_available}")
        if cuda_available:
            dev_idx = 0
            device_name = f"cuda:{dev_idx}"
            gpu_name = torch.cuda.get_device_name(dev_idx)
            cc = torch.cuda.get_device_capability(dev_idx)
            vram_gb = round(torch.cuda.get_device_properties(dev_idx).total_memory / (1024 ** 3), 2)
            print(f"  GPU Name: {gpu_name}")
            print(f"  Compute Capability: {cc[0]}.{cc[1]}")
            print(f"  Total VRAM: {vram_gb} GB")
        else:
            print("  Notice: No CUDA-capable device detected. Host is CPU-only.")
    except ImportError:
        print("  FAIL: PyTorch is not installed in current environment.")

    # Step 2: Chatterbox Package Check
    print("\n[Step 2/6] Importing official 'chatterbox' package...")
    chatterbox_imported = False
    try:
        import chatterbox
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        chatterbox_imported = True
        print(f"  SUCCESS: Official 'chatterbox.mtl_tts.ChatterboxMultilingualTTS' imported successfully.")
    except ImportError as e:
        print(f"  FAIL: Could not import official 'chatterbox.mtl_tts' ({e}).")
        print("  (Install in GPU environment: pip install chatterbox-tts)")

    # Step 3: Official Model Load
    print("\n[Step 3/6] Loading official Chatterbox Multilingual V3 model...")
    model = None
    model_loaded = False
    if chatterbox_imported and torch_available:
        try:
            print(f"  Calling ChatterboxMultilingualTTS.from_pretrained(device='{device_name}', t3_model='v3')...")
            t0 = time.time()
            model = ChatterboxMultilingualTTS.from_pretrained(
                device=device_name,
                t3_model="v3"
            )
            load_sec = round(time.time() - t0, 2)
            model_loaded = True
            print(f"  SUCCESS: Official Chatterbox V3 model loaded on {device_name} in {load_sec}s.")
        except Exception as e:
            print(f"  FAIL: Official model loading failed ({e}).")
    else:
        print("  SKIPPED: Model loading skipped because dependencies are missing on host.")

    # Step 4: Reference Audio Preparation
    print("\n[Step 4/6] Verifying Reference Voice Audio...")
    ref_audio = ROOT_DIR / "storage" / "reference_audio" / "sample_alex.wav"
    if not ref_audio.exists():
        ref_audio = ROOT_DIR / "storage" / "sample_alex.wav"

    if ref_audio.exists():
        ref_data, sr = sf.read(str(ref_audio))
        ref_dur = round(len(ref_data) / sr, 2)
        print(f"  Reference Audio Found: {ref_audio}")
        print(f"  Duration: {ref_dur}s, Sample Rate: {sr} Hz")
    else:
        print(f"  FAIL: Reference audio not found at {ref_audio}")
        sys.exit(1)

    # Step 5 & 6: Neural Inference Generation
    print("\n[Step 5/6] Executing Real Neural Generation Test...")
    input_text = "Hey, how are you?"
    target_out = ROOT_DIR / "storage" / "generated_audio" / "real_chatterbox_v3_test.wav"
    target_out.parent.mkdir(parents=True, exist_ok=True)

    if model_loaded and model is not None:
        try:
            print(f"  Calling model.generate(text='{input_text}', language_id='en', audio_prompt_path='{ref_audio}')...")
            t_infer = time.time()
            wav = model.generate(
                text=input_text,
                language_id="en",
                audio_prompt_path=str(ref_audio)
            )
            latency_ms = int((time.time() - t_infer) * 1000)

            if hasattr(wav, "detach"):
                wav_arr = wav.detach().cpu().float().numpy().squeeze()
            else:
                wav_arr = np.asarray(wav, dtype=np.float32).squeeze()

            out_sr = getattr(model, "sr", 24000)
            sf.write(str(target_out), wav_arr, out_sr, subtype="PCM_16")

            dur = round(len(wav_arr) / out_sr, 2)
            rms = float(np.sqrt(np.mean(wav_arr ** 2)))
            print(f"\n[Step 6/6] Official Neural Generation Verification:")
            print(f"  Output File: {target_out}")
            print(f"  Duration: {dur}s")
            print(f"  Inference Latency: {latency_ms} ms")
            print(f"  RMS Amplitude: {round(rms, 4)}")
            print(f"  Status: REAL NEURAL CHATTERBOX V3 VERIFIED ON {device_name.upper()}")
        except Exception as gen_err:
            print(f"  FAIL: Generation error: {gen_err}")
    else:
        print("  NOTICE: Real neural inference CANNOT be performed on this host.")
        print("  Reason: Official Chatterbox model is not loaded (requires GPU + PyTorch + chatterbox-tts).")
        print("  Status: REAL NEURAL INFERENCE NOT VERIFIED (Running on host without GPU).")

        # In dev mode, test the acoustic engine path to verify fallback pipeline integrity
        from voice_service.app.inference import synthesizer
        fallback_path, fb_dur, fb_lat, fb_eng = synthesizer.synthesize(
            text=input_text,
            reference_audio_path=str(ref_audio),
            language="en"
        )
        print(f"\nFallback Engine Verification (Development Mode):")
        print(f"  Fallback Engine Name: {fb_eng}")
        print(f"  Fallback Path: {fallback_path}")
        print(f"  Duration: {fb_dur}s, Latency: {fb_lat}ms")

    print("\n" + "=" * 70)
    print("AUDIT EXECUTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    run_diagnostics()
