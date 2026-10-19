import sys
import time
import traceback
from pathlib import Path

print("Step 1: Importing libraries...")
import torch
print("PyTorch:", torch.__version__, "CUDA available:", torch.cuda.is_available())

try:
    import chatterbox
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    print("Chatterbox Multilingual TTS imported successfully.")
except Exception as e:
    print("Import failed:", e)
    traceback.print_exc()
    sys.exit(1)

print("\nStep 2: Attempting model loading with:")
print('ChatterboxMultilingualTTS.from_pretrained(device="cpu", t3_model="v3")')

start_time = time.time()
try:
    model = ChatterboxMultilingualTTS.from_pretrained(device="cpu", t3_model="v3")
    load_time = round(time.time() - start_time, 2)
    print(f"\nMODEL LOAD SUCCESS in {load_time}s!")
    print("Model instance:", type(model))
except Exception as e:
    load_time = round(time.time() - start_time, 2)
    print(f"\nMODEL LOAD FAILED in {load_time}s!")
    print(f"Exception Type: {type(e).__name__}")
    print(f"Exception Message: {e}")
    traceback.print_exc()
