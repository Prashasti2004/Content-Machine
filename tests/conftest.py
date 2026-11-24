from datetime import UTC, datetime, timedelta

import pytest

from content_machine.config import Series
from content_machine.models import Source, Trend


@pytest.fixture
def series() -> Series:
    return Series.model_validate({
        "id": "test_space",
        "name": "Space Test",
        "sources": {
            "youtube": {"keywords": ["black hole", "nasa"]},
            "instagram": {"hashtags": ["astronomy"]},
        },
    })


def make_trend(title: str, views=0, likes=0, comments=0, hours_ago=10, source=Source.YOUTUBE):
    return Trend(
        source=source, id=title, title=title, url="https://example.com",
        views=views, likes=likes, comments=comments,
        published_at=datetime.now(UTC) - timedelta(hours=hours_ago),
    )
