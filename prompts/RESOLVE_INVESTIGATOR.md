# Resolve investigator prompt

**Archived result:** Phase 2 passed on 2026-09-18. Reuse this only when re-validating against a different Resolve version.

Do **not** repeat Phase 1 (ZIP layout, paris timelines, API existence). That is already in `docs/`. This prompt is only for the one-clip **export + re-import** experiment.

## Mission

Prove a one-clip + one-audio timeline can be built via scripting, exported with `ExportProject`, and re-imported with the same media still present.

## Checklist

1. Confirm scripting module import and `scriptapp("Resolve")` succeeds.
2. Create or open a disposable project.
3. Import `001_OPENING_PLACEHOLDER.mp4` and `VO_01_OPENING_PLACEHOLDER.wav`.
4. Create timeline `PRE_EDIT_MAIN` at 25 fps.
5. Place video on V1 and audio on A1 for 75 frames.
6. Export `.drp`, then re-import into a clean project database.
7. Record exact API method names, return values, and failures.
8. Update `docs/resolve_scripting.md` and mark Phase 2 `VALIDATED_IN_RESOLVE` only if re-import succeeds.

## Output format

- What worked (API calls)
- What failed (errors, null returns)
- Minimal code that reproduces success
- Open questions / API gaps
