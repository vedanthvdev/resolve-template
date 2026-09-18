"""One-clip (and later multi-clip) Resolve round-trip build entrypoints."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from resolve_template.resolve.api import resolve_available
from resolve_template.story import load_story


def resolve_build(
    story_path: Path,
    *,
    output: Path,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Build a placeholder package from story.yaml.

    When Resolve is unavailable, write a GENERATOR_EXISTS package that never
    pretends a native .drp was exported.
    """
    story_path = Path(story_path)
    output = Path(output)
    story = load_story(story_path)

    if output.exists():
        if not overwrite:
            raise FileExistsError(f"output exists (pass --overwrite): {output}")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    media_dir = output / "Placeholder_Media"
    media_dir.mkdir()
    (output / "README.md").write_text(
        _package_readme(resolve_available()),
        encoding="utf-8",
    )
    (output / "story.snapshot.yaml").write_text(
        story_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    if not resolve_available():
        return {
            "status": "GENERATOR_EXISTS",
            "output": str(output.resolve()),
            "timeline": story.get("timeline", {}).get("name"),
            "drp": None,
            "note": "DaVinci Resolve scripting not available; no ExportProject ran.",
        }

    # Phase 2 VALIDATED_IN_RESOLVE path — implement against live Resolve API.
    raise NotImplementedError(
        "Resolve is available but ExportProject round-trip is not implemented yet. "
        "See docs/phases/02-one-clip-roundtrip.md and prompts/RESOLVE_INVESTIGATOR.md."
    )


def _package_readme(resolve_ok: bool) -> str:
    label = "GENERATOR_EXISTS" if not resolve_ok else "VALIDATED_IN_RESOLVE"
    return (
        f"# resolve-template package\n\n"
        f"**Validation label:** `{label}`\n\n"
        "A native `.drp` is included only when DaVinci Resolve exported it.\n"
        "Do not treat hand-written archives as genuine Resolve projects.\n"
    )
