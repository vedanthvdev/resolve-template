# Paris fixture (Resolve 21)

Place a real DaVinci Resolve project export here:

- `paris.drp` — native export from Resolve (do not hand-craft)

Then run:

```bash
python3 -m resolve_template.cli inspect fixtures/resolve_21/paris/paris.drp
```

Update `docs/reference_project_analysis.md` and `docs/file_format_observations.md` with findings.

**Status:** fixture not yet committed (binary export pending).
