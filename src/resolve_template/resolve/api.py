"""Thin wrappers around DaVinci Resolve scripting APIs."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


def get_resolve() -> Any | None:
    """Return the Resolve scripting object, or None if unavailable."""
    try:
        import DaVinciResolveScript as dvr  # type: ignore
    except ImportError:
        module_dir = Path(
            "/Library/Application Support/Blackmagic Design/"
            "DaVinci Resolve/Developer/Scripting/Modules"
        )
        if not module_dir.is_dir():
            return None
        sys.path.insert(0, str(module_dir))
        try:
            import DaVinciResolveScript as dvr  # type: ignore
        except ImportError:
            return None
    try:
        resolve = dvr.scriptapp("Resolve")
    except Exception:  # noqa: BLE001 - native Resolve boundary has no stable exception types
        return None
    return resolve


def resolve_available() -> bool:
    return get_resolve() is not None
