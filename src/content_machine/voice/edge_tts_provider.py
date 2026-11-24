from __future__ import annotations

import asyncio
from pathlib import Path

from .base import VoiceProvider


class EdgeTTSProvider(VoiceProvider):
    """Free Microsoft Edge neural voices via the `edge-tts` package."""

    def synthesize(self, text: str, out_path: Path, voice_id: str) -> Path:
        import edge_tts  # lazy: optional [media] dependency

        async def _run() -> None:
            await edge_tts.Communicate(text, voice_id).save(str(out_path))

        asyncio.run(_run())
        return out_path
