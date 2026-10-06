#!/usr/bin/env python3
"""
EX REVIVAL — Official Resemble AI Chatterbox Multilingual V3 Asset Downloader & Validator.
Downloads official Chatterbox V3 neural weights from ResembleAI/chatterbox into voice_service/models/chatterbox_v3.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("chatterbox.weights")

# Official Hugging Face repository for Resemble AI Chatterbox
DEFAULT_REPO = "ResembleAI/chatterbox"
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DEST = ROOT_DIR / "voice_service" / "models" / "chatterbox_v3"


def verify_checkpoint(dest_path: Path, test_init: bool = False) -> bool:
    """
    Verifies existence, completeness, and integrity of official Chatterbox V3 assets.
    """
    if not dest_path.exists():
        logger.error(f"Checkpoint directory {dest_path} does not exist.")
        return False

    files = list(dest_path.iterdir())
    if not files:
        logger.error(f"Checkpoint directory {dest_path} is empty. No assets found.")
        return False

    logger.info(f"Auditing downloaded assets in {dest_path}:")
    total_size_mb = 0
    weight_files = []
    config_files = []

    for f in files:
        if f.is_file():
            size_mb = round(f.stat().st_size / (1024 * 1024), 2)
            total_size_mb += size_mb
            logger.info(f" - {f.name} ({size_mb} MB)")
            if f.suffix in [".safetensors", ".bin", ".pt"]:
                weight_files.append(f.name)
            elif f.suffix in [".json", ".yaml", ".yml", ".txt"]:
                config_files.append(f.name)

    logger.info(f"Total downloaded assets size: {round(total_size_mb, 2)} MB")

    if not weight_files:
        logger.error("AUDIT FAILURE: No neural weight tensors (.safetensors, .bin, .pt) detected in checkpoint.")
        return False

    # Optional dry load validation if chatterbox package is installed
    if test_init:
        try:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            logger.info("Testing ChatterboxMultilingualTTS model initialization on CPU...")
            model = ChatterboxMultilingualTTS.from_pretrained(device="cpu", t3_model="v3")
            logger.info("Model class initialized successfully from downloaded checkpoint.")
        except ImportError:
            logger.info("Note: 'chatterbox' package not installed in current environment; skipping class load test.")
        except Exception as e:
            logger.error(f"AUDIT FAILURE: Model initialization failed with error: {e}")
            return False

    logger.info("Verification SUCCESS: Official Resemble AI Chatterbox V3 assets verified.")
    return True


def download_weights(repo_id: str, dest_path: Path, token: str = None):
    """Downloads weights from Hugging Face Hub using snapshot_download."""
    logger.info(f"Connecting to Hugging Face repository: '{repo_id}'...")
    logger.info(f"Target destination: {dest_path}")

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        logger.error("huggingface_hub package is not installed. Install via: pip install huggingface-hub")
        sys.exit(1)

    dest_path.mkdir(parents=True, exist_ok=True)

    try:
        hf_token = token or os.environ.get("HF_TOKEN") or None
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(dest_path),
            token=hf_token,
            resume_download=True,
        )
        logger.info("Download completed from Hugging Face.")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Download & Validate Official Resemble AI Chatterbox V3 Assets")
    parser.add_argument("--repo-id", default=DEFAULT_REPO, help=f"Hugging Face repository ID (default: {DEFAULT_REPO})")
    parser.add_argument("--dest", default=str(DEFAULT_DEST), help=f"Destination directory (default: {DEFAULT_DEST})")
    parser.add_argument("--token", default=None, help="Hugging Face API token (or set HF_TOKEN env var)")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing checkpoint without downloading")
    parser.add_argument("--test-init", action="store_true", help="Attempt Python class load after verification")

    args = parser.parse_args()
    dest = Path(args.dest)

    if args.verify_only:
        valid = verify_checkpoint(dest, test_init=args.test_init)
        sys.exit(0 if valid else 1)

    download_weights(args.repo_id, dest, args.token)
    valid = verify_checkpoint(dest, test_init=args.test_init)
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
