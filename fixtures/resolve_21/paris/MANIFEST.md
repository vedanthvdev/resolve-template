# Paris fixture (Resolve 21.1)

## Location

The native export used for Phase 1 lives **outside git**:

`/Users/chintuvedanth/Downloads/paris.drp`

Do not commit it: it is a personal project with absolute media paths (`/Users/chintuvedanth/Desktop/paris/...`) and is not needed to regenerate findings (those are in `docs/`).

If a copy is added later:

- `fixtures/resolve_21/paris/paris.drp` — **only** a Resolve `ExportProject` file
- Never hand-craft this archive

## Identity

- Size: 3.8 MB
- Format: ZIP / deflate, 12 XML members
- `DbAppVer="21.1.0.0014"` `DbPrjVer="17"`
- App match: DaVinci Resolve 21.1.0 (21.1.00014)

## Members

See table in `docs/reference_project_analysis.md`. Short list:

- `project.xml`
- `MediaPool/Master/MpFolder.xml`
- 9× `SeqContainer/<uuid>.xml`
- `Gallery.xml`

## Inspect

```bash
.venv/bin/python -m resolve_template.cli inspect /Users/chintuvedanth/Downloads/paris.drp
```

Do not copy this archive into git. For a reproducible inspect fixture, use
`fixtures/resolve_21/cafe/project.drp`.

Expect: `is_zip: true`, 12 members. Do not require ElementTree success.

## Live database names

- `paris`
- `Copy of paris` (open during 2026-09-18 probe)

Do not use these projects for Phase 2 experiments.
