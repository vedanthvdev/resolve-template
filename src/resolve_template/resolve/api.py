"""Thin wrappers around DaVinci Resolve scripting APIs."""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Any


def resolve_script_module_paths(system: str | None = None) -> list[Path]:
    """Return official scripting module locations for the current platform."""
    system = system or platform.system()
    paths: list[Path] = []
    script_api = os.environ.get("RESOLVE_SCRIPT_API")
    if script_api:
        configured = Path(script_api)
        paths.append(configured if configured.name == "Modules" else configured / "Modules")
    if system == "Darwin":
        paths.append(
            Path(
                "/Library/Application Support/Blackmagic Design/"
                "DaVinci Resolve/Developer/Scripting/Modules"
            )
        )
    elif system == "Windows":
        program_data = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        paths.append(
            program_data
            / "Blackmagic Design"
            / "DaVinci Resolve"
            / "Support"
            / "Developer"
            / "Scripting"
            / "Modules"
        )
    elif system == "Linux":
        paths.append(Path("/opt/resolve/Developer/Scripting/Modules"))
    return list(dict.fromkeys(paths))


def get_resolve() -> Any | None:
    """Return the Resolve scripting object, or None if unavailable."""
    try:
        import DaVinciResolveScript as dvr  # type: ignore
    except ImportError:
        for module_dir in resolve_script_module_paths():
            if not module_dir.is_dir():
                continue
            sys.path.insert(0, str(module_dir))
            try:
                import DaVinciResolveScript as dvr  # type: ignore

                break
            except ImportError:
                continue
        else:
            return None
    try:
        resolve = dvr.scriptapp("Resolve")
    except Exception:  # noqa: BLE001 - native Resolve boundary has no stable exception types
        return None
    return resolve


def resolve_available() -> bool:
    return get_resolve() is not None
