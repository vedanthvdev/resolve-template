from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest

from resolve_template.resolve import roundtrip

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "poc_bins_markers" / "story.yaml"


def test_full_package_without_resolve(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(roundtrip, "get_resolve", lambda: None)
    out = tmp_path / "out"
    result = roundtrip.resolve_build(EXAMPLES, output=out, overwrite=True)
    assert result["status"] == "GENERATOR_EXISTS"
    assert result["drp"] is None
    assert (out / "shot_tracker.csv").is_file()
    assert (out / "timeline_map.md").is_file()
    assert "omitted because Resolve did not export it" in (out / "README.md").read_text(
        encoding="utf-8"
    )
    with (out / "shot_tracker.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    video_names = [row["filename"] for row in rows if row["kind"] == "video"]
    assert video_names[0] == "001_SHOT_01_PLACEHOLDER.mp4"


@pytest.mark.resolve
def test_full_package_relink_in_resolve() -> None:
    if os.environ.get("RESOLVE_ROUNDTRIP") != "1":
        pytest.skip("Set RESOLVE_ROUNDTRIP=1 to mutate disposable Resolve projects")

    output = Path(__file__).resolve().parents[2] / "output" / "poc_full_package"
    result = roundtrip.resolve_build(EXAMPLES, output=output, overwrite=True)
    assert result["status"] == "VALIDATED_IN_RESOLVE"
    assert Path(result["drp"]).is_file()
    validation = result["validation"]
    assert validation["relinked_clip_count"] == 14
    assert "001_SHOT_01_PLACEHOLDER.mp4" in validation["relinked_names"]
    assert "VO_01_BED_PLACEHOLDER.wav" in validation["relinked_names"]
    with (output / "shot_tracker.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [int(row["shot"]) for row in rows if row["kind"] == "video"] == list(range(1, 11))
    readme = (output / "README.md").read_text(encoding="utf-8")
    assert "**Validation label:** `VALIDATED_IN_RESOLVE`" in readme
    assert "ExportProject" in readme
