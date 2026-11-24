from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class VisualProvider(ABC):
    @abstractmethod
    def fetch(self, query: str, out_dir: Path, index: int) -> Path:
        """Download one clip or image for a scene and return its local path."""
