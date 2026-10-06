import os
import uuid
from pathlib import Path
from typing import Optional
from app.config import get_settings

settings = get_settings()


class StorageService:
    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER
        self.local_base_path = settings.get_storage_path()
        self.ref_audio_dir = self.local_base_path / "reference_audio"
        self.gen_audio_dir = self.local_base_path / "generated_audio"
        self.temp_dir = self.local_base_path / "temp"

        # Ensure storage subdirectories exist
        self.ref_audio_dir.mkdir(parents=True, exist_ok=True)
        self.gen_audio_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def save_reference_audio(self, file_bytes: bytes, filename_ext: str = ".wav") -> str:
        """Save reference audio securely and return local relative or absolute path."""
        file_id = f"ref_{uuid.uuid4().hex}{filename_ext}"
        destination = self.ref_audio_dir / file_id
        with open(destination, "wb") as f:
            f.write(file_bytes)
        return str(destination)

    async def save_generated_audio(self, file_bytes: bytes, filename_ext: str = ".wav") -> str:
        """Save AI synthesized audio and return storage path."""
        file_id = f"gen_{uuid.uuid4().hex}{filename_ext}"
        destination = self.gen_audio_dir / file_id
        with open(destination, "wb") as f:
            f.write(file_bytes)
        return str(destination)

    def get_audio_url(self, storage_path: Optional[str]) -> Optional[str]:
        """Convert storage path to an accessible HTTP URL."""
        if not storage_path:
            return None
        # In development with local storage, we mount /storage as static files
        p = Path(storage_path).resolve()
        try:
            rel = p.relative_to(self.local_base_path)
            # Normalize path slashes for URL
            rel_str = str(rel).replace("\\", "/")
            return f"/storage/{rel_str}"
        except ValueError:
            return f"/storage/{p.name}"

    async def delete_file(self, storage_path: Optional[str]) -> bool:
        """Safely delete file if exists."""
        if not storage_path:
            return False
        try:
            p = Path(storage_path)
            if p.exists() and p.is_file():
                p.unlink()
                return True
        except Exception:
            pass
        return False


storage_service = StorageService()
