"""Environment settings, global settings.yaml and per-series YAML."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------- secrets / env ----------


class Env(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str | None = None
    youtube_api_key: str | None = None
    instagram_access_token: str | None = None
    instagram_business_account_id: str | None = None
    pexels_api_key: str | None = None
    elevenlabs_api_key: str | None = None

    cm_config_dir: Path = Path("config")
    cm_output_dir: Path = Path("output")


@lru_cache
def get_env() -> Env:
    return Env()


# ---------- global settings.yaml ----------


class LLMSettings(BaseModel):
    model: str = "claude-opus-5-5"
    effort: str = "high"
    max_tokens: int = 16000


class ScoringWeights(BaseModel):
    velocity: float = 0.45
    engagement: float = 0.25
    freshness: float = 0.15
    relevance: float = 0.15


class ScoringSettings(BaseModel):
    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    freshness_half_life_hours: float = 72
    top_k_topics: int = 10


class RenderSettings(BaseModel):
    width: int = 1080
    height: int = 1920
    fps: int = 30
    font: str = "assets/fonts/Montserrat-Bold.ttf"
    caption_font_size: int = 80
    caption_words_per_chunk: int = 2


class Settings(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    scoring: ScoringSettings = Field(default_factory=ScoringSettings)
    render: RenderSettings = Field(default_factory=RenderSettings)


def load_settings(config_dir: Path | None = None) -> Settings:
    path = (config_dir or get_env().cm_config_dir) / "settings.yaml"
    data: dict[str, Any] = yaml.safe_load(path.read_text()) if path.exists() else {}
    return Settings.model_validate(data or {})


# ---------- series ----------


class YouTubeSource(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    max_results: int = 25
    published_within_days: int = 7


class InstagramSource(BaseModel):
    hashtags: list[str] = Field(default_factory=list)
    limit_per_hashtag: int = 25


class Sources(BaseModel):
    youtube: YouTubeSource | None = None
    instagram: InstagramSource | None = None


class ScriptStyle(BaseModel):
    hook_style: str = "a question or surprising fact in the first 2 seconds"
    cta: str = "Follow for more"
    banned_topics: list[str] = Field(default_factory=list)


class VoiceConfig(BaseModel):
    provider: str = "edge"
    voice_id: str = "en-US-GuyNeural"


class VisualsConfig(BaseModel):
    provider: str = "pexels"
    style: str = ""


class MusicConfig(BaseModel):
    track: str | None = None
    volume: float = 0.12


class Series(BaseModel):
    id: str
    name: str
    language: str = "en"
    region: str = "US"
    audience: str = ""
    tone: str = ""
    duration_seconds: int = 45
    sources: Sources = Field(default_factory=Sources)
    script: ScriptStyle = Field(default_factory=ScriptStyle)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    visuals: VisualsConfig = Field(default_factory=VisualsConfig)
    music: MusicConfig = Field(default_factory=MusicConfig)

    @property
    def keywords(self) -> list[str]:
        kws: list[str] = []
        if self.sources.youtube:
            kws += self.sources.youtube.keywords
        if self.sources.instagram:
            kws += self.sources.instagram.hashtags
        return kws


def series_dir(config_dir: Path | None = None) -> Path:
    return (config_dir or get_env().cm_config_dir) / "series"


def list_series(config_dir: Path | None = None) -> list[Series]:
    return [Series.model_validate(yaml.safe_load(p.read_text()))
            for p in sorted(series_dir(config_dir).glob("*.y*ml"))]


def load_series(series_id: str, config_dir: Path | None = None) -> Series:
    for s in list_series(config_dir):
        if s.id == series_id:
            return s
    raise KeyError(f"Series '{series_id}' not found in {series_dir(config_dir)}")
