"""Portrait stock footage (falls back to photos) from the Pexels API."""

from __future__ import annotations

from pathlib import Path

import httpx

from ..config import get_env
from .base import VisualProvider

API = "https://api.pexels.com"


class PexelsProvider(VisualProvider):
    def __init__(self, api_key: str | None = None, client: httpx.Client | None = None):
        key = api_key or get_env().pexels_api_key
        if not key:
            raise RuntimeError("PEXELS_API_KEY is not set")
        self.client = client or httpx.Client(timeout=60, headers={"Authorization": key})

    def fetch(self, query: str, out_dir: Path, index: int) -> Path:
        return self._video(query, out_dir, index) or self._photo(query, out_dir, index)

    def _video(self, query: str, out_dir: Path, index: int) -> Path | None:
        r = self.client.get(f"{API}/videos/search",
                            params={"query": query, "orientation": "portrait", "per_page": 5})
        r.raise_for_status()
        for video in r.json().get("videos", []):
            files = [f for f in video.get("video_files", [])
                     if f.get("file_type") == "video/mp4" and (f.get("height") or 0) >= 1280]
            if files:
                best = min(files, key=lambda f: abs((f.get("height") or 0) - 1920))
                return self._download(best["link"], out_dir / f"scene_{index:02d}.mp4")
        return None

    def _photo(self, query: str, out_dir: Path, index: int) -> Path:
        r = self.client.get(f"{API}/v1/search",
                            params={"query": query, "orientation": "portrait", "per_page": 1})
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if not photos:
            raise LookupError(f"No Pexels media for {query!r}")
        return self._download(photos[0]["src"]["large2x"], out_dir / f"scene_{index:02d}.jpg")

    def _download(self, url: str, path: Path) -> Path:
        with self.client.stream("GET", url, follow_redirects=True) as r:
            r.raise_for_status()
            with path.open("wb") as fh:
                for chunk in r.iter_bytes():
                    fh.write(chunk)
        return path
