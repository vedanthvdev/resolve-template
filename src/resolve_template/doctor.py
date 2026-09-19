"""Environment diagnostics for placeholder generation and Resolve round-trips."""

from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import sys
from importlib.resources import files
from pathlib import Path
from typing import Any

from resolve_template.resolve.api import get_resolve, resolve_script_module_paths


def resolve_app_paths(system: str | None = None) -> list[Path]:
    """Return configured and conventional Resolve application locations."""
    system = system or platform.system()
    paths: list[Path] = []
    configured = os.environ.get("RESOLVE_APP_PATH")
    if configured:
        paths.append(Path(configured))
    executable = shutil.which("Resolve.exe" if system == "Windows" else "resolve")
    if executable:
        paths.append(Path(executable))
    if system == "Darwin":
        paths.append(Path("/Applications/DaVinci Resolve/DaVinci Resolve.app"))
    elif system == "Windows":
        program_files = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        paths.append(
            program_files / "Blackmagic Design" / "DaVinci Resolve" / "Resolve.exe"
        )
    elif system == "Linux":
        paths.append(Path("/opt/resolve/bin/resolve"))
    return list(dict.fromkeys(paths))


def doctor_report() -> dict[str, Any]:
    python_ok = sys.version_info >= (3, 10)
    ffmpeg = shutil.which("ffmpeg")
    schema = files("resolve_template").joinpath("story-v1.schema.json")
    schema_ok = schema.is_file()

    system = platform.system()
    app_path = next((path for path in resolve_app_paths(system) if path.exists()), None)
    module_path = next(
        (path for path in resolve_script_module_paths(system) if path.is_dir()), None
    )
    try:
        module_importable = importlib.util.find_spec("DaVinciResolveScript") is not None
    except (ImportError, ValueError):
        module_importable = False

    resolve = get_resolve()
    resolve_connected = resolve is not None
    resolve_app_ok = app_path is not None or resolve_connected
    scripting_ok = module_path is not None or module_importable or resolve_connected
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
            str(app_path) if app_path else ("running" if resolve_connected else "not found"),
            "Install DaVinci Resolve Studio to export a native .drp.",
        ),
        _check(
            "Resolve scripting",
            scripting_ok,
            str(module_path)
            if module_path
            else ("importable" if module_importable or resolve_connected else "not found"),
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
