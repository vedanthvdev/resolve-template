from __future__ import annotations

import os
from pathlib import Path

import pytest

from resolve_template.resolve import roundtrip

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "poc_audio_tracks" / "story.yaml"
VIDEO_NAMES = [f"{index:03d}_SHOT_{index:02d}_PLACEHOLDER.mp4" for index in range(1, 11)]
AUDIO_FILES = [
    "VO_01_BED_PLACEHOLDER.wav",
    "MUSIC_01_BED_PLACEHOLDER.wav",
    "SFX_01_HIT_PLACEHOLDER.wav",
    "SFX_02_HIT_PLACEHOLDER.wav",
]


def test_audio_tracks_build_without_resolve(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(roundtrip, "get_resolve", lambda: None)
    out = tmp_path / "out"
    result = roundtrip.resolve_build(EXAMPLES, output=out, overwrite=True)
    assert result["status"] == "GENERATOR_EXISTS"
    media = out / "Placeholder_Media"
    for name in [*VIDEO_NAMES, *AUDIO_FILES]:
        assert (media / name).is_file()
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "silent WAVs" in readme


@pytest.mark.resolve
def test_audio_tracks_roundtrip_in_resolve() -> None:
    if os.environ.get("RESOLVE_ROUNDTRIP") != "1":
        pytest.skip("Set RESOLVE_ROUNDTRIP=1 to mutate disposable Resolve projects")

    output = Path(__file__).resolve().parents[2] / "output" / "poc_audio_tracks"
    result = roundtrip.resolve_build(EXAMPLES, output=output, overwrite=True)
    assert result["status"] == "VALIDATED_IN_RESOLVE"
    validation = result["validation"]
    assert validation["video_items_v1"] == 10
    assert validation["audio_items_a1"] == 1
    assert validation["audio_items_a2"] == 1
    assert validation["audio_items_a3"] == 2
    assert validation["audio_names_by_track"] == {
        "A1": ["VO"],
        "A2": ["MUSIC"],
        "A3": ["SFX", "SFX"],
    }
