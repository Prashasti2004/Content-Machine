"""Data models shared across pipeline stages."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Source(StrEnum):
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"


class Trend(BaseModel):
    """One piece of trending content pulled from a platform."""

    source: Source
    id: str
    title: str
    url: str
    description: str = ""
    views: int = 0
    likes: int = 0
    comments: int = 0
    published_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict, repr=False)

    @property
    def hours_since_publish(self) -> float:
        if self.published_at is None:
            return 72.0
        delta = datetime.now(UTC) - self.published_at
        return max(delta.total_seconds() / 3600, 1.0)


class Topic(BaseModel):
    """A candidate video idea derived from one or more trends."""

    title: str
    angle: str = ""
    score: float = 0.0
    supporting_trends: list[Trend] = Field(default_factory=list)


class Scene(BaseModel):
    narration: str
    on_screen_text: str = ""
    visual_query: str
    duration_hint: float | None = None


class Script(BaseModel):
    title: str
    hook: str
    scenes: list[Scene]
    cta: str
    description: str
    hashtags: list[str]

    @property
    def narration(self) -> str:
        parts = [self.hook, *(s.narration for s in self.scenes), self.cta]
        return " ".join(p.strip() for p in parts if p.strip())


class StageStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class StageRecord(BaseModel):
    name: str
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    output: str | None = None
    error: str | None = None


class RunManifest(BaseModel):
    run_id: str
    series_id: str
    topic: Topic | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stages: list[StageRecord] = Field(default_factory=list)
