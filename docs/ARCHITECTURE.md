# Architecture

Content Machine is a linear, resumable pipeline. Each stage reads the previous stage's artifact from the run folder and writes its own, so any stage can be re-run in isolation (e.g. regenerate only the voiceover).

## Stages

| # | Stage | Module | Input | Output |
|---|---|---|---|---|
| 1 | Trend discovery | `trends.youtube`, `trends.instagram` | `Series` | `trends.json` (`list[Trend]`) |
| 2 | Topic ranking | `trends.scorer` | trends + run history | `topics.json` (`list[Topic]`) |
| 3 | Script | `script.generator` | top `Topic` + `Series` | `script.json` (`Script`) |
| 4 | Voiceover | `voice.*` | `Script.narration` | `voice.mp3` |
| 5 | Captions | `captions.whisper_captions` | `voice.mp3` | `captions.json` (word timings) |
| 6 | Visuals | `visuals.*` | `Script.scenes[*].visual_query` | `assets/scene_NN.*` |
| 7 | Render | `video.renderer` | all of the above + music | `final.mp4`, `thumbnail.jpg`, `metadata.json` |

`pipeline.py` orchestrates the stages and records each one in `manifest.json` (status, timings, error).

## Data models (`models.py`)

- **Trend** — one piece of trending content from a source: `source`, `title`, `url`, `views`, `likes`, `comments`, `published_at`, `tags`, `raw`.
- **Topic** — a candidate idea derived from one or more trends: `title`, `angle`, `score`, `supporting_trends`.
- **Scene** — `narration`, `on_screen_text`, `visual_query`, `duration_hint`.
- **Script** — `title`, `hook`, `scenes`, `cta`, `description`, `hashtags`; `narration` property joins everything for TTS.
- **RunManifest** — run id, series id, topic, per-stage records.

## Scoring

```
velocity    = views / max(hours_since_publish, 1)
engagement  = (likes + 2·comments) / max(views, 1)
freshness   = exp(-hours_since_publish / 72)
relevance   = keyword overlap between trend text and series keywords/hashtags (0..1)

score = 0.45·norm(velocity) + 0.25·norm(engagement) + 0.15·freshness + 0.15·relevance
```

`norm` is min-max within the current batch. Weights live in `config/settings.yaml`. Topics whose normalised title matches a past run in `output/history.json` are dropped.

## Provider pattern

Every external dependency sits behind a small abstract base class:

```python
class TrendSource(ABC):
    name: str
    def fetch(self, series: Series) -> list[Trend]: ...

class VoiceProvider(ABC):
    def synthesize(self, text: str, out_path: Path, voice_id: str) -> Path: ...

class VisualProvider(ABC):
    def fetch(self, query: str, out_dir: Path, index: int) -> Path: ...
```

Adding a provider = new file + registration in the package `__init__.py` + a `provider:` value in series YAML.

## Script generation

- Model: `claude-opus-5-5` with adaptive thinking (configurable in `settings.yaml`).
- Structured output: the response is constrained to a JSON schema and validated into `Script`.
- Server-side refusal fallback is enabled (`fallbacks: "default"`) so a rare safety decline is retried on a fallback model instead of failing the run.
- Prompt template: `script/prompts/short_script.md` — series style guide + topic + top trend titles as *inspiration only* (no copying).

## Rendering

- Canvas 1080×1920, 30 fps, H.264 + AAC.
- Each scene's duration ≈ its share of narration words × voice length.
- Images get a slow zoom (Ken Burns); videos are center-cropped to 9:16 and trimmed/looped.
- Captions: 1–3 words at a time, centered lower-third, highlighted current word.
- Music is mixed under the voice at `music.volume`.

## Future components

- **Review UI** — approve/regenerate per scene before render.
- **Publisher** — YouTube Data API `videos.insert` (Shorts) and Instagram Graph API Reels publishing.
- **Scheduler** — cron/APScheduler, N videos/day per series.
- **Feedback loop** — pull analytics of published videos back into scoring weights.
