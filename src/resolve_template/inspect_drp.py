"""Offline inspection of Resolve .drp archives."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any


def inspect_drp(path: Path) -> dict[str, Any]:
    """Return a summary of archive members without claiming write capability."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    if not zipfile.is_zipfile(path):
        return {
            "path": str(path.resolve()),
            "is_zip": False,
            "status": "INSPECT_ONLY",
            "note": "File is not a ZIP-based .drp; further format work needed.",
            "members": [],
        }

    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        infos = [
            {
                "name": info.filename,
                "compressed_size": info.compress_size,
                "file_size": info.file_size,
            }
            for info in zf.infolist()
        ]

    return {
        "path": str(path.resolve()),
        "is_zip": True,
        "member_count": len(names),
        "members": infos,
        "status": "INSPECT_ONLY",
        "note": "Read-only inspect. A genuine writable .drp requires Resolve ExportProject.",
    }
