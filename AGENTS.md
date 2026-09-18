# Agent instructions

## Build order

Follow [docs/phases/README.md](docs/phases/README.md). Do not implement Phase N+1 features until Phase N’s gate is green.

## Honesty

Never write a README or package metadata that implies Resolve validated a `.drp` unless export + re-import ran on a real install.

## Preferred tools

- Official Resolve scripting only for native projects
- `story.yaml` + JSON Schema for AI/human input
- Unit tests for inspect; `tests/resolve_roundtrip` for live Resolve

## Investigator prompt

When debugging live Resolve behavior, use [prompts/RESOLVE_INVESTIGATOR.md](prompts/RESOLVE_INVESTIGATOR.md).
