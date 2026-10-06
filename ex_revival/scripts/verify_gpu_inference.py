#!/usr/bin/env python3
"""
EX REVIVAL — GPU Hardware & Real Chatterbox Neural Inference Diagnostics.
Executes on GPU instances to verify CUDA capability, Tensor Core acceleration,
and zero-shot voice cloning performance.
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
    print("=" * 65)
    print("EX REVIVAL — GPU HARDWARE & CHATTERBOX NEURAL DIAGNOSTICS")
    print("=" * 65)

    # 1. PyTorch & CUDA Check
    print("\n[1/4] Verifying PyTorch and CUDA runtime...")
    torch_installed = False
    cuda_available = False
    try:
        import torch
        torch_installed = True
        print(f"  PyTorch Version: {torch.__version__}")
        cuda_available = torch.cuda.is_available()
    except ImportError:
        print("  Notice: PyTorch is not installed on this host environment.")
        print("  (For GPU instances: pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121)")

    print(f"  CUDA Available: {cuda_available}")

    if not torch_installed or not cuda_available:
        print("  Hardware Mode: CPU / Acoustic Synthesis active.")
        device = "cpu"
    else:
        num_devices = torch.cuda.device_count()
        device = torch.device("cuda:0")
        gpu_name = torch.cuda.get_device_name(device)
        total_vram_gb = round(torch.cuda.get_device_properties(device).total_memory / (1024 ** 3), 2)
        cc = torch.cuda.get_device_capability(device)
        print(f"  GPU Count: {num_devices}")
        print(f"  Primary GPU: {gpu_name}")
        print(f"  Total VRAM: {total_vram_gb} GB")
        print(f"  Compute Capability: {cc[0]}.{cc[1]}")

    # 2. CUDA Tensor Allocation & FP16 Benchmark
    print("\n[2/4] Testing Tensor Allocation & FP16 Acceleration...")
    if cuda_available:
        t0 = time.time()
        x = torch.randn(2048, 2048, device=device, dtype=torch.float16)
        y = torch.matmul(x, x)
        torch.cuda.synchronize()
        dt_ms = round((time.time() - t0) * 1000, 2)
        allocated_mb = round(torch.cuda.memory_allocated(device) / (1024 ** 2), 2)
        print(f"  FP16 GEMM 2048x2048: completed in {dt_ms} ms")
        print(f"  CUDA VRAM in use: {allocated_mb} MB")
        del x, y
        torch.cuda.empty_cache()
    else:
        print("  Skipped CUDA benchmark (running on CPU).")

    # 3. Model Weights Check
    print("\n[3/4] Inspecting Chatterbox Multilingual V3 Weights...")
    checkpoint_dir = ROOT_DIR / "voice_service" / "models" / "chatterbox_v3"
    print(f"  Target Checkpoint Path: {checkpoint_dir}")
    if checkpoint_dir.exists() and any(checkpoint_dir.iterdir()):
        files = list(checkpoint_dir.iterdir())
        print(f"  Found {len(files)} files in checkpoint directory:")
        for f in files[:5]:
            sz_mb = round(f.stat().st_size / (1024 * 1024), 2)
            print(f"   - {f.name} ({sz_mb} MB)")
        if len(files) > 5:
            print(f"   - ... and {len(files) - 5} more files")
    else:
        print("  Notice: No local weights in checkpoint directory.")
        print("  To download: python scripts/download_chatterbox_weights.py")

    # 4. Synthesizer Inference Run
    print("\n[4/4] Executing Voice Clone Synthesis Test...")
    from voice_service.app.inference import synthesizer

    # Locate reference sample
    ref_audio = ROOT_DIR / "storage" / "reference_audio" / "sample_alex.wav"
    if not ref_audio.exists():
        ref_audio = ROOT_DIR / "storage" / "sample_alex.wav"

    if not ref_audio.exists():
        print(f"  Creating synthetic reference tone at {ref_audio}...")
        ref_audio.parent.mkdir(parents=True, exist_ok=True)
        sr = 24000
        t = np.linspace(0, 3.0, sr * 3, endpoint=False)
        tone = (np.sin(2 * np.pi * 180 * t) * 0.6).astype(np.float32)
        sf.write(str(ref_audio), tone, sr)

    test_text = "Hello! This is a real-time verification of EX REVIVAL running on the Chatterbox voice engine."
    print(f"  Input text: \"{test_text}\"")
    print(f"  Reference audio: {ref_audio}")

    t_start = time.time()
    out_path, duration, latency_ms = synthesizer.synthesize(
        text=test_text,
        reference_audio_path=str(ref_audio),
        language="en",
        emotion="warm"
    )
    total_time_ms = int((time.time() - t_start) * 1000)

    # Inspect generated file
    out_file = Path(out_path)
    if out_file.exists():
        audio_data, sr = sf.read(str(out_file))
        actual_dur = round(len(audio_data) / sr, 2)
        rms = float(np.sqrt(np.mean(audio_data ** 2)))
        rtf = round(latency_ms / (actual_dur * 1000), 2) if actual_dur > 0 else 0

        print(f"\nSynthesis Diagnostic Results:")
        print(f"  Status: SUCCESS")
        print(f"  Engine Active: {'Chatterbox Neural GPU' if synthesizer.is_loaded else 'Chatterbox Acoustic Fallback'}")
        print(f"  Output File: {out_file.name}")
        print(f"  Audio Duration: {actual_dur} seconds")
        print(f"  Inference Latency: {latency_ms} ms (Total: {total_time_ms} ms)")
        print(f"  Real-Time Factor (RTF): {rtf}x {'(< 1.0 = faster than real-time)' if rtf < 1.0 else ''}")
        print(f"  RMS Amplitude: {round(rms, 4)} ({'Non-silent' if rms > 0.001 else 'SILENT'})")
    else:
        print(f"  FAIL: Generated audio file not found at {out_path}")
        sys.exit(1)

    print("\n" + "=" * 65)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 65)


if __name__ == "__main__":
    run_diagnostics()
