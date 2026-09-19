# Phase 5 — Markers and Media Pool bins

**Status in this repo:** **`VALIDATED_IN_RESOLVE` on 2026-09-19** with DaVinci Resolve Studio 21.1.0.

## Goal

Create bins `01_VIDEO_PLACEHOLDERS` … `06_REFERENCE` and timeline markers from the story spec.

## Files

- `examples/poc_bins_markers/story.yaml`
- `src/resolve_template/story.py`
- `src/resolve_template/resolve/roundtrip.py`
- `tests/resolve_roundtrip/test_bins_markers.py`

## Commands

```bash
.venv/bin/python -m resolve_template.cli resolve-build examples/poc_bins_markers/story.yaml \
  --output output/poc_bins_markers --overwrite
RESOLVE_ROUNDTRIP=1 .venv/bin/python -m pytest \
  tests/resolve_roundtrip/test_bins_markers.py::test_bins_and_markers_roundtrip_in_resolve
```

## Gate

**Gate passed.** Re-import matched:

Bins (clip names inside each):

| Bin | Clips |
|-----|------:|
| `01_VIDEO_PLACEHOLDERS` | 10 video placeholders |
| `02_AUDIO_VO` | `VO_01_BED_PLACEHOLDER.wav` |
| `03_AUDIO_MUSIC` | `MUSIC_01_BED_PLACEHOLDER.wav` |
| `04_AUDIO_SFX` | 2 SFX hits |
| `05_GRAPHICS` | 0 |
| `06_REFERENCE` | 0 |

Markers (4): `OPENING` @ 0, `SFX_HIT_1` @ 50, `MIDPOINT` @ 125, `LAST_SHOT` @ 225.

Generated package: `output/poc_bins_markers.zip` (ignored by git). Disposable projects deleted.

## Notes

- Bins are created with `MediaPool.AddSubFolder` on Master, then `MoveClips`.
- Video always goes to `01_VIDEO_PLACEHOLDERS`. Audio `role` maps vo/music/sfx to bins 02–04.
- Markers use `Timeline.AddMarker(frame, color, name, note, duration)`.
- Stories without `bins` / `markers` (Phases 2–4) skip this step.
