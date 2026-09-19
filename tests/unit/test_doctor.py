from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from resolve_template import doctor
from resolve_template.resolve.api import resolve_script_module_paths


def test_doctor_reports_resolve_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = tmp_path / "Resolve.app"
    modules = tmp_path / "Modules"
    app.mkdir()
    modules.mkdir()
    monkeypatch.setattr(doctor.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        doctor.shutil,
        "which",
        lambda name: "/usr/local/bin/ffmpeg" if name == "ffmpeg" else None,
    )
    monkeypatch.setattr(doctor, "resolve_app_paths", lambda _system: [app])
    monkeypatch.setattr(doctor, "resolve_script_module_paths", lambda _system: [modules])
    monkeypatch.setattr(doctor.importlib.util, "find_spec", lambda _name: None)
    resolve = SimpleNamespace(GetVersionString=lambda: "21.1.0")
    monkeypatch.setattr(doctor, "get_resolve", lambda: resolve)

    report = doctor.doctor_report()

    assert report["offline_ready"] is True
    assert report["resolve_ready"] is True
    assert all(check["ok"] for check in report["checks"])


def test_windows_resolve_paths_use_program_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("RESOLVE_APP_PATH", raising=False)
    monkeypatch.setenv("PROGRAMFILES", str(tmp_path / "Program Files"))
    monkeypatch.setattr(doctor.shutil, "which", lambda _name: None)
    assert doctor.resolve_app_paths("Windows") == [
        tmp_path
        / "Program Files"
        / "Blackmagic Design"
        / "DaVinci Resolve"
        / "Resolve.exe"
    ]


def test_linux_resolve_paths_include_official_locations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RESOLVE_APP_PATH", raising=False)
    monkeypatch.delenv("RESOLVE_SCRIPT_API", raising=False)
    monkeypatch.setattr(doctor.shutil, "which", lambda _name: None)
    assert doctor.resolve_app_paths("Linux") == [Path("/opt/resolve/bin/resolve")]
    assert resolve_script_module_paths("Linux") == [
        Path("/opt/resolve/Developer/Scripting/Modules")
    ]


def test_configured_paths_override_platform_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = tmp_path / "resolve"
    api = tmp_path / "Developer" / "Scripting"
    monkeypatch.setenv("RESOLVE_APP_PATH", str(app))
    monkeypatch.setenv("RESOLVE_SCRIPT_API", str(api))
    monkeypatch.setattr(doctor.shutil, "which", lambda _name: None)
    assert doctor.resolve_app_paths("Linux")[0] == app
    assert resolve_script_module_paths("Linux")[0] == api / "Modules"
