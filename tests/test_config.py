from pathlib import Path

from content_machine.config import list_series, load_series, load_settings

ROOT = Path(__file__).resolve().parents[1] / "config"


def test_example_series_loads():
    s = load_series("example_space_facts", ROOT)
    assert s.sources.youtube and s.sources.youtube.keywords
    assert "spacefacts" in s.keywords


def test_list_series_nonempty():
    assert any(s.id == "example_space_facts" for s in list_series(ROOT))


def test_settings_load():
    settings = load_settings(ROOT)
    assert settings.llm.model == "claude-opus-5-5"
    w = settings.scoring.weights
    assert abs(w.velocity + w.engagement + w.freshness + w.relevance - 1.0) < 1e-9
