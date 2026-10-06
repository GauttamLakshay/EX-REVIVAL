#!/usr/bin/env python3
"""
EX REVIVAL — Chatterbox Multilingual V3 Model Weights Downloader & Validator.
Downloads official Chatterbox V3 neural weights into voice_service/models/chatterbox_v3.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("chatterbox.weights")

DEFAULT_REPO = "chatterbox-ai/chatterbox-multilingual-v3"
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DEST = ROOT_DIR / "voice_service" / "models" / "chatterbox_v3"


def verify_checkpoint(dest_path: Path) -> bool:
    """Verifies existence and size of required Chatterbox model files."""
    if not dest_path.exists():
        logger.error(f"Checkpoint directory {dest_path} does not exist.")
        return False

    files = list(dest_path.iterdir())
    if not files:
        logger.error(f"Checkpoint directory {dest_path} is empty.")
        return False

    logger.info(f"Checking checkpoint files in {dest_path}:")
    total_size_mb = 0
    has_weights = False

    for f in files:
        size_mb = round(f.stat().st_size / (1024 * 1024), 2)
        total_size_mb += size_mb
        logger.info(f" - {f.name} ({size_mb} MB)")
        if f.suffix in [".safetensors", ".bin", ".pt"]:
            has_weights = True

    logger.info(f"Total model weights footprint: {round(total_size_mb, 2)} MB")

    if not has_weights:
        logger.warning("No .safetensors, .bin, or .pt weight tensors found in directory.")
        return False

    logger.info("Verification SUCCESS: Chatterbox Multilingual V3 checkpoint is valid.")
    return True


def download_weights(repo_id: str, dest_path: Path, token: str = None):
    """Downloads weights from Hugging Face Hub."""
    logger.info(f"Downloading Chatterbox weights from Hugging Face: '{repo_id}'...")
    logger.info(f"Target destination: {dest_path}")

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        logger.error("huggingface_hub package is not installed.")
        logger.error("Install via: pip install huggingface-hub")
        sys.exit(1)

    dest_path.mkdir(parents=True, exist_ok=True)

    try:
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(dest_path),
            token=token or os.environ.get("HF_TOKEN") or None,
            resume_download=True,
        )
        logger.info("Download completed successfully.")
    except Exception as e:
        logger.error(f"Error during weight download: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Download & Validate Chatterbox V3 Model Weights")
    parser.add_argument("--repo-id", default=DEFAULT_REPO, help=f"Hugging Face repository ID (default: {DEFAULT_REPO})")
    parser.add_argument("--dest", default=str(DEFAULT_DEST), help=f"Destination directory (default: {DEFAULT_DEST})")
    parser.add_argument("--token", default=None, help="Hugging Face API token (or set HF_TOKEN env var)")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing checkpoint without downloading")

    args = parser.parse_args()
    dest = Path(args.dest)

    if args.verify_only:
        valid = verify_checkpoint(dest)
        sys.exit(0 if valid else 1)

    download_weights(args.repo_id, dest, args.token)
    valid = verify_checkpoint(dest)
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
