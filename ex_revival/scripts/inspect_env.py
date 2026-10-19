import sys
import ctypes
from pathlib import Path
import importlib.metadata

print("=== 1 & 2. PYTHON ENVIRONMENT ===")
print("Python Executable:", sys.executable)
print("Python Version:", sys.version)

print("\n=== 3. INSTALLED VERSIONS ===")
try:
    import torch
    print("PyTorch:", torch.__version__)
    print("CUDA Available:", torch.cuda.is_available())
except Exception as e:
    print("PyTorch Error:", e)

try:
    import torchaudio
    print("Torchaudio:", torchaudio.__version__)
except Exception as e:
    print("Torchaudio Error:", e)

try:
    import chatterbox
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    print("chatterbox package imported successfully")
    print("ChatterboxMultilingualTTS imported successfully")
    print("chatterbox-tts dist version:", importlib.metadata.version("chatterbox-tts"))
except Exception as e:
    print("Chatterbox Error:", e)

print("\n=== SYSTEM RAM ===")
class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

stat = MEMORYSTATUSEX()
stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
total_ram = round(stat.ullTotalPhys / (1024**3), 2)
avail_ram = round(stat.ullAvailPhys / (1024**3), 2)
print(f"Total Physical RAM: {total_ram} GB")
print(f"Available Physical RAM: {avail_ram} GB")

print("\n=== 4 & 5. CHATTERBOX_V3 ASSETS ===")
models_dir = Path("D:/Ex rev/ex_revival/voice_service/models/chatterbox_v3")
if models_dir.exists():
    total_size = 0
    for p in sorted(models_dir.iterdir()):
        if p.is_file():
            size_mb = round(p.stat().st_size / (1024**2), 2)
            total_size += size_mb
            print(f" - {p.name}: {size_mb} MB")
    print(f"Total Model Directory Size: {round(total_size, 2)} MB")
else:
    print("Models directory does not exist:", models_dir)
