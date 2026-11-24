"""Write a Shorts/Reels script for a topic with Claude (structured JSON output)."""

from __future__ import annotations

import json
from pathlib import Path

import anthropic

from ..config import LLMSettings, Series
from ..models import Script, Topic

PROMPT_PATH = Path(__file__).parent / "prompts" / "short_script.md"
WORDS_PER_SECOND = 2.5  # typical energetic narration pace

SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "hook": {"type": "string"},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "narration": {"type": "string"},
                    "on_screen_text": {"type": "string"},
                    "visual_query": {"type": "string"},
                },
                "required": ["narration", "on_screen_text", "visual_query"],
                "additionalProperties": False,
            },
        },
        "cta": {"type": "string"},
        "description": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "hook", "scenes", "cta", "description", "hashtags"],
    "additionalProperties": False,
}


class ScriptRefusedError(RuntimeError):
    pass


def build_prompt(series: Series, topic: Topic, max_trends: int = 8) -> str:
    trend_lines = [
        f"- [{t.source.value}] {t.title} ({t.views:,} views, {t.likes:,} likes)"
        for t in topic.supporting_trends[:max_trends]
    ] or ["- (no supporting trends — topic supplied manually)"]
    return PROMPT_PATH.read_text(encoding="utf-8").format(
        series_name=series.name,
        audience=series.audience or "general short-form audience",
        tone=series.tone or "engaging",
        language=series.language,
        duration_seconds=series.duration_seconds,
        word_budget=int(series.duration_seconds * WORDS_PER_SECOND),
        hook_style=series.script.hook_style,
        cta=series.script.cta,
        banned_topics=", ".join(series.script.banned_topics) or "nothing specific",
        topic_title=topic.title,
        trend_context="\n".join(trend_lines),
    )


class ScriptGenerator:
    def __init__(self, settings: LLMSettings, client: anthropic.Anthropic | None = None):
        self.settings = settings
        self.client = client or anthropic.Anthropic()

    def generate(self, series: Series, topic: Topic) -> Script:
        response = self.client.beta.messages.create(
            model=self.settings.model,
            max_tokens=self.settings.max_tokens,
            # Re-run on a fallback model if a safety classifier declines the request.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={
                "effort": self.settings.effort,
                "format": {"type": "json_schema", "schema": SCRIPT_SCHEMA},
            },
            messages=[{"role": "user", "content": build_prompt(series, topic)}],
        )
        if response.stop_reason == "refusal":
            raise ScriptRefusedError(f"Model declined topic {topic.title!r}")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("Script generation hit max_tokens; raise llm.max_tokens")

        text = next(b.text for b in response.content if b.type == "text")
        return Script.model_validate(json.loads(text))
