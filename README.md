# Content Machine

> Turn what's trending on **YouTube** and **Instagram** into ready-to-post **Shorts / Reels** — automatically, one series at a time.

Content Machine is a pipeline that:

1. **Discovers** trending and viral topics on YouTube and Instagram for a *series* you define (e.g. "Space facts in 60 seconds", "Indian history myths", "AI tools of the week").
2. **Ranks** those topics by virality, freshness and fit with the series.
3. **Writes** a hook-first short-form script (30–60 s) with scene-by-scene visual directions, using Claude.
4. **Produces** the video: voiceover, B-roll / images, burned-in word-level captions, background music, 9:16 render.
5. **Stores** every run (trends, script, assets, final MP4) so you can review before publishing.

```
 series.yaml ─┐
              ▼
 ┌────────────┐   ┌───────────┐   ┌────────────┐   ┌─────────┐   ┌─────────┐   ┌──────────┐
 │  Trends    │──▶│  Topic    │──▶│  Script    │──▶│  Voice  │──▶│ Visuals │──▶│  Render  │──▶ output/<run>/final.mp4
 │ YT + IG    │   │  ranking  │   │  (Claude)  │   │  (TTS)  │   │ + caps  │   │ (FFmpeg) │
 └────────────┘   └───────────┘   └────────────┘   └─────────┘   └─────────┘   └──────────┘
```

> **Status:** early scaffold. The architecture, config, data models and CLI are in place; most stages have a first working implementation or a clearly marked stub. See [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Table of contents

- [Features](#features)
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Getting started](#getting-started)
- [Defining a series](#defining-a-series)
- [CLI usage](#cli-usage)
- [Configuration & API keys](#configuration--api-keys)
- [Output layout](#output-layout)
- [Roadmap](#roadmap)
- [Responsible use](#responsible-use)
- [Contributing](#contributing)

---

## Features

| Stage | What it does | Default provider | Swappable |
|---|---|---|---|
| Trend discovery | Pulls trending Shorts/videos by keyword + region, and top hashtag media from Instagram | YouTube Data API v3, Instagram Graph API | ✅ `trends/` |
| Topic ranking | Scores by views/hour, engagement rate, recency, series relevance; de-dupes against past runs | Built-in scorer (+ optional Claude re-rank) | ✅ `trends/scorer.py` |
| Script writing | Hook → body → payoff → CTA, scene list with on-screen text and visual queries, title, description, hashtags | Claude (`claude-opus-5-5`) with structured JSON output | ✅ `script/` |
| Voiceover | Natural TTS, per-series voice | `edge-tts` (free) — ElevenLabs optional | ✅ `voice/` |
| Visuals | Stock B-roll / images per scene | Pexels API | ✅ `visuals/` |
| Captions | Word-level timestamps → animated burned-in captions | `faster-whisper` | ✅ `captions/` |
| Render | 1080×1920, 30 fps, Ken-Burns on images, music ducking | FFmpeg (via MoviePy) | ✅ `video/` |

## How it works

1. **Series config** (`config/series/*.yaml`) describes the niche: keywords, hashtags, target audience, tone, length, voice, language, region.
2. **`trends`** queries each source and normalises results into `Trend` objects (title, url, views, likes, comments, published_at, source).
3. **`scorer`** computes a virality score and clusters similar trends into candidate **`Topic`s**; topics already used in past runs are skipped.
4. **`script`** sends the top topic + supporting trend context + series style guide to Claude and gets back a validated **`Script`** (scenes, narration, on-screen text, visual search queries, metadata).
5. **`voice`** synthesises narration → `voice.mp3`.
6. **`captions`** transcribes the voiceover for word timings → `captions.json`.
7. **`visuals`** fetches one clip/image per scene → `assets/`.
8. **`video`** assembles everything into `final.mp4` plus `thumbnail.jpg` and `metadata.json` (title, description, hashtags).

Full details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Tech stack

- **Python 3.11+**
- **Typer** CLI, **Pydantic v2** models & settings, **httpx** for APIs
- **Anthropic SDK** (Claude) for scripting
- **edge-tts** / ElevenLabs for voice
- **faster-whisper** for caption timing
- **MoviePy 2 + FFmpeg** for rendering
- **pytest** + **ruff** + GitHub Actions CI

## Project structure

```
Content-Machine/
├── config/
│   ├── settings.yaml            # global defaults (render, providers, paths)
│   └── series/
│       └── example_space_facts.yaml
├── docs/
│   ├── ARCHITECTURE.md
│   └── ROADMAP.md
├── src/content_machine/
│   ├── cli.py                   # `cm` command
│   ├── config.py                # env settings + series loader
│   ├── models.py                # Trend, Topic, Script, Scene, RunManifest
│   ├── pipeline.py              # orchestrates all stages
│   ├── storage.py               # run folders + history of used topics
│   ├── trends/                  # youtube.py, instagram.py, scorer.py
│   ├── script/                  # generator.py + prompts/
│   ├── voice/                   # edge_tts_provider.py
│   ├── captions/                # whisper_captions.py
│   ├── visuals/                 # pexels.py
│   └── video/                   # renderer.py
├── assets/
│   ├── music/                   # royalty-free background tracks (you add these)
│   └── fonts/                   # caption fonts (you add these)
├── output/                      # generated runs (git-ignored)
├── tests/
├── .env.example
├── pyproject.toml
└── Makefile
```

## Getting started

### Prerequisites

- Python **3.11+**
- **FFmpeg** on your PATH (`brew install ffmpeg` / `sudo apt install ffmpeg` / `winget install ffmpeg`)
- API keys (see [below](#configuration--api-keys))

### Install

```bash
git clone https://github.com/Prashasti2004/Content-Machine.git
cd Content-Machine
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,media]"
cp .env.example .env   # then fill in your keys
```

`[media]` pulls the heavy video/audio dependencies (MoviePy, faster-whisper, edge-tts). Leave it out if you only want trends + scripts.

### First run

```bash
cm series list                                   # see available series
cm trends example_space_facts                    # fetch & rank trending topics
cm script example_space_facts                    # write a script for the top topic
cm make   example_space_facts                    # full pipeline → output/<run>/final.mp4
```

## Defining a series

A series is a YAML file in `config/series/`. Example:

```yaml
id: example_space_facts
name: "Space Facts in 60 Seconds"
language: en
region: IN                      # YouTube regionCode for trending
audience: "curious teens and young adults"
tone: "awe-inspiring, fast, a little funny"
duration_seconds: 45

sources:
  youtube:
    keywords: ["space facts", "black hole", "NASA", "universe shorts"]
    max_results: 25
    published_within_days: 7
  instagram:
    hashtags: ["spacefacts", "astronomy", "universe"]

script:
  hook_style: "question or shocking stat in the first 2 seconds"
  cta: "Follow for a new space fact every day"
  banned_topics: ["conspiracy theories"]

voice:
  provider: edge
  voice_id: en-US-GuyNeural

visuals:
  provider: pexels
  style: "cinematic space footage, nebulae, planets"

music:
  track: assets/music/ambient_space.mp3
  volume: 0.12
```

## CLI usage

| Command | Description |
|---|---|
| `cm series list` | List configured series |
| `cm trends <series>` | Fetch trends from all sources and print the ranked topics |
| `cm script <series> [--topic "…"]` | Generate a script (top-ranked topic, or one you pass) |
| `cm make <series> [--topic "…"] [--dry-run]` | Run the full pipeline and render a video |
| `cm runs` | List previous runs |

## Configuration & API keys

Copy `.env.example` to `.env`:

| Variable | Needed for | How to get it |
|---|---|---|
| `ANTHROPIC_API_KEY` | Script writing | [console.anthropic.com](https://console.anthropic.com) (or `ant auth login`) |
| `YOUTUBE_API_KEY` | YouTube trends | Google Cloud Console → enable *YouTube Data API v3* → API key |
| `INSTAGRAM_ACCESS_TOKEN` | Instagram trends | Meta for Developers → Instagram Graph API (requires an IG **Business/Creator** account linked to a Facebook Page) |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | Instagram trends | Graph API Explorer → `me/accounts?fields=instagram_business_account` |
| `PEXELS_API_KEY` | Stock visuals | [pexels.com/api](https://www.pexels.com/api/) |
| `ELEVENLABS_API_KEY` | *(optional)* premium voice | [elevenlabs.io](https://elevenlabs.io) |

> **Instagram note:** the official Graph API's hashtag search is limited to 30 unique hashtags per 7 days per account and returns *top* and *recent* media for a hashtag — not a global "trending" feed. Content Machine treats high-engagement recent hashtag media as the trend signal. Scraping Instagram violates its Terms of Use, so it is not supported here.

## Output layout

```
output/2026-11-24_example_space_facts_black-holes-evaporate/
├── manifest.json      # every stage's inputs/outputs + timings
├── trends.json        # raw normalised trends
├── topics.json        # ranked topics
├── script.json        # final script
├── voice.mp3
├── captions.json
├── assets/            # scene_01.mp4, scene_02.jpg …
├── final.mp4
├── thumbnail.jpg
└── metadata.json      # title, description, hashtags for upload
```

## Roadmap

Short version — see [docs/ROADMAP.md](docs/ROADMAP.md):

- [x] Project scaffold, config, models, CLI
- [ ] Trends: YouTube ✅ first pass · Instagram ✅ first pass · Google Trends / Reddit (planned)
- [ ] Script generation with Claude (first pass) + self-critique loop
- [ ] Voice, captions, visuals, render (first pass)
- [ ] Review dashboard (approve / regenerate a scene)
- [ ] Auto-upload to YouTube Shorts & Instagram Reels
- [ ] Scheduler: N videos/day per series
- [ ] Analytics feedback loop (performance → topic scoring)

## Responsible use

- Use only official APIs and respect each platform's Terms and rate limits.
- Use **trends as inspiration**, not as content to copy. Scripts are original; never re-upload other creators' videos.
- Use royalty-free / licensed music and footage (Pexels license, your own tracks).
- Fact-check scripts before publishing — LLMs can be wrong. Label AI-generated content where platforms require it.

## Contributing

1. Fork → create a branch → `make check` (lint + tests) → open a PR.
2. New providers implement the base class in the matching folder (`trends/base.py`, `voice/base.py`, …) and register in that package's `__init__.py`.

See [CONTRIBUTING.md](CONTRIBUTING.md).
