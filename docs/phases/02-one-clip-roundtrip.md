# Phase 2 — One video clip + one audio clip

**Status in this repo:** generator + tests exist. Native `.drp` is **not** proven here because Resolve is not installed.

This is the current blocker for every later phase.

## Goal

Resolve itself must:

1. Import `001_OPENING_PLACEHOLDER.mp4`
2. Import `VO_01_OPENING_PLACEHOLDER.wav`
3. Create timeline `PRE_EDIT_MAIN`
4. Place video on V1 and audio on A1
5. Show duration 75 frames at 25 fps
6. `ExportProject` a `.drp`
7. Re-import that `.drp` with the same clips still present

## Files

- `examples/poc_one_clip/story.yaml`
- `src/resolve_template/resolve/roundtrip.py`
- `src/resolve_template/resolve/api.py`
- `scripts/resolve_roundtrip.py`
- `tests/resolve_roundtrip/test_one_clip.py`
- `prompts/RESOLVE_INVESTIGATOR.md`

## Commands

```bash
python3 -m resolve_template.cli resolve-build examples/poc_one_clip/story.yaml --output output --overwrite
python3 -m pytest tests/resolve_roundtrip
```

## Gate

`VALIDATED_IN_RESOLVE`: re-imported project still contains the one video and one audio clip on the expected tracks with duration 75 frames at 25 fps.
