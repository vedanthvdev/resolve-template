from __future__ import annotations

import os
from pathlib import Path

import pytest

from resolve_template.resolve import roundtrip

STORY = Path(__file__).resolve().parents[2] / "examples" / "full_story" / "story.yaml"


def test_full_story_builds_without_resolve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(roundtrip, "get_resolve", lambda: None)
    output = tmp_path / "full_story"
    result = roundtrip.resolve_build(STORY, output=output, overwrite=True)

    assert result["status"] == "GENERATOR_EXISTS"
    assert result["summary"] == {
        "timeline_name": "PRE_EDIT_MAIN",
        "fps": 25.0,
        "duration_frames": 250,
        "duration_seconds": 10.0,
        "video_clips": 10,
        "audio_clips": 4,
        "audio_by_track": {"A1": 1, "A2": 1, "A3": 2},
        "title_cards": 1,
        "transitions": ["fade_from_black", "cross_dissolve", "fade_to_black"],
    }
    assert (output / "Placeholder_Media" / "TITLE_CARD_01_OPENING.mp4").is_file()
    assert Path(result["package_zip"]).is_file()


@pytest.mark.resolve
def test_full_story_roundtrip_in_resolve() -> None:
    if os.environ.get("RESOLVE_ROUNDTRIP") != "1":
        pytest.skip("Set RESOLVE_ROUNDTRIP=1 to mutate disposable Resolve projects")

    output = Path(__file__).resolve().parents[2] / "output" / "full_story"
    result = roundtrip.resolve_build(STORY, output=output, overwrite=True)
    validation = result["validation"]

    assert result["status"] == "VALIDATED_IN_RESOLVE"
    assert validation["video_items_v1"] == 10
    assert validation["audio_items_a1"] == 1
    assert validation["audio_items_a2"] == 1
    assert validation["audio_items_a3"] == 2
    assert validation["title_names"] == ["TITLE_CARD_01_OPENING.mp4"]
    assert validation["transition_count"] == 3
    assert validation["marker_count"] == 4
    assert validation["bin_names"] == [
        "01_VIDEO_PLACEHOLDERS",
        "02_AUDIO_VO",
        "03_AUDIO_MUSIC",
        "04_AUDIO_SFX",
        "05_GRAPHICS",
        "06_REFERENCE",
    ]
    assert validation["relinked_clip_count"] == 15
    assert Path(validation["relink_folder"]) == output.resolve() / "Placeholder_Media"
