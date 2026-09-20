from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from resolve_template.resolve import roundtrip

STORY = Path(__file__).resolve().parents[2] / "examples" / "poc_linked_audio" / "story.yaml"


def test_linked_audio_builds_without_resolve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(roundtrip, "get_resolve", lambda: None)
    output = tmp_path / "linked_audio"
    result = roundtrip.resolve_build(STORY, output=output, overwrite=True)

    assert result["status"] == "GENERATOR_EXISTS"
    assert result["summary"]["linked_video_clips"] == 1
    media = output / "Placeholder_Media" / "001_CAMERA_WITH_SCRATCH_AUDIO_PLACEHOLDER.mp4"
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "json",
            str(media),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert [stream["codec_type"] for stream in json.loads(probe.stdout)["streams"]] == [
        "video",
        "audio",
    ]
    assert "A4 production (linked to V1)" in (
        output / "timeline_map.md"
    ).read_text(encoding="utf-8")
    assert ",True," in (output / "shot_tracker.csv").read_text(encoding="utf-8")


@pytest.mark.resolve
def test_linked_audio_roundtrip_in_resolve() -> None:
    if os.environ.get("RESOLVE_ROUNDTRIP") != "1":
        pytest.skip("Set RESOLVE_ROUNDTRIP=1 to mutate disposable Resolve projects")

    output = Path(__file__).resolve().parents[2] / "output" / "poc_linked_audio"
    result = roundtrip.resolve_build(STORY, output=output, overwrite=True)
    validation = result["validation"]

    assert result["status"] == "VALIDATED_IN_RESOLVE"
    assert validation["video_items_v1"] == 2
    assert validation["audio_items_a4"] == 1
    assert validation["production_audio_names"] == [
        "001_CAMERA_WITH_SCRATCH_AUDIO_PLACEHOLDER.mp4"
    ]
    assert validation["linked_production_audio"] == [True]
    assert validation["track_names"]["A4"] == "Production"
