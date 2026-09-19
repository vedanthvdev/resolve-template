# Agent instructions

## Build order

Follow [docs/phases/README.md](docs/phases/README.md). Do not implement Phase N+1 features until Phase N’s gate is green.

## Honesty

Never write a README or package metadata that implies Resolve validated a `.drp` unless export + re-import ran on a real install.

## Preferred tools

- Official Resolve scripting only for native projects
- `story.yaml` + JSON Schema for AI/human input
- Unit tests for inspect; `tests/resolve_roundtrip` for live Resolve

## Do not re-probe paris unless version changes

Phase 1 notes (2026-09-18, Resolve 21.1.0):

- [docs/reference_project_analysis.md](docs/reference_project_analysis.md)
- [docs/file_format_observations.md](docs/file_format_observations.md)
- [docs/resolve_scripting.md](docs/resolve_scripting.md)
- [docs/resolve_generation_strategy.md](docs/resolve_generation_strategy.md)

`.drp` source path: `/Users/chintuvedanth/Downloads/paris.drp`. Live projects `paris` and `Copy of paris` are off-limits for experiments.

## Investigator prompt

Phase 2 passed on Resolve 21.1.0. Use [prompts/RESOLVE_INVESTIGATOR.md](prompts/RESOLVE_INVESTIGATOR.md) only to re-validate after a Resolve version change.
