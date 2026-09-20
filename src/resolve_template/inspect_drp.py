"""Offline inspection of Resolve .drp archives."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Any

_DB_APP_VER = re.compile(r'DbAppVer="([^"]+)"')


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
            "db_app_ver": None,
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
        db_app_ver = _read_db_app_ver(zf)

    return {
        "path": str(path.resolve()),
        "is_zip": True,
        "member_count": len(names),
        "members": infos,
        "db_app_ver": db_app_ver,
        "status": "INSPECT_ONLY",
        "note": "Read-only inspect. A genuine writable .drp requires Resolve ExportProject.",
    }


def _read_db_app_ver(archive: zipfile.ZipFile) -> str | None:
    if "project.xml" not in archive.namelist():
        return None
    header = archive.read("project.xml")[:512].decode("utf-8", errors="replace")
    match = _DB_APP_VER.search(header)
    return match.group(1) if match else None
