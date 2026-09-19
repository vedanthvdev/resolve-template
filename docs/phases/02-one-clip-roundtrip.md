# Phase 2 — One video clip + one audio clip

**Status in this repo:** **`VALIDATED_IN_RESOLVE` on 2026-09-18** with DaVinci Resolve Studio 21.1.0.

Resolve exported and re-imported a genuine `.drp` containing exactly one generated black video on V1 and one generated silent WAV on A1, both 75 frames at 25 fps.

Phase 1 already confirmed `ProjectManager.ExportProject` / `ImportProject` exist on Studio 21.1.0 and documented `AppendToTimeline` fields (`mediaType` 1=video, 2=audio, `trackIndex`, `recordFrame`). Do not re-inspect `paris.drp` for that. Use a **disposable** project; do not touch `paris` / `Copy of paris`. See `docs/resolve_generation_strategy.md` for the un-run recipe.

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
.venv/bin/python -m resolve_template.cli resolve-build examples/poc_one_clip/story.yaml \
  --output output/poc_one_clip --overwrite
RESOLVE_ROUNDTRIP=1 .venv/bin/python -m pytest \
  tests/resolve_roundtrip/test_one_clip.py::test_one_clip_roundtrip_in_resolve
```

## Gate

**Gate passed.** Re-import validation returned:

- fps: 25
- V1 items: 1, `001_OPENING_PLACEHOLDER.mp4`, 75 frames
- A1 items: 1, `VO_01_OPENING_PLACEHOLDER.wav`, 75 frames
- `.drp`: Resolve-exported ZIP archive
- Disposable build and import projects deleted; original `Copy of paris` restored

Generated package: `output/poc_one_clip.zip` (ignored by git), containing `project.drp`, both placeholder media files, README, and story snapshot.

## Resolve 21.1 findings

- `Project.SetSettings({"timelineFrameRate": 25.0})` works; the earlier combined settings update returned false.
- Runtime `ImportMedia` rejected the typed-dictionary form documented by the bundled stub, but the legacy list-of-paths form succeeded.
- `AppendToTimeline.endFrame` is **exclusive**. `endFrame=74` produced 74 frames; `endFrame=75` produced 75.
