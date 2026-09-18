from __future__ import annotations

from pathlib import Path

import pytest

from resolve_template.resolve.roundtrip import resolve_build


EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "poc_one_clip" / "story.yaml"


def test_resolve_build_without_resolve(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = resolve_build(EXAMPLES, output=out, overwrite=True)
    assert result["status"] == "GENERATOR_EXISTS"
    assert result["drp"] is None
    assert (out / "README.md").exists()
    assert (out / "Placeholder_Media").is_dir()
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "**Validation label:** `GENERATOR_EXISTS`" in readme


@pytest.mark.resolve
def test_one_clip_roundtrip_in_resolve() -> None:
    pytest.skip("Requires DaVinci Resolve scripting — Phase 2 gate not yet proven")
