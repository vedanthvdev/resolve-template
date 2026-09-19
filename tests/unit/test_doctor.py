from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from resolve_template import doctor


def test_doctor_reports_resolve_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = tmp_path / "Resolve.app"
    modules = tmp_path / "Modules"
    app.mkdir()
    modules.mkdir()
    monkeypatch.setattr(doctor, "RESOLVE_APP", app)
    monkeypatch.setattr(doctor, "RESOLVE_MODULES", modules)
    monkeypatch.setattr(doctor.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(doctor.shutil, "which", lambda _name: "/usr/local/bin/ffmpeg")
    resolve = SimpleNamespace(GetVersionString=lambda: "21.1.0")
    monkeypatch.setattr(doctor, "get_resolve", lambda: resolve)

    report = doctor.doctor_report()

    assert report["offline_ready"] is True
    assert report["resolve_ready"] is True
    assert all(check["ok"] for check in report["checks"])
