# Phase 6 — Full story package

**Status in this repo:** **`VALIDATED_IN_RESOLVE` on 2026-09-19** with DaVinci Resolve Studio 21.1.0.

## Goal

ZIP containing:

- native `.drp` only if Resolve exported it
- `Placeholder_Media/`
- shot tracker XLSX/CSV
- timeline map
- README that never lies about Resolve testing

## Files

- `src/resolve_template/package.py`
- `src/resolve_template/resolve/roundtrip.py`
- `tests/unit/test_package.py`
- `tests/resolve_roundtrip/test_full_package.py`
- Story reused from Phase 5: `examples/poc_bins_markers/story.yaml`

## Commands

```bash
.venv/bin/python -m resolve_template.cli resolve-build examples/poc_bins_markers/story.yaml \
  --output output/poc_full_package --overwrite
RESOLVE_ROUNDTRIP=1 .venv/bin/python -m pytest \
  tests/resolve_roundtrip/test_full_package.py::test_full_package_relink_in_resolve
```

## Gate

**Gate passed.**

- Package ZIP includes `project.drp`, `Placeholder_Media/`, `shot_tracker.csv`, `timeline_map.md`, README.
- Tracker video rows are shots 1–10 with matching filenames.
- After `ImportProject`, `MediaPool.RelinkClips` against the package’s persistent
  `Placeholder_Media/` folder brought all 14 media clips online (10 video + 4
  audio). File paths resolved inside that folder.
- README uses `VALIDATED_IN_RESOLVE` only when ExportProject ran.

The tracker is **CSV** (stdlib, no extra dependency). XLSX was not required for the gate.

Generated package: `output/poc_full_package.zip` (ignored by git).
