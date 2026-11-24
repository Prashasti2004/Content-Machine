"""Instagram trends via the official Instagram Graph API (hashtag search).

Requirements: an Instagram Business/Creator account linked to a Facebook Page, a
long-lived access token with `instagram_basic` + `pages_show_list`, and the
account's IG user id. Limit: 30 unique hashtags per 7 days per account.
"""

from __future__ import annotations

import re
from datetime import datetime

import httpx

from ..config import Series, get_env
from ..models import Source, Trend
from .base import TrendSource

GRAPH = "https://graph.facebook.com/v21.0"
FIELDS = "id,caption,media_type,permalink,like_count,comments_count,timestamp"


class InstagramTrends(TrendSource):
    name = "instagram"

    def __init__(
        self,
        access_token: str | None = None,
        user_id: str | None = None,
        client: httpx.Client | None = None,
    ):
        env = get_env()
        self.token = access_token or env.instagram_access_token
        self.user_id = user_id or env.instagram_business_account_id
        self.client = client or httpx.Client(timeout=20)

    def is_configured(self, series: Series) -> bool:
        ig = series.sources.instagram
        return bool(self.token and self.user_id and ig and ig.hashtags)

    def fetch(self, series: Series) -> list[Trend]:
        cfg = series.sources.instagram
        assert cfg is not None
        trends: list[Trend] = []
        for tag in cfg.hashtags:
            hashtag_id = self._hashtag_id(tag.lstrip("#"))
            if not hashtag_id:
                continue
            for edge in ("top_media", "recent_media"):
                r = self.client.get(f"{GRAPH}/{hashtag_id}/{edge}", params={
                    "user_id": self.user_id,
                    "fields": FIELDS,
                    "limit": cfg.limit_per_hashtag,
                    "access_token": self.token,
                })
                r.raise_for_status()
                trends += [self._to_trend(m, tag) for m in r.json().get("data", [])]
        # de-dupe (a post can be in both top and recent)
        return list({t.id: t for t in trends}.values())

    def _hashtag_id(self, tag: str) -> str | None:
        r = self.client.get(f"{GRAPH}/ig_hashtag_search", params={
            "user_id": self.user_id, "q": tag, "access_token": self.token,
        })
        r.raise_for_status()
        data = r.json().get("data", [])
        return data[0]["id"] if data else None

    @staticmethod
    def _to_trend(m: dict, tag: str) -> Trend:
        caption = m.get("caption") or ""
        first_line = caption.strip().split("\n", 1)[0][:120] or f"#{tag} post"
        ts = m.get("timestamp")
        return Trend(
            source=Source.INSTAGRAM,
            id=m["id"],
            title=first_line,
            url=m.get("permalink", ""),
            description=caption[:500],
            views=0,  # Graph API does not expose views for others' media
            likes=int(m.get("like_count") or 0),
            comments=int(m.get("comments_count") or 0),
            published_at=datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z") if ts else None,
            tags=re.findall(r"#(\w+)", caption)[:15],
            raw={"media_type": m.get("media_type"), "hashtag": tag},
        )
