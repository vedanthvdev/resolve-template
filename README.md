# resolve-template

Build DaVinci Resolve **placeholder story templates** from a `story.yaml` so an AI (or a human) can plan a cut without inventing Resolve XML by hand.

This project aims to produce a **genuine** `.drp` by driving Resolve’s official scripting API (`ExportProject`), not by forging archive bytes.

## Current reality

| Capability | Status |
|------------|--------|
| Offline inspect of a real `.drp` | Scaffolded (Phase 1) |
| Generator / CLI that *would* call Resolve | Scaffolded (Phase 2) |
| Native `.drp` proven via Resolve export + re-import | **Not proven** — Resolve not validated in this environment |

See [docs/phases/README.md](docs/phases/README.md) for the build order. **Phase 2 is the blocker** for everything after it.

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
python3 -m pip install -e ".[dev]"
python3 -m resolve_template.cli --help
python3 -m pytest tests/unit
```

When DaVinci Resolve is installed and scripting is enabled:

```bash
python3 -m resolve_template.cli resolve-build examples/poc_one_clip/story.yaml --output output --overwrite
python3 -m pytest tests/resolve_roundtrip
```

## Honesty labels

- `INSPECT_ONLY` — read/analyze `.drp` without claiming we can write one
- `GENERATOR_EXISTS` — code path exists; Resolve may be absent
- `VALIDATED_IN_RESOLVE` — export + re-import proven on a real Resolve install

## License

MIT
