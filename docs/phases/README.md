# Build phases

Build **one phase at a time**. Do not start a phase until its predecessor gate is green.

| Phase | Doc | Status | Gate |
|-------|-----|--------|------|
| 1 | [01-research.md](01-research.md) | **Documented 2026-09-18** (ZIP + APIs; no write proven) | Offline inspect notes + official ExportProject map |
| 2 | [02-one-clip-roundtrip.md](02-one-clip-roundtrip.md) | **Validated 2026-09-18** | `VALIDATED_IN_RESOLVE` one-clip round-trip |
| 3 | [03-multi-clip.md](03-multi-clip.md) | **Validated 2026-09-19** | 10 sequential V1 clips round-trip |
| 4 | [04-audio-tracks.md](04-audio-tracks.md) | **Validated 2026-09-19** | A1 / A2 / A3 clip counts match |
| 5 | [05-markers-and-bins.md](05-markers-and-bins.md) | **Validated 2026-09-19** | Markers + bins match spec |
| 6 | [06-full-story-package.md](06-full-story-package.md) | **Validated 2026-09-19** | ZIP package with honest README |
| 7 | [07-transitions-and-titles.md](07-transitions-and-titles.md) | **Validated 2026-09-19** | At least one transition round-trip |
| 8 | [08-ai-story-workflow.md](08-ai-story-workflow.md) | **Validated 2026-09-19** | Full story builds via same path |

## Rules

1. **Never claim Resolve validation** unless a real DaVinci Resolve install exported and re-imported the `.drp`.
2. **Native `.drp` only** when Resolve produced it via `ExportProject` (or equivalent official API). Do not hand-craft fake archives and call them genuine.
3. **Fail closed on honesty**: READMEs, package metadata, and CI labels must distinguish `INSPECT_ONLY`, `GENERATOR_EXISTS`, and `VALIDATED_IN_RESOLVE`.
4. Prefer small PRs that advance a single phase gate.
