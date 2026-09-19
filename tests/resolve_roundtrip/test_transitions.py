from __future__ import annotations

import os
from pathlib import Path

import pytest

from resolve_template.resolve import roundtrip

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "poc_transitions_titles" / "story.yaml"


def test_transitions_titles_build_without_resolve(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(roundtrip, "get_resolve", lambda: None)
    out = tmp_path / "out"
    result = roundtrip.resolve_build(EXAMPLES, output=out, overwrite=True)
    assert result["status"] == "GENERATOR_EXISTS"
    assert result["drp"] is None
    assert (out / "Placeholder_Media" / "001_SHOT_01_PLACEHOLDER.mp4").is_file()
    assert (out / "Placeholder_Media" / "TITLE_01_OPENING.mp4").is_file()
    map_text = (out / "timeline_map.md").read_text(encoding="utf-8")
    assert "cross dissolve after shot 1" in map_text
    assert "TITLE_01_OPENING.mp4" in map_text


@pytest.mark.resolve
def test_cross_dissolve_roundtrip_in_resolve() -> None:
    if os.environ.get("RESOLVE_ROUNDTRIP") != "1":
        pytest.skip("Set RESOLVE_ROUNDTRIP=1 to mutate disposable Resolve projects")

    output = Path(__file__).resolve().parents[2] / "output" / "poc_transitions_titles"
    result = roundtrip.resolve_build(EXAMPLES, output=output, overwrite=True)
    assert result["status"] == "VALIDATED_IN_RESOLVE"
    assert Path(result["drp"]).is_file()
    validation = result["validation"]
    assert validation["video_items_v1"] == 2
    assert validation["transition_count"] == 3
    assert [item["story_kind"] for item in validation["transition_validation"]] == [
        "fade_from_black",
        "cross_dissolve",
        "fade_to_black",
    ]
    assert all(
        item["resolve_implementation"] == "Cross Dissolve"
        for item in validation["transition_validation"]
    )
    assert validation["fade_from_black"] is True
    assert validation["fade_to_black"] is True
    assert validation["title_names"] == ["TITLE_01_OPENING.mp4"]
    assert validation["gaps"] == []
    assert validation["relinked_clip_count"] == 3
