"""Environment diagnostics for placeholder generation and Resolve round-trips."""

from __future__ import annotations

import platform
import shutil
import sys
from importlib.resources import files
from pathlib import Path
from typing import Any

from resolve_template.resolve.api import get_resolve

RESOLVE_APP = Path("/Applications/DaVinci Resolve/DaVinci Resolve.app")
RESOLVE_MODULES = Path(
    "/Library/Application Support/Blackmagic Design/"
    "DaVinci Resolve/Developer/Scripting/Modules"
)


def doctor_report() -> dict[str, Any]:
    python_ok = sys.version_info >= (3, 10)
    ffmpeg = shutil.which("ffmpeg")
    schema = files("resolve_template").joinpath("story-v1.schema.json")
    schema_ok = schema.is_file()

    if platform.system() == "Darwin":
        resolve_app_ok = RESOLVE_APP.is_dir()
        scripting_ok = RESOLVE_MODULES.is_dir()
    else:
        resolve_app_ok = False
        scripting_ok = False

    resolve = get_resolve() if scripting_ok else None
    resolve_connected = resolve is not None
    resolve_version = None
    if resolve_connected:
        getter = getattr(resolve, "GetVersionString", None)
        if getter is not None:
            resolve_version = getter()

    checks = [
        _check(
            "Python",
            python_ok,
            f"{platform.python_version()} at {sys.executable}",
            "Create .venv with Python 3.10 or newer.",
        ),
        _check("ffmpeg", bool(ffmpeg), ffmpeg or "not found", "Install ffmpeg and retry."),
        _check(
            "story schema",
            schema_ok,
            str(schema),
            "Reinstall resolve-template so package data is present.",
        ),
        _check(
            "DaVinci Resolve",
            resolve_app_ok,
            str(RESOLVE_APP) if resolve_app_ok else "not found",
            "Install DaVinci Resolve Studio to export a native .drp.",
        ),
        _check(
            "Resolve scripting",
            scripting_ok,
            str(RESOLVE_MODULES) if scripting_ok else "developer modules not found",
            "Install Resolve scripting modules and enable external scripting.",
        ),
        _check(
            "Resolve connection",
            resolve_connected,
            resolve_version or ("connected" if resolve_connected else "not connected"),
            "Start Resolve and enable Preferences > System > General > External scripting.",
        ),
    ]
    return {
        "ok": all(check["ok"] for check in checks),
        "offline_ready": all(check["ok"] for check in checks[:3]),
        "resolve_ready": all(check["ok"] for check in checks),
        "checks": checks,
    }


def _check(name: str, ok: bool, detail: str, fix: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail, "fix": None if ok else fix}
