# EX REVIVAL — GPU Deployment & Real Chatterbox Inference Guide

This guide describes how to deploy **EX REVIVAL** to a production GPU environment (AWS EC2 G4dn/G5, RunPod, Lambda Labs, GCP, or on-premise NVIDIA servers) and run real **Chatterbox Multilingual V3** neural voice cloning.

---

## 1. Hardware & System Prerequisites

* **GPU:** NVIDIA GPU with $\ge 8\text{ GB}$ VRAM (e.g. RTX 3090/4090, Tesla T4, A10G, L4, A100).
* **NVIDIA Driver:** Version $\ge 525.60.13$ (supports CUDA 12.1+).
* **OS:** Ubuntu 22.04 LTS (recommended) or Windows 11 with WSL2 / Native CUDA.
* **Storage:** $\ge 25\text{ GB}$ SSD space for Docker images, model weights, and audio caches.
* **Container Runtime:** Docker Engine $\ge 24.0$ with **NVIDIA Container Toolkit** (`nvidia-container-toolkit`).

---

## 2. NVIDIA Container Toolkit Setup (Linux Host)

Ensure Docker can communicate with NVIDIA GPUs:

```bash
# 1. Configure the production repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# 2. Install NVIDIA Container Toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# 3. Configure Docker daemon and restart
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 4. Verify GPU pass-through
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

---

## 3. Chatterbox Multilingual V3 Model Weights

Weights reside in `voice_service/models/chatterbox_v3/`.

### Option A: Automatic Download via Script
Run the included downloader script:
```bash
python scripts/download_chatterbox_weights.py --repo-id chatterbox-ai/chatterbox-multilingual-v3
```
*If accessing gated checkpoints, supply your token: `--token <HF_TOKEN>` or set `export HF_TOKEN=...`.*

### Option B: Manual Placement
Copy your pre-trained weights into the directory:
```text
voice_service/models/chatterbox_v3/
├── config.json
├── model.safetensors (or pytorch_model.bin)
├── vocab.json
└── tokenizer.json
```

Verify the files:
```bash
python scripts/download_chatterbox_weights.py --verify-only
```

---

## 4. Production Stack Deployment (Docker Compose)

Deploy the database (PostgreSQL), GPU Voice Service (CUDA 12.1), and FastAPI Orchestrator:

```bash
# Build and start all services in detached mode
docker compose -f docker-compose.gpu.yml up --build -d
```

### Inspect Container Status:
```bash
docker compose -f docker-compose.gpu.yml ps
```

### Inspect Live GPU Container Logs:
```bash
docker logs -f ex_revival_voice_gpu
```
Expected startup confirmation:
```text
[Chatterbox GPU] CUDA hardware detected: NVIDIA A10G (Compute Capability: 8.6)
[Chatterbox] Found neural model weights at /app/voice_service/models/chatterbox_v3.
[Chatterbox] Neural weights loaded onto cuda:0.
[Chatterbox] Warming up GPU inference pipeline...
[Chatterbox] Warmup finished in 320ms. CUDA VRAM active: 2840.4MB.
[Voice Service] Initialized with engine: chatterbox_v3_neural on cuda:0
```

---

## 5. Verification & Telemetry

### Check Service Health & GPU Metrics:
```bash
curl http://localhost:8001/health
```
Example Response:
```json
{
  "status": "ok",
  "service": "chatterbox_voice_service",
  "device": "cuda",
  "cuda_available": true,
  "gpu_name": "NVIDIA A10G",
  "is_model_loaded": true,
  "engine": "chatterbox_v3_neural",
  "sample_rate": 24000,
  "vram_total_mb": 22528.0,
  "vram_allocated_mb": 3120.5,
  "vram_reserved_mb": 4096.0
}
```

### Run End-to-End GPU Diagnostic Script:
```bash
python scripts/verify_gpu_inference.py
```
This tests:
1. PyTorch CUDA tensor allocation & FP16 matrix operations.
2. Model weight checkpoint integrity.
3. Neural voice clone synthesis from reference sample on GPU.
4. Latency and Real-Time Factor (RTF).

---

## 6. Architecture & Memory Management

* **Half-Precision (FP16):** Configured by default (`USE_FP16=true`) to leverage NVIDIA Tensor Cores and halve VRAM usage.
* **Warmup on Startup:** `WARMUP_ON_STARTUP=true` performs a 1-turn compilation pass during service boot, eliminating first-request latency spikes.
* **Shared IPC:** `ipc: host` is enabled in `docker-compose.gpu.yml` to prevent PyTorch shared memory bus crashes during audio batching.
* **Single Worker Execution:** `workers: 1` is configured to prevent CUDA out-of-memory errors from redundant model duplication across multiple worker processes.
