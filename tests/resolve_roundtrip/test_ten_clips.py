from __future__ import annotations

import os
from pathlib import Path

import pytest

from resolve_template.resolve import roundtrip

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "poc_ten_clips" / "story.yaml"
EXPECTED_NAMES = [f"{index:03d}_SHOT_{index:02d}_PLACEHOLDER.mp4" for index in range(1, 11)]
EXPECTED_STARTS = list(range(0, 250, 25))
EXPECTED_DURATIONS = [25] * 10


def test_ten_clip_build_without_resolve(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(roundtrip, "get_resolve", lambda: None)
    out = tmp_path / "out"
    result = roundtrip.resolve_build(EXAMPLES, output=out, overwrite=True)
    assert result["status"] == "GENERATOR_EXISTS"
    assert result["drp"] is None
    media = out / "Placeholder_Media"
    for name in EXPECTED_NAMES:
        assert (media / name).is_file()
    assert not list(media.glob("*.wav"))


@pytest.mark.resolve
def test_ten_clip_roundtrip_in_resolve() -> None:
    if os.environ.get("RESOLVE_ROUNDTRIP") != "1":
        pytest.skip("Set RESOLVE_ROUNDTRIP=1 to mutate disposable Resolve projects")

    output = Path(__file__).resolve().parents[2] / "output" / "poc_ten_clips"
    result = roundtrip.resolve_build(EXAMPLES, output=output, overwrite=True)
    assert result["status"] == "VALIDATED_IN_RESOLVE"
    assert Path(result["drp"]).is_file()
    validation = result["validation"]
    assert validation["fps"] == 25.0
    assert validation["video_items_v1"] == 10
    assert validation["audio_items_a1"] == 0
    assert validation["video_names"] == [f"Shot {index:03d}" for index in range(1, 11)]
    assert validation["video_starts"] == EXPECTED_STARTS
    assert validation["video_durations"] == EXPECTED_DURATIONS
    assert validation["timeline_duration_frames"] == 250
    assert validation["gaps"] == []
