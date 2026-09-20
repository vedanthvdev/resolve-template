# Phase 9 — linked production audio

**Status in this repo:** **`VALIDATED_IN_RESOLVE` on 2026-09-20** with
DaVinci Resolve Studio 21.1.0.

## Goal

Let camera-style placeholders carry optional silent production audio without
changing the existing A1 VO, A2 Music, and A3 SFX model.

## Story input

```yaml
video:
  - shot: 1
    label: Camera interview
    track: V1
    duration: 2s
    linked_audio: true
```

The generated MP4 contains video and silent stereo AAC. Resolve appends the
picture to V1, appends its production audio to named A4 `Production`, and links
the two timeline items. Video clips without `linked_audio: true` remain
video-only.

## Gate

**Gate passed.** `examples/poc_linked_audio/story.yaml` exported and re-imported
with two V1 clips, one A4 production-audio item, exact matching placement, and a
persisted V1/A4 link.

```bash
RESOLVE_ROUNDTRIP=1 .venv/bin/python -m pytest \
  tests/resolve_roundtrip/test_linked_audio.py
```
