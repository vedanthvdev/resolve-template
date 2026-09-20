from __future__ import annotations

import os
from pathlib import Path

import pytest

from resolve_template.resolve import roundtrip

STORY = Path(__file__).resolve().parents[2] / "examples" / "cafe" / "story.yaml"


def test_cafe_builds_without_resolve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(roundtrip, "get_resolve", lambda: None)
    output = tmp_path / "cafe"
    result = roundtrip.resolve_build(STORY, output=output, overwrite=True)

    assert result["status"] == "GENERATOR_EXISTS"
    assert result["summary"]["timeline_name"] == "PRE_EDIT_MAIN"
    assert result["summary"]["video_clips"] == 3
    assert result["summary"]["linked_video_clips"] == 1
    assert result["summary"]["audio_clips"] == 3
    assert result["summary"]["audio_by_track"] == {"A1": 1, "A2": 1, "A3": 1}
    assert result["summary"]["title_cards"] == 1
    assert result["summary"]["picture_duration_frames"] == 200
    assert result["summary"]["fade_tail_frames"] == 6
    assert result["summary"]["duration_frames"] == 206
    assert (output / "Placeholder_Media" / "TITLE_01_THE_CAFE.mp4").is_file()
    assert Path(result["package_zip"]).is_file()


@pytest.mark.resolve
def test_cafe_roundtrip_in_resolve() -> None:
    if os.environ.get("RESOLVE_ROUNDTRIP") != "1":
        pytest.skip("Set RESOLVE_ROUNDTRIP=1 to mutate disposable Resolve projects")

    output = Path(__file__).resolve().parents[2] / "output" / "cafe"
    result = roundtrip.resolve_build(STORY, output=output, overwrite=True)
    validation = result["validation"]

    assert result["status"] == "VALIDATED_IN_RESOLVE"
    assert validation["video_items_v1"] == 3
    assert validation["video_names"] == ["Exterior", "Interview", "Closing"]
    assert validation["video_durations"] == [50, 100, 50]
    assert validation["audio_items_a1"] == 1
    assert validation["audio_items_a2"] == 1
    assert validation["audio_items_a3"] == 1
    assert validation["audio_items_a4"] == 1
    assert validation["production_audio_names"] == ["Interview (cam)"]
    assert validation["linked_production_audio"] == [True]
    assert validation["title_names"] == ["THE CAFE"]
    assert validation["timeline_folder"] == "Master"
    assert validation["track_names"] == {
        "V1": "Picture",
        "V2": "Titles",
        "A1": "VO",
        "A2": "Music",
        "A3": "SFX",
        "A4": "Production",
    }
    assert validation["picture_duration_frames"] == 200
    assert validation["timeline_duration_frames"] == 206
    assert validation["transition_count"] == 3
    assert validation["marker_count"] == 3
    assert validation["bin_names"] == [
        "A-Roll",
        "Voiceover",
        "Score",
        "Hits",
        "Graphics",
    ]
    assert validation["relinked_clip_count"] == 7
