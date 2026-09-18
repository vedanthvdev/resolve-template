"""Thin wrappers around DaVinci Resolve scripting APIs."""

from __future__ import annotations

from typing import Any


def get_resolve() -> Any | None:
    """Return the Resolve scripting object, or None if unavailable."""
    try:
        import DaVinciResolveScript as dvr  # type: ignore
    except ImportError:
        return None
    try:
        resolve = dvr.scriptapp("Resolve")
    except Exception:
        return None
    return resolve


def resolve_available() -> bool:
    return get_resolve() is not None
