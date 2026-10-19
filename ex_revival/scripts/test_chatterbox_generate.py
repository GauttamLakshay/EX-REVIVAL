import os
import sys
import time
import traceback
from pathlib import Path
import soundfile as sf
import numpy as np
import torch

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

ref_audio = ROOT_DIR / "sample_alex.wav"
output_path = ROOT_DIR / "voice_service" / "models" / "chatterbox_v3" / "cpu_test.wav"
output_path.parent.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("EX REVIVAL — REAL CHATTERBOX MULTILINGUAL V3 CPU GENERATION TEST")
print("=" * 60)

print(f"\nPyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Reference voice audio: {ref_audio} (Exists: {ref_audio.exists()})")
print(f"Target output file: {output_path}")

print("\n[Step 1] Loading official ChatterboxMultilingualTTS on CPU with t3_model='v3'...")
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

t_load_start = time.time()
try:
    model = ChatterboxMultilingualTTS.from_pretrained(
        device="cpu",
        t3_model="v3"
    )
    load_time = round(time.time() - t_load_start, 2)
    print(f"MODEL LOAD: SUCCESS (took {load_time}s)")
except Exception as e:
    load_time = round(time.time() - t_load_start, 2)
    print(f"MODEL LOAD: FAILED (after {load_time}s)")
    print(f"Error: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n[Step 2] Executing model.generate()...")
input_text = "Hey, how are you?"
t_gen_start = time.time()
try:
    wav = model.generate(
        input_text,
        language_id="en",
        audio_prompt_path=str(ref_audio)
    )
    gen_time_sec = round(time.time() - t_gen_start, 2)
    gen_time_ms = int(gen_time_sec * 1000)
    print(f"model.generate() finished in {gen_time_sec}s ({gen_time_ms}ms)!")

    # Convert tensor to numpy array
    if isinstance(wav, torch.Tensor):
        wav_arr = wav.detach().cpu().float().numpy().squeeze()
    else:
        wav_arr = np.asarray(wav, dtype=np.float32).squeeze()

    sr = getattr(model, "sr", 24000)
    sf.write(str(output_path), wav_arr, sr, subtype="PCM_16")

    # Metrics
    file_size_bytes = output_path.stat().st_size
    duration_sec = round(len(wav_arr) / sr, 2)
    rms = float(np.sqrt(np.mean(wav_arr ** 2)))
    peak = float(np.max(np.abs(wav_arr)))

    print("\n[Step 3] Output Audio Verification:")
    print(f"  File exists: {output_path.exists()}")
    print(f"  File size: {file_size_bytes} bytes ({round(file_size_bytes / 1024, 2)} KB)")
    print(f"  Duration: {duration_sec}s")
    print(f"  Sample rate: {sr} Hz")
    print(f"  Peak amplitude: {round(peak, 4)}")
    print(f"  RMS amplitude: {round(rms, 4)} ({'NON-SILENT' if rms > 0.001 else 'SILENT!'})")
    print(f"  Actual inference time: {gen_time_sec}s")

    print("\n" + "=" * 60)
    print("FINAL SUMMARY:")
    print("MODEL LOAD: SUCCESS")
    print("NEURAL INFERENCE: SUCCESS")
    print("DEVICE: CPU")
    print("MODEL: Chatterbox Multilingual V3")
    print(f"INFERENCE TIME: {gen_time_sec}s")
    print(f"OUTPUT FILE: {output_path}")
    print(f"OUTPUT DURATION: {duration_sec}s")
    print("ERROR: None")
    print("=" * 60)

except Exception as e:
    gen_time_sec = round(time.time() - t_gen_start, 2)
    print(f"NEURAL INFERENCE: FAILED (after {gen_time_sec}s)")
    print(f"Error: {e}")
    traceback.print_exc()
    print("\n" + "=" * 60)
    print("FINAL SUMMARY:")
    print("MODEL LOAD: SUCCESS")
    print("NEURAL INFERENCE: FAILED")
    print("DEVICE: CPU")
    print("MODEL: Chatterbox Multilingual V3")
    print(f"INFERENCE TIME: {gen_time_sec}s")
    print("OUTPUT FILE: None")
    print("OUTPUT DURATION: 0s")
    print(f"ERROR: {type(e).__name__}: {e}")
    print("=" * 60)
    sys.exit(1)
