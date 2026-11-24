"""YouTube trends via the official YouTube Data API v3."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx

from ..config import Series, get_env
from ..models import Source, Trend
from .base import TrendSource

API = "https://www.googleapis.com/youtube/v3"


class YouTubeTrends(TrendSource):
    name = "youtube"

    def __init__(self, api_key: str | None = None, client: httpx.Client | None = None):
        self.api_key = api_key or get_env().youtube_api_key
        self.client = client or httpx.Client(timeout=20)

    def is_configured(self, series: Series) -> bool:
        return bool(self.api_key and series.sources.youtube and series.sources.youtube.keywords)

    def fetch(self, series: Series) -> list[Trend]:
        cfg = series.sources.youtube
        assert cfg is not None
        after = datetime.now(UTC) - timedelta(days=cfg.published_within_days)
        per_kw = max(cfg.max_results // max(len(cfg.keywords), 1), 5)

        video_ids: list[str] = []
        for kw in cfg.keywords:
            r = self.client.get(f"{API}/search", params={
                "key": self.api_key,
                "part": "id",
                "q": kw,
                "type": "video",
                "videoDuration": "short",          # < 4 min; Shorts live here
                "order": "viewCount",
                "publishedAfter": after.isoformat().replace("+00:00", "Z"),
                "regionCode": series.region,
                "relevanceLanguage": series.language,
                "maxResults": min(per_kw, 50),
            })
            r.raise_for_status()
            video_ids += [it["id"]["videoId"] for it in r.json().get("items", [])]

        return self._details(list(dict.fromkeys(video_ids)))

    def _details(self, ids: list[str]) -> list[Trend]:
        trends: list[Trend] = []
        for i in range(0, len(ids), 50):  # videos.list accepts up to 50 ids
            r = self.client.get(f"{API}/videos", params={
                "key": self.api_key,
                "part": "snippet,statistics",
                "id": ",".join(ids[i:i + 50]),
            })
            r.raise_for_status()
            for it in r.json().get("items", []):
                sn, st = it["snippet"], it.get("statistics", {})
                trends.append(Trend(
                    source=Source.YOUTUBE,
                    id=it["id"],
                    title=sn["title"],
                    url=f"https://www.youtube.com/shorts/{it['id']}",
                    description=sn.get("description", "")[:500],
                    views=int(st.get("viewCount", 0)),
                    likes=int(st.get("likeCount", 0)),
                    comments=int(st.get("commentCount", 0)),
                    published_at=datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00")),
                    tags=sn.get("tags", [])[:15],
                ))
        return trends
