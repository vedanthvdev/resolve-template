# Phase 4 — Audio tracks A1 / A2 / A3

**Status in this repo:** **`VALIDATED_IN_RESOLVE` on 2026-09-19** with DaVinci Resolve Studio 21.1.0.

Silent generated WAV placeholders sit on three audio tracks. No real or copyrighted audio is in the package.

## Goal

Silent VO, music and SFX placeholders on three audio tracks.

## Files

- `examples/poc_audio_tracks/story.yaml`
- `src/resolve_template/resolve/roundtrip.py`
- `src/resolve_template/story.py`
- `tests/resolve_roundtrip/test_audio_tracks.py`

## Commands

```bash
.venv/bin/python -m resolve_template.cli resolve-build examples/poc_audio_tracks/story.yaml \
  --output output/poc_audio_tracks --overwrite
RESOLVE_ROUNDTRIP=1 .venv/bin/python -m pytest \
  tests/resolve_roundtrip/test_audio_tracks.py::test_audio_tracks_roundtrip_in_resolve
```

## Gate

**Gate passed.** Re-import clip counts:

| Track | Clips | Names |
|-------|------:|-------|
| V1 | 10 | `001_SHOT_01_PLACEHOLDER.mp4` … `010_SHOT_10_PLACEHOLDER.mp4` |
| A1 | 1 | `VO_01_BED_PLACEHOLDER.wav` (250 frames) |
| A2 | 1 | `MUSIC_01_BED_PLACEHOLDER.wav` (250 frames) |
| A3 | 2 | `SFX_01_HIT_PLACEHOLDER.wav` @ 50, `SFX_02_HIT_PLACEHOLDER.wav` @ 175 |

All audio files are generated silence (48 kHz mono PCM). Disposable round-trip projects were deleted.

Generated package: `output/poc_audio_tracks.zip` (ignored by git).

## Notes

- Empty timelines start with one audio track. The builder calls `Timeline.AddTrack("audio")` until A3 exists.
- `AppendToTimeline` uses `mediaType=2` and `trackIndex` 1/2/3.
- Story validation rejects audio on A4+ and clips that run past the timeline end.
