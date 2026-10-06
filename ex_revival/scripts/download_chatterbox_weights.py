#!/usr/bin/env python3
"""
EX REVIVAL — Official Resemble AI Chatterbox Multilingual V3 Asset Downloader & Validator.
Downloads official Chatterbox V3 neural weights from ResembleAI/chatterbox into voice_service/models/chatterbox_v3.
Validates presence and file sizes of required assets including t3_mtl23ls_v3.safetensors.
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

# Mandatory assets for Chatterbox Multilingual V3
REQUIRED_ASSETS = [
    "t3_mtl23ls_v3.safetensors",  # Core V3 T3 backbone checkpoint (~2.14 GB)
]

OPTIONAL_CORE_ASSETS = [
    "s3gen_v3.safetensors",
    "s3gen_v3.pt",
    "ve.pt",
    "mtl_tokenizer.json",
    "tokenizer.json",
]


def verify_checkpoint(dest_path: Path, test_init: bool = True) -> bool:
    """
    Verifies existence, completeness, and integrity of official Chatterbox V3 assets.
    Exits with error if critical assets are missing or undersized.
    """
    if not dest_path.exists():
        logger.error(f"FAIL: Checkpoint directory {dest_path} does not exist.")
        return False

    files = {f.name: f for f in dest_path.iterdir() if f.is_file()}
    if not files:
        logger.error(f"FAIL: Checkpoint directory {dest_path} is empty. No assets found.")
        return False

    logger.info(f"Auditing downloaded assets in {dest_path}:")
    total_size_mb = 0

    for name, f in files.items():
        size_mb = round(f.stat().st_size / (1024 * 1024), 2)
        total_size_mb += size_mb
        logger.info(f" - {name} ({size_mb} MB)")

    logger.info(f"Total downloaded assets size: {round(total_size_mb, 2)} MB")

    # 1. Verify mandatory V3 checkpoint t3_mtl23ls_v3.safetensors
    if "t3_mtl23ls_v3.safetensors" not in files:
        logger.error(
            "FAIL: Critical V3 model asset 't3_mtl23ls_v3.safetensors' is MISSING. "
            "ChatterboxMultilingualTTS(t3_model='v3') will fail to load."
        )
        return False

    v3_size_mb = files["t3_mtl23ls_v3.safetensors"].stat().st_size / (1024 * 1024)
    if v3_size_mb < 1500.0:  # Must be ~2.14 GB
        logger.error(
            f"FAIL: 't3_mtl23ls_v3.safetensors' is incomplete or corrupted "
            f"({round(v3_size_mb, 2)} MB, expected ~2140 MB)."
        )
        return False

    logger.info("SUCCESS: 't3_mtl23ls_v3.safetensors' checkpoint verified (valid size).")

    # 2. Test class initialization if requested and package is available
    if test_init:
        try:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            logger.info("Testing ChatterboxMultilingualTTS model initialization on CPU...")
            model = ChatterboxMultilingualTTS.from_pretrained(device="cpu", t3_model="v3")
            if model is None:
                logger.error("FAIL: ChatterboxMultilingualTTS returned None.")
                return False
            logger.info("SUCCESS: Official ChatterboxMultilingualTTS class initialized from checkpoint.")
        except ImportError as ie:
            logger.warning(f"Note: chatterbox-tts package not installed in current environment ({ie}). Skipping class initialization.")
        except Exception as e:
            logger.error(f"FAIL: ChatterboxMultilingualTTS initialization test failed: {e}")
            return False

    logger.info("Verification SUCCESS: Official Chatterbox V3 assets verified.")
    return True


def download_weights(repo_id: str, dest_path: Path, token: str = None):
    """Downloads weights from Hugging Face Hub with authentication error handling."""
    logger.info(f"Connecting to Hugging Face repository: '{repo_id}'...")
    logger.info(f"Target destination: {dest_path}")

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        logger.error("huggingface_hub package is not installed. Install via: pip install huggingface-hub")
        sys.exit(1)

    dest_path.mkdir(parents=True, exist_ok=True)
    hf_token = token or os.environ.get("HF_TOKEN") or None

    try:
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(dest_path),
            token=hf_token,
            resume_download=True,
        )
        logger.info("Download completed from Hugging Face.")
    except Exception as e:
        logger.error(f"FAIL: Download failed: {e}")
        if "401" in str(e) or "403" in str(e):
            logger.error("Hugging Face authentication failed. Provide a valid HF_TOKEN.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Download & Validate Official Resemble AI Chatterbox V3 Assets")
    parser.add_argument("--repo-id", default=DEFAULT_REPO, help=f"Hugging Face repository ID (default: {DEFAULT_REPO})")
    parser.add_argument("--dest", default=str(DEFAULT_DEST), help=f"Destination directory (default: {DEFAULT_DEST})")
    parser.add_argument("--token", default=None, help="Hugging Face API token (or set HF_TOKEN env var)")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing checkpoint without downloading")
    parser.add_argument("--skip-init-test", action="store_true", help="Skip Python class initialization test")

    args = parser.parse_args()
    dest = Path(args.dest)

    if args.verify_only:
        valid = verify_checkpoint(dest, test_init=not args.skip_init_test)
        sys.exit(0 if valid else 1)

    download_weights(args.repo_id, dest, args.token)
    valid = verify_checkpoint(dest, test_init=not args.skip_init_test)
    if not valid:
        logger.error("FAIL: Downloaded checkpoint failed verification.")
        sys.exit(1)


if __name__ == "__main__":
    main()
