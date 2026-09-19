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

## What Resolve stores vs what we generate

| Artifact | Who writes it | Notes |
|----------|---------------|--------|
| `.drp` | Resolve `ExportProject` only | ZIP of XML + binary blobs; see `file_format_observations.md` |
| Placeholder media | this CLI | mp4/wav/png with stable names |
| `story.yaml` | human or model | never Resolve XML |
| Package README | this CLI | must carry `INSPECT_ONLY` / `GENERATOR_EXISTS` / `VALIDATED_IN_RESOLVE` |

## Packages

- `resolve_template.cli` — `new`, `doctor`, `inspect`, `resolve-build`
- `resolve_template.doctor` — Python / ffmpeg / Resolve diagnostics
- `resolve_template.inspect_drp` — ZIP listing; do not require well-formed XML
- `resolve_template.story` — YAML load / validate
- `resolve_template.resolve.api` — `scriptapp("Resolve")`
- `resolve_template.resolve.roundtrip` — create / import / append / export

## Official API map (21.1)

See `resolve_scripting.md` for signatures. Short map:

```
Resolve
  GetProjectManager()
    CreateProject / LoadProject / SaveProject / CloseProject
    ExportProject / ImportProject          ← genuine .drp
    ArchiveProject / RestoreProject        ← not .drp
  Project
    GetMediaPool / GetSetting / SetSetting / GetTimelineByIndex
  MediaPool
    ImportMedia / AddSubFolder / CreateEmptyTimeline
    AppendToTimeline / CreateTimelineFromClips / RelinkClips
  Timeline
    AddMarker / GetItemListInTrack / SetSetting / AddTrack
    InsertTitleIntoTimeline("Text")        ← generator; displayed text unproven
    Export(...)                            ← DRT/XML/AAF, not .drp
  TimelineItem
    AddTransition / GetType                ← Phase 7 Cross Dissolve
```

## Validation labels

| Label | Meaning |
|-------|---------|
| `INSPECT_ONLY` | Read a real `.drp`; no claim we can write one |
| `GENERATOR_EXISTS` | Code path exists; Resolve missing or round-trip unproven |
| `VALIDATED_IN_RESOLVE` | Export + re-import succeeded on a real install |

## Local machine notes (2026-09-18)

- Resolve Studio 21.1.0 is installed and scripting answered.
- Current user project at probe time was `Copy of paris` — leave it alone.
- Bundled `ResolvePython` is 3.14; Homebrew CPython 3.14 also exists. Prefer the connection method that `scriptapp` actually returns, and record it in Phase 2 notes.
