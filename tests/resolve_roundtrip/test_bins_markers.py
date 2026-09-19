from __future__ import annotations

import os
from pathlib import Path

import pytest

from resolve_template.resolve import roundtrip
from resolve_template.story import STANDARD_BINS

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "poc_bins_markers" / "story.yaml"


def test_bins_markers_build_without_resolve(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(roundtrip, "get_resolve", lambda: None)
    out = tmp_path / "out"
    result = roundtrip.resolve_build(EXAMPLES, output=out, overwrite=True)
    assert result["status"] == "GENERATOR_EXISTS"
    assert (out / "story.snapshot.yaml").read_text(encoding="utf-8").count("01_VIDEO_PLACEHOLDERS")


@pytest.mark.resolve
def test_bins_and_markers_roundtrip_in_resolve() -> None:
    if os.environ.get("RESOLVE_ROUNDTRIP") != "1":
        pytest.skip("Set RESOLVE_ROUNDTRIP=1 to mutate disposable Resolve projects")

    output = Path(__file__).resolve().parents[2] / "output" / "poc_bins_markers"
    result = roundtrip.resolve_build(EXAMPLES, output=output, overwrite=True)
    assert result["status"] == "VALIDATED_IN_RESOLVE"
    validation = result["validation"]
    assert validation["bin_names"] == list(STANDARD_BINS)
    assert validation["marker_count"] == 4
    assert validation["marker_names"] == ["OPENING", "SFX_HIT_1", "MIDPOINT", "LAST_SHOT"]
    assert validation["audio_items_a1"] == 1
    assert validation["audio_items_a2"] == 1
    assert validation["audio_items_a3"] == 2
    assert validation["video_items_v1"] == 10
