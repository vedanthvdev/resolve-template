from __future__ import annotations

import zipfile
from pathlib import Path

from resolve_template.inspect_drp import inspect_drp


def test_inspect_zip_drp(tmp_path: Path) -> None:
    drp = tmp_path / "sample.drp"
    with zipfile.ZipFile(drp, "w") as zf:
        zf.writestr("Project/project.db", b"not-a-real-db")
        zf.writestr("MediaPool/clip.json", b"{}")

    result = inspect_drp(drp)
    assert result["is_zip"] is True
    assert result["member_count"] == 2
    assert result["status"] == "INSPECT_ONLY"
    assert result["db_app_ver"] is None
    names = {m["name"] for m in result["members"]}
    assert "Project/project.db" in names


def test_inspect_non_zip(tmp_path: Path) -> None:
    drp = tmp_path / "opaque.drp"
    drp.write_bytes(b"\x00\x01not-zip")
    result = inspect_drp(drp)
    assert result["is_zip"] is False
    assert result["status"] == "INSPECT_ONLY"
    assert result["db_app_ver"] is None


def test_inspect_exported_cafe_fixture() -> None:
    drp = (
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "resolve_21"
        / "cafe"
        / "project.drp"
    )
    result = inspect_drp(drp)
    names = {member["name"] for member in result["members"]}
    assert result["is_zip"] is True
    assert result["status"] == "INSPECT_ONLY"
    assert result["db_app_ver"] == "21.1.0.0014"
    assert result["member_count"] == 9
    assert "project.xml" in names
    assert "Gallery.xml" in names
    assert any(name.startswith("SeqContainer/") for name in names)
    assert any(name.endswith("MpFolder.xml") for name in names)
