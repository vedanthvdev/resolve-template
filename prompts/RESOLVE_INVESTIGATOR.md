# Resolve investigator prompt

Use this when a live DaVinci Resolve install is available and Phase 2 must be proven.

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
