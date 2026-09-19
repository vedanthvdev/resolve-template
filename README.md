# resolve-template

Build DaVinci Resolve **placeholder story templates** from a `story.yaml` so an AI (or a human) can plan a cut without inventing Resolve XML by hand.

This project aims to produce a **genuine** `.drp` by driving Resolve’s official scripting API (`ExportProject`), not by forging archive bytes.

## Current reality

| Capability | Status |
|------------|--------|
| Offline inspect of a real `.drp` | Documented (Phase 1, 21.1 ZIP+XML; see `docs/`) |
| Generated black MP4 + silent WAV package | Working (Phase 2) |
| Native `.drp` proven via Resolve export + re-import | **Validated** on Studio 21.1.0 |
| Ten sequential V1 placeholders, no gaps | **Validated** on Studio 21.1.0 |
| Silent VO / music / SFX on A1–A3 | **Validated** on Studio 21.1.0 |
| Six Media Pool bins + timeline markers | **Validated** on Studio 21.1.0 |
| Full package ZIP + one-folder relink | **Validated** on Studio 21.1.0 |
| Cross dissolve, fades, generated title cards | **Validated** on Studio 21.1.0 |
| Canonical AI/human full-story workflow | **Validated** on Studio 21.1.0 |

See [docs/phases/README.md](docs/phases/README.md) for the build order. The canonical
template is [`examples/full_story/story.yaml`](examples/full_story/story.yaml).

## Phased plan

1. Research / inspect real projects → [docs/phases/01-research.md](docs/phases/01-research.md)
2. One video + one audio round-trip → [docs/phases/02-one-clip-roundtrip.md](docs/phases/02-one-clip-roundtrip.md)
3. Multi-clip timeline → [docs/phases/03-multi-clip.md](docs/phases/03-multi-clip.md)
4. Audio tracks A1–A3 → [docs/phases/04-audio-tracks.md](docs/phases/04-audio-tracks.md)
5. Markers and Media Pool bins → [docs/phases/05-markers-and-bins.md](docs/phases/05-markers-and-bins.md)
6. Full story package ZIP → [docs/phases/06-full-story-package.md](docs/phases/06-full-story-package.md)
7. Transitions and titles → [docs/phases/07-transitions-and-titles.md](docs/phases/07-transitions-and-titles.md)
8. AI story workflow → [docs/phases/08-ai-story-workflow.md](docs/phases/08-ai-story-workflow.md)

## Quick start

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/resolve-template doctor
.venv/bin/resolve-template new my_story
.venv/bin/resolve-template resolve-build examples/full_story/story.yaml \
  --output output/full_story --force
```

The build command prints the DRP path, ZIP path, timeline duration, clip counts,
and what to open in Resolve. Use `--json` only for machine-readable output.
Schema failures print field paths without a Python traceback.

## Easier story authoring

- Use seconds such as `start: 2s` and `duration: 1.48s`; values must land on a
  whole frame at the selected fps.
- Omit V1 `start` values to place shots sequentially.
- Omit `timeline.duration_frames` to derive it from V1.
- Omit `bins` entirely, or map only the roles you need to custom names:

```yaml
bins:
  video: Shots
  music: Score
  graphics: Title Cards
```

Frame fields remain supported for exact control. `--overwrite` remains an alias
for `--force`.

`doctor` checks conventional Resolve locations on macOS, Windows, and Linux.
Use `RESOLVE_APP_PATH` and `RESOLVE_SCRIPT_API` for custom installs.

```bash
.venv/bin/python -m pytest tests/unit
RESOLVE_ROUNDTRIP=1 .venv/bin/python -m pytest \
  tests/resolve_roundtrip/test_full_story.py::test_full_story_roundtrip_in_resolve
```

`titles` currently produce generated title-card MP4 placeholders on V2. They are
not native Resolve Text or Text+ titles, and the `text` field remains planning
metadata rather than burned-in text.

## Honesty labels

- `INSPECT_ONLY` — read/analyze `.drp` without claiming we can write one
- `GENERATOR_EXISTS` — code path exists; Resolve may be absent
- `VALIDATED_IN_RESOLVE` — export + re-import proven on a real Resolve install

## License

MIT
