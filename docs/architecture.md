# Architecture

```
story.yaml  -->  CLI (resolve-build)  -->  Resolve scripting  -->  ExportProject .drp
                     |                         |
                     v                         v
              Placeholder_Media/         Round-trip tests
                     |
                     v
              Package ZIP + tracker + README (honest label)
```

## Packages

- `resolve_template.cli` — user entrypoints
- `resolve_template.inspect_drp` — offline archive inspect (Phase 1)
- `resolve_template.story` — YAML load / validate
- `resolve_template.resolve.api` — Resolve connection
- `resolve_template.resolve.roundtrip` — build + export orchestration

## Validation labels

Propagated into package READMEs and CLI JSON: `INSPECT_ONLY`, `GENERATOR_EXISTS`, `VALIDATED_IN_RESOLVE`.
