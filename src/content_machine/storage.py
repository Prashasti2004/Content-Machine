"""Run folders and history of already-used topics."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from pydantic import BaseModel

from .models import RunManifest


def slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-") or "untitled"


def normalize_title(text: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split())


class Storage:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = output_dir / "history.json"

    # ---- runs ----
    def new_run_dir(self, series_id: str, topic_title: str) -> Path:
        base = f"{date.today().isoformat()}_{series_id}_{slugify(topic_title)}"
        path, n = self.output_dir / base, 2
        while path.exists():
            path, n = self.output_dir / f"{base}-{n}", n + 1
        (path / "assets").mkdir(parents=True)
        return path

    def list_runs(self) -> list[Path]:
        return sorted(p for p in self.output_dir.iterdir() if (p / "manifest.json").exists())

    @staticmethod
    def write_json(path: Path, obj: BaseModel | list | dict) -> Path:
        if isinstance(obj, BaseModel):
            text = obj.model_dump_json(indent=2)
        else:
            text = json.dumps(
                [o.model_dump(mode="json") if isinstance(o, BaseModel) else o for o in obj]
                if isinstance(obj, list) else obj,
                indent=2,
                ensure_ascii=False,
            )
        path.write_text(text, encoding="utf-8")
        return path

    def save_manifest(self, run_dir: Path, manifest: RunManifest) -> None:
        self.write_json(run_dir / "manifest.json", manifest)

    # ---- history ----
    def used_titles(self, series_id: str) -> set[str]:
        if not self.history_file.exists():
            return set()
        data = json.loads(self.history_file.read_text())
        return set(data.get(series_id, []))

    def mark_used(self, series_id: str, title: str) -> None:
        data = json.loads(self.history_file.read_text()) if self.history_file.exists() else {}
        titles = set(data.get(series_id, []))
        titles.add(normalize_title(title))
        data[series_id] = sorted(titles)
        self.history_file.write_text(json.dumps(data, indent=2))
