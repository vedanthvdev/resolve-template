# Phase 3 — Multi-clip timeline

**Status in this repo:** **`VALIDATED_IN_RESOLVE` on 2026-09-19** with DaVinci Resolve Studio 21.1.0.

Ten sequential generated video placeholders sit on V1 with matching shot numbers, filenames, starts, and no gaps. No audio bed was added so video order bugs cannot hide under a single A1 clip.

## Goal

Ten sequential video placeholders on V1. Filenames, shot numbers and timeline order must match.

## Files

- `examples/poc_ten_clips/story.yaml`
- `src/resolve_template/resolve/roundtrip.py`
- `src/resolve_template/story.py`
- `src/resolve_template/placeholders.py`
- `tests/resolve_roundtrip/test_ten_clips.py`
- `tests/unit/test_story.py`

## Commands

```bash
.venv/bin/python -m resolve_template.cli resolve-build examples/poc_ten_clips/story.yaml \
  --output output/poc_ten_clips --overwrite
RESOLVE_ROUNDTRIP=1 .venv/bin/python -m pytest \
  tests/resolve_roundtrip/test_ten_clips.py::test_ten_clip_roundtrip_in_resolve
```

## Gate

**Gate passed.** Re-import validation returned:

- fps: 25
- V1 items: 10
- names: `001_SHOT_01_PLACEHOLDER.mp4` … `010_SHOT_10_PLACEHOLDER.mp4`
- starts: 0, 25, 50, … 225
- durations: 25 frames each
- timeline coverage: 250 frames
- gaps: none
- A1 items: 0
- Disposable projects deleted; `Copy of paris` restored

Generated package: `output/poc_ten_clips.zip` (ignored by git).

## Notes

- Story validation rejects V1 gaps, shot-number skips, and timeline duration that does not match clip coverage.
- Each shot is a generated 1920×1080 color MP4 (1 second at 25 fps). No real camera media.
- Phase 4 may add silent A1/A2/A3 beds; they were intentionally omitted here.
