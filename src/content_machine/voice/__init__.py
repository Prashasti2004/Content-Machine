from .base import VoiceProvider


def get_voice_provider(name: str) -> VoiceProvider:
    if name == "edge":
        from .edge_tts_provider import EdgeTTSProvider

        return EdgeTTSProvider()
    raise ValueError(f"Unknown voice provider: {name!r}")


__all__ = ["VoiceProvider", "get_voice_provider"]
