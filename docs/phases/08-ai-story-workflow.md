# Phase 8 — AI story workflow

**Status in this repo:** **`VALIDATED_IN_RESOLVE` on 2026-09-19** with
DaVinci Resolve Studio 21.1.0.

## Goal

Any model can emit `story.yaml`, call this CLI, and get a package. Creative planning stays outside Resolve XML.

## Canonical workflow

```bash
.venv/bin/resolve-template doctor
.venv/bin/resolve-template new my_story --build
```

The canonical checked-in story is `examples/full_story/story.yaml`. It contains
ten labeled, color-coded V1 clips, named A1–A3 tracks, five custom bins, markers,
three semantic transition roles, and one generated title-card MP4 with visible
text on V2. Filenames and sequential V1 starts are derived.

`load_story` enforces the packaged JSON Schema first and reports field paths.
Semantic validators then enforce contiguous V1 coverage and transition targets.

## Gate

**Gate passed.** The full story exported and re-imported through the same path:

- 10 V1 clips and 4 A1–A3 clips
- 5 custom bins and 4 markers with second-based durations
- 3 transitions with semantic roles preserved in the validation report
- timeline stored in Master with named Picture, Titles, VO, Music, and SFX tracks
- 1 generated title card with visible text on V2
- 15 media items relinked to the package’s persistent `Placeholder_Media/`
