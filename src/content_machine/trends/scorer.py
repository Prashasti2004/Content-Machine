"""Rank trends into candidate topics. See docs/ARCHITECTURE.md#scoring."""

from __future__ import annotations

import math
import re

from ..config import ScoringSettings, Series
from ..models import Topic, Trend
from ..storage import normalize_title

# Instagram exposes no view counts for other accounts' media; approximate reach
# from interactions so IG posts can be compared with YouTube videos.
IG_INTERACTION_TO_VIEWS = 30


def _popularity(t: Trend) -> float:
    return t.views if t.views else (t.likes + 2 * t.comments) * IG_INTERACTION_TO_VIEWS


def _engagement(t: Trend) -> float | None:
    return (t.likes + 2 * t.comments) / t.views if t.views else None


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _relevance(t: Trend, series: Series) -> float:
    kw_tokens = set().union(*(_tokens(k) for k in series.keywords)) if series.keywords else set()
    if not kw_tokens:
        return 0.0
    text = _tokens(f"{t.title} {t.description} {' '.join(t.tags)}")
    return len(kw_tokens & text) / len(kw_tokens)


def _minmax(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    return [0.5] * len(values) if hi == lo else [(v - lo) / (hi - lo) for v in values]


def score_trends(trends: list[Trend], series: Series, cfg: ScoringSettings) -> list[float]:
    if not trends:
        return []
    w = cfg.weights
    velocity = _minmax([_popularity(t) / t.hours_since_publish for t in trends])

    raw_eng = [_engagement(t) for t in trends]
    known = [e for e in raw_eng if e is not None]
    fill = sum(known) / len(known) if known else 0.0
    engagement = _minmax([e if e is not None else fill for e in raw_eng])

    freshness = [math.exp(-t.hours_since_publish / cfg.freshness_half_life_hours) for t in trends]
    relevance = [_relevance(t, series) for t in trends]

    return [
        w.velocity * v + w.engagement * e + w.freshness * f + w.relevance * r
        for v, e, f, r in zip(velocity, engagement, freshness, relevance, strict=True)
    ]


def rank_topics(
    trends: list[Trend],
    series: Series,
    cfg: ScoringSettings,
    used_titles: set[str] | None = None,
) -> list[Topic]:
    """One topic per distinct trend title, best first, skipping already-used ones."""
    used = used_titles or set()
    scores = score_trends(trends, series, cfg)
    best: dict[str, Topic] = {}
    for trend, score in sorted(zip(trends, scores, strict=True), key=lambda x: -x[1]):
        key = normalize_title(trend.title)
        if not key or key in used:
            continue
        if key in best:
            best[key].supporting_trends.append(trend)
            continue
        best[key] = Topic(title=trend.title, score=round(score, 4), supporting_trends=[trend])
    return list(best.values())[: cfg.top_k_topics]
