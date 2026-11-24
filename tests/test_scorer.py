from content_machine.config import ScoringSettings
from content_machine.models import Source
from content_machine.trends.scorer import rank_topics

from .conftest import make_trend


def test_viral_relevant_trend_ranks_first(series):
    trends = [
        make_trend("Cooking pasta", views=1_000, likes=10, hours_ago=100),
        make_trend("What happens inside a black hole", views=900_000, likes=50_000, hours_ago=12),
        make_trend("NASA just found this", views=200_000, likes=8_000, hours_ago=30),
    ]
    topics = rank_topics(trends, series, ScoringSettings())
    assert topics[0].title == "What happens inside a black hole"
    assert topics[-1].title == "Cooking pasta"


def test_used_titles_are_skipped(series):
    trends = [make_trend("Black Hole Facts!", views=10), make_trend("Other", views=5)]
    topics = rank_topics(trends, series, ScoringSettings(), used_titles={"black hole facts"})
    assert [t.title for t in topics] == ["Other"]


def test_instagram_without_views_is_scored(series):
    trends = [
        make_trend("ig astronomy post", likes=5_000, comments=300, source=Source.INSTAGRAM),
        make_trend("yt video", views=100, likes=1),
    ]
    topics = rank_topics(trends, series, ScoringSettings())
    assert topics[0].title == "ig astronomy post"
