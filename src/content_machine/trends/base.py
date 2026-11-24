from __future__ import annotations

from abc import ABC, abstractmethod

from ..config import Series
from ..models import Trend


class TrendSource(ABC):
    name: str

    @abstractmethod
    def is_configured(self, series: Series) -> bool:
        """True when credentials exist and the series enables this source."""

    @abstractmethod
    def fetch(self, series: Series) -> list[Trend]:
        """Return normalised trends for the series."""
