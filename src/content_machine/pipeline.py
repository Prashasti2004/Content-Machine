"""Orchestrates trend discovery -> script -> voice -> captions -> visuals -> render."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from .config import Series, Settings, get_env
from .models import RunManifest, Script, StageRecord, StageStatus, Topic, Trend
from .storage import Storage
from .trends import TrendSource, default_sources, rank_topics

console = Console()


class Pipeline:
    def __init__(
        self,
        settings: Settings,
        storage: Storage | None = None,
        sources: list[TrendSource] | None = None,
    ):
        self.settings = settings
        self.storage = storage or Storage(get_env().cm_output_dir)
        self.sources = sources if sources is not None else default_sources()

    # ---------- stage 1-2 ----------
    def discover(self, series: Series) -> tuple[list[Trend], list[Topic]]:
        trends: list[Trend] = []
        for src in self.sources:
            if not src.is_configured(series):
                console.print(f"[yellow]skip[/] {src.name}: not configured")
                continue
            try:
                found = src.fetch(series)
                console.print(f"[green]{src.name}[/]: {len(found)} trends")
                trends += found
            except Exception as exc:  # one failing source shouldn't kill the run
                console.print(f"[red]{src.name} failed:[/] {exc}")
        topics = rank_topics(trends, series, self.settings.scoring,
                             self.storage.used_titles(series.id))
        return trends, topics

    # ---------- stage 3 ----------
    def write_script(self, series: Series, topic: Topic) -> Script:
        from .script import ScriptGenerator

        return ScriptGenerator(self.settings.llm).generate(series, topic)

    # ---------- full run ----------
    def run(self, series: Series, topic_title: str | None = None, dry_run: bool = False) -> Path:
        trends: list[Trend] = []
        if topic_title:
            topic = Topic(title=topic_title)
        else:
            trends, topics = self.discover(series)
            if not topics:
                raise RuntimeError("No topics found. Check API keys and series sources.")
            topic = topics[0]

        run_dir = self.storage.new_run_dir(series.id, topic.title)
        manifest = RunManifest(run_id=run_dir.name, series_id=series.id, topic=topic)
        self.storage.write_json(run_dir / "trends.json", trends)
        console.print(f"[bold]Run[/] {run_dir}")

        @contextmanager
        def stage(name: str):
            rec = StageRecord(name=name, started_at=datetime.now(UTC))
            manifest.stages.append(rec)
            try:
                yield rec
                rec.status = StageStatus.DONE
            except Exception as exc:
                rec.status, rec.error = StageStatus.FAILED, repr(exc)
                raise
            finally:
                rec.finished_at = datetime.now(UTC)
                self.storage.save_manifest(run_dir, manifest)

        with stage("script") as rec:
            script = self.write_script(series, topic)
            rec.output = str(self.storage.write_json(run_dir / "script.json", script))
            self.storage.write_json(run_dir / "metadata.json", {
                "title": script.title,
                "description": script.description,
                "hashtags": script.hashtags,
            })

        if dry_run:
            console.print("[cyan]dry run[/]: stopping after script")
            return run_dir

        self._produce(series, script, run_dir, stage)
        self.storage.mark_used(series.id, topic.title)
        return run_dir

    # ---------- stage 4-7 ----------
    def _produce(self, series: Series, script: Script, run_dir: Path, stage: Callable) -> None:
        from .captions import chunk_words, transcribe_words
        from .video import render_video
        from .visuals import get_visual_provider
        from .voice import get_voice_provider

        with stage("voice") as rec:
            voice_path = get_voice_provider(series.voice.provider).synthesize(
                script.narration, run_dir / "voice.mp3", series.voice.voice_id)
            rec.output = str(voice_path)

        with stage("captions") as rec:
            words = transcribe_words(voice_path, language=series.language)
            captions = chunk_words(words, self.settings.render.caption_words_per_chunk)
            rec.output = str(self.storage.write_json(run_dir / "captions.json", captions))

        with stage("visuals") as rec:
            provider = get_visual_provider(series.visuals.provider)
            style = f" {series.visuals.style}" if series.visuals.style else ""
            assets = [provider.fetch(f"{s.visual_query}{style}".strip(), run_dir / "assets", i)
                      for i, s in enumerate(script.scenes, start=1)]
            rec.output = str(run_dir / "assets")

        with stage("render") as rec:
            out = render_video(script, voice_path, assets, captions, run_dir / "final.mp4",
                               self.settings.render, series.music)
            rec.output = str(out)
