import os
import sys
import time
from pathlib import Path
import soundfile as sf
import numpy as np
import torch

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

ref_audio = ROOT_DIR / "sample_alex.wav"
out_dir = ROOT_DIR / "voice_service" / "models" / "chatterbox_v3"
out_dir.mkdir(parents=True, exist_ok=True)
out_turn1 = out_dir / "benchmark_turn1.wav"
out_turn2 = out_dir / "benchmark_turn2.wav"

print("=" * 70)
print("EX REVIVAL — REAL CHATTERBOX V3 CPU INFERENCE BENCHMARK")
print("=" * 70)

# 1. Imports
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

# 2. Model Load Benchmark
print("\n[Phase 1] Benchmarking Model Load Time (t3_model='v3', device='cpu')...")
t0 = time.time()
model = ChatterboxMultilingualTTS.from_pretrained(device="cpu", t3_model="v3")
model_load_sec = round(time.time() - t0, 2)
print(f"Model Load Time: {model_load_sec}s")
assert model is not None, "Model failed to load"
print(f"Model Class: {model.__class__.__name__}")
print(f"Sample Rate: {model.sr} Hz")

# 3. First Inference Turn
text_turn1 = "Hey, how are you?"
print(f"\n[Phase 2] Benchmarking First Inference Turn...")
print(f"Text: '{text_turn1}'")
print(f"Reference Audio: {ref_audio}")
t_start_1 = time.time()
wav_1 = model.generate(text_turn1, language_id="en", audio_prompt_path=str(ref_audio))
t_infer_1 = round(time.time() - t_start_1, 2)

if isinstance(wav_1, torch.Tensor):
    wav_1_arr = wav_1.detach().cpu().float().numpy().squeeze()
else:
    wav_1_arr = np.asarray(wav_1, dtype=np.float32).squeeze()

sf.write(str(out_turn1), wav_1_arr, model.sr, subtype="PCM_16")
dur_1 = round(len(wav_1_arr) / model.sr, 2)
rms_1 = float(np.sqrt(np.mean(wav_1_arr ** 2)))
rtf_1 = round(t_infer_1 / dur_1, 2) if dur_1 > 0 else 0

print(f"Turn 1 Inference Time: {t_infer_1}s")
print(f"Turn 1 Audio Duration: {dur_1}s")
print(f"Turn 1 RMS Amplitude: {round(rms_1, 4)}")
print(f"Turn 1 Real-Time Factor (RTF): {rtf_1}x")

# 4. Second Inference Turn (Warm / Conditionals cached or re-evaluated)
text_turn2 = "I'm doing well, thank you."
print(f"\n[Phase 3] Benchmarking Second Inference Turn (Warm Cache)...")
print(f"Text: '{text_turn2}'")
t_start_2 = time.time()
wav_2 = model.generate(text_turn2, language_id="en", audio_prompt_path=str(ref_audio))
t_infer_2 = round(time.time() - t_start_2, 2)

if isinstance(wav_2, torch.Tensor):
    wav_2_arr = wav_2.detach().cpu().float().numpy().squeeze()
else:
    wav_2_arr = np.asarray(wav_2, dtype=np.float32).squeeze()

sf.write(str(out_turn2), wav_2_arr, model.sr, subtype="PCM_16")
dur_2 = round(len(wav_2_arr) / model.sr, 2)
rms_2 = float(np.sqrt(np.mean(wav_2_arr ** 2)))
rtf_2 = round(t_infer_2 / dur_2, 2) if dur_2 > 0 else 0

print(f"Turn 2 Inference Time: {t_infer_2}s")
print(f"Turn 2 Audio Duration: {dur_2}s")
print(f"Turn 2 RMS Amplitude: {round(rms_2, 4)}")
print(f"Turn 2 Real-Time Factor (RTF): {rtf_2}x")

# 5. Summary
print("\n" + "=" * 70)
print("BENCHMARK SUMMARY")
print("=" * 70)
print(f"Model Load Time:          {model_load_sec}s")
print(f"First Inference Latency:  {t_infer_1}s (Output: {dur_1}s, RTF: {rtf_1}x)")
print(f"Second Inference Latency: {t_infer_2}s (Output: {dur_2}s, RTF: {rtf_2}x)")
print(f"Turn 1 File:              {out_turn1}")
print(f"Turn 2 File:              {out_turn2}")
print("Status:                   REAL + NEEDS OPTIMIZATION")
print("=" * 70)
