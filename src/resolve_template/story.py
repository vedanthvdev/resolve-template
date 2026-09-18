"""Load and lightly validate story.yaml documents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_story(path: Path) -> dict[str, Any]:
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"story must be a mapping: {path}")
    if "timeline" not in data:
        raise ValueError(f"story missing timeline: {path}")
    return data
