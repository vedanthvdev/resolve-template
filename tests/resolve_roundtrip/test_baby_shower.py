from __future__ import annotations

import os
from pathlib import Path

import pytest

from resolve_template.resolve import roundtrip

STORY = Path(__file__).resolve().parents[2] / "examples" / "baby_shower" / "story.yaml"


def test_baby_shower_builds_without_resolve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(roundtrip, "get_resolve", lambda: None)
    output = tmp_path / "baby_shower"
    result = roundtrip.resolve_build(STORY, output=output, overwrite=True)

    assert result["status"] == "GENERATOR_EXISTS"
    assert result["summary"]["timeline_name"] == "BABY_SHOWER_PRE_EDIT"
    assert result["summary"]["video_clips"] == 28
    assert result["summary"]["linked_video_clips"] == 5
    assert result["summary"]["audio_clips"] == 15
    assert result["summary"]["audio_by_track"] == {"A1": 5, "A2": 2, "A3": 8}
    assert result["summary"]["title_cards"] == 3
    assert result["summary"]["picture_duration_frames"] == 3750
    assert result["summary"]["fade_tail_frames"] == 30
    assert result["summary"]["duration_frames"] == 3780
    assert (output / "Placeholder_Media" / "TITLE_01_BABY_SHOWER.mp4").is_file()
    assert Path(result["package_zip"]).is_file()


@pytest.mark.resolve
def test_baby_shower_roundtrip_in_resolve() -> None:
    if os.environ.get("RESOLVE_ROUNDTRIP") != "1":
        pytest.skip("Set RESOLVE_ROUNDTRIP=1 to mutate disposable Resolve projects")

    output = Path(__file__).resolve().parents[2] / "output" / "baby_shower"
    result = roundtrip.resolve_build(STORY, output=output, overwrite=True)
    validation = result["validation"]

    assert result["status"] == "VALIDATED_IN_RESOLVE"
    assert validation["video_items_v1"] == 28
    assert validation["audio_items_a1"] == 5
    assert validation["audio_items_a2"] == 2
    assert validation["audio_items_a3"] == 8
    assert validation["audio_items_a4"] == 5
    assert validation["production_audio_names"] == [
        "Interview Mom Answer 1 (cam)",
        "Interview Dad Answer 1 (cam)",
        "Interview Friend 1 (cam)",
        "Interview Mom Answer 2 (cam)",
        "Interview Friend 2 (cam)",
    ]
    assert validation["linked_production_audio"] == [True] * 5
    assert validation["title_count"] == 3
    assert validation["timeline_folder"] == "Master"
    assert validation["track_names"]["A1"] == "VO"
    assert validation["track_names"]["A2"] == "Music"
    assert validation["track_names"]["A3"] == "SFX"
    assert validation["track_names"]["A4"] == "Production"
    assert validation["picture_duration_frames"] == 3750
    assert validation["timeline_duration_frames"] == 3780
    assert validation["shot_labels"][0] == "Venue Establishing"
    assert validation["shot_labels"][-1] == "Closing Hands On Belly"
    assert validation["transition_count"] == 4
    assert validation["marker_count"] == 10
    assert validation["bin_names"] == [
        "Shots",
        "Interviews",
        "Songs",
        "Sound Effects",
        "Title Cards",
    ]
    assert validation["relinked_clip_count"] == 46
