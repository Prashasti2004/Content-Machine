# Roadmap

## Phase 0 — Foundation ✅
- [x] Repo scaffold, packaging, CI, lint, tests
- [x] Config: `.env` settings + per-series YAML
- [x] Core data models and run storage
- [x] CLI skeleton (`cm`)

## Phase 1 — Trends → Script (MVP brain)
- [x] YouTube trends via Data API v3 (search by keyword, sort by views, recent window)
- [x] Instagram hashtag top/recent media via Graph API
- [x] Virality scorer + de-dup against history
- [x] Claude script generation with structured output
- [ ] Self-critique pass: hook strength, fact-check flags, length check
- [ ] Unit tests with recorded API fixtures

## Phase 2 — Script → Video (MVP body)
- [x] edge-tts voiceover
- [x] faster-whisper word timings
- [x] Pexels visuals
- [x] MoviePy renderer (first pass)
- [ ] Animated word-highlight captions
- [ ] Thumbnail generation
- [ ] ElevenLabs voice provider
- [ ] AI image provider for abstract scenes

## Phase 3 — Review & Publish
- [ ] Local review dashboard (approve / regenerate scene / edit script)
- [ ] YouTube Shorts upload (OAuth)
- [ ] Instagram Reels publish (Graph API content publishing)

## Phase 4 — Automation & Learning
- [ ] Scheduler: N videos/day per series
- [ ] Analytics ingestion (views, retention) → scorer weights
- [ ] Multi-language series (Hindi, etc.)
- [ ] Extra trend sources: Google Trends, Reddit, X
