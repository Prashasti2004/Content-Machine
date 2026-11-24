from content_machine.models import Scene, Script, Topic
from content_machine.script.generator import build_prompt
from content_machine.storage import Storage, slugify
from content_machine.video.renderer import scene_durations


def _script() -> Script:
    return Script(
        title="t", hook="Did you know this?", cta="Follow for more",
        description="d", hashtags=["space"],
        scenes=[Scene(narration="one two three", visual_query="stars"),
                Scene(narration="four five", visual_query="planet")],
    )


def test_narration_joins_parts():
    assert _script().narration == "Did you know this? one two three four five Follow for more"


def test_scene_durations_sum_to_total():
    d = scene_durations(_script(), 12.0)
    assert len(d) == 2 and abs(sum(d) - 12.0) < 1e-9


def test_storage_history_roundtrip(tmp_path):
    st = Storage(tmp_path)
    st.mark_used("s", "Black Holes, Explained!")
    assert st.used_titles("s") == {"black holes explained"}
    run = st.new_run_dir("s", "Black Holes, Explained!")
    assert run.name.endswith("s_black-holes-explained") and (run / "assets").is_dir()


def test_slugify():
    assert slugify("  Hello, World!! ") == "hello-world"


def test_prompt_renders(series):
    prompt = build_prompt(series, Topic(title="Black holes evaporate"))
    assert "Black holes evaporate" in prompt and "{" not in prompt
