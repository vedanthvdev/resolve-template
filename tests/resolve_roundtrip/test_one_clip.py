from __future__ import annotations

import os
from pathlib import Path

import pytest

from resolve_template.resolve import roundtrip

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "poc_one_clip" / "story.yaml"


def test_resolve_build_without_resolve(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(roundtrip, "get_resolve", lambda: None)
    out = tmp_path / "out"
    result = roundtrip.resolve_build(EXAMPLES, output=out, overwrite=True)
    assert result["status"] == "GENERATOR_EXISTS"
    assert result["drp"] is None
    assert Path(result["package_zip"]).is_file()
    assert (out / "README.md").exists()
    assert (out / "Placeholder_Media" / "001_OPENING_PLACEHOLDER.mp4").is_file()
    assert (out / "Placeholder_Media" / "VO_01_OPENING_PLACEHOLDER.wav").is_file()
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "**Validation label:** `GENERATOR_EXISTS`" in readme


@pytest.mark.resolve
def test_one_clip_roundtrip_in_resolve() -> None:
    if os.environ.get("RESOLVE_ROUNDTRIP") != "1":
        pytest.skip("Set RESOLVE_ROUNDTRIP=1 to mutate disposable Resolve projects")

    output = Path(__file__).resolve().parents[2] / "output" / "poc_one_clip"
    result = roundtrip.resolve_build(EXAMPLES, output=output, overwrite=True)
    assert result["status"] == "VALIDATED_IN_RESOLVE"
    assert Path(result["drp"]).is_file()
    assert Path(result["package_zip"]).is_file()
    validation = result["validation"]
    assert validation["fps"] == 25.0
    assert validation["video_items_v1"] == 1
    assert validation["audio_items_a1"] == 1
    assert validation["video_name"] == "Shot 001"
    assert validation["audio_name"] == "VO"
    assert validation["video_duration_frames"] == 75
    assert validation["audio_duration_frames"] == 75
    assert validation["gaps"] == []


@pytest.mark.resolve
def test_4k_story_roundtrip_in_resolve(tmp_path: Path) -> None:
    if os.environ.get("RESOLVE_ROUNDTRIP") != "1":
        pytest.skip("Set RESOLVE_ROUNDTRIP=1 to mutate disposable Resolve projects")

    story = tmp_path / "story.yaml"
    story.write_text(
        """
version: "1"
fps: 25
width: 3840
height: 2160
timeline:
  name: UHD
  duration_frames: 1
video:
  - shot: 1
    track: V1
    start_frame: 0
    duration_frames: 1
""",
        encoding="utf-8",
    )
    result = roundtrip.resolve_build(story, output=tmp_path / "out", overwrite=True)
    assert result["status"] == "VALIDATED_IN_RESOLVE"
    assert result["validation"]["width"] == 3840
    assert result["validation"]["height"] == 2160
    assert result["validation"]["video_duration_frames"] == 1
