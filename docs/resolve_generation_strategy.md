# Resolve generation strategy

## Preferred path

1. Author `story.yaml` (human or AI).
2. Generate placeholder media files with deterministic names.
3. Drive Resolve scripting to import media, build timeline, set markers/bins (later phases).
4. Call Resolve `ExportProject` to emit a native `.drp`.
5. Package ZIP with media + tracker + honest README.
6. Round-trip tests re-import the `.drp` and assert structure.

## Rejected path

Hand-writing or mutating `.drp` ZIP internals and claiming they are native Resolve projects.

## Phase coupling

- Phase 1: learn storage + APIs
- Phase 2: prove one-clip export/import
- Phases 3–7: grow timeline fidelity only after Phase 2 is green
- Phase 8: AI emits `story.yaml` only; Resolve XML stays out of the model context
