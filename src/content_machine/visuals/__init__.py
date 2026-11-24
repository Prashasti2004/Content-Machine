from .base import VisualProvider


def get_visual_provider(name: str) -> VisualProvider:
    if name == "pexels":
        from .pexels import PexelsProvider

        return PexelsProvider()
    raise ValueError(f"Unknown visual provider: {name!r}")


__all__ = ["VisualProvider", "get_visual_provider"]
