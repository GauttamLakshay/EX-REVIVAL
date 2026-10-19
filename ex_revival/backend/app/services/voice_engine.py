from abc import ABC, abstractmethod
from typing import Optional


class VoiceEngine(ABC):
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        reference_audio_path: str,
        language: Optional[str] = "en",
        emotion: Optional[str] = "neutral",
        exaggeration: Optional[float] = 0.72,
        cfg_weight: Optional[float] = 0.68,
    ) -> str:
        """
        Synthesizes speech from text conditioned on the reference voice audio.
        Returns the local storage path or URL to the generated audio file.
        """
        pass
