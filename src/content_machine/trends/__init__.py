from .base import TrendSource
from .instagram import InstagramTrends
from .scorer import rank_topics
from .youtube import YouTubeTrends


def default_sources() -> list[TrendSource]:
    return [YouTubeTrends(), InstagramTrends()]


__all__ = ["TrendSource", "YouTubeTrends", "InstagramTrends", "rank_topics", "default_sources"]
