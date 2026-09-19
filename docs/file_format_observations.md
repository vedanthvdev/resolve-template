# File format observations

**Label:** `INSPECT_ONLY`  
**Source:** `/Users/chintuvedanth/Downloads/paris.drp` (Resolve 21.1.0 export)  
**Date:** 2026-09-18

## Rules

1. Treat a real Resolve export as ground truth.
2. Do not reverse-engineer a write path. Official write path is `ProjectManager.ExportProject`.
3. Do not hand-write or patch these XML members and call the result a native `.drp`.

## Container

- Extension `.drp` = ZIP (deflate).
- Members are XML only in this sample.
- No SQLite / no `.db` / no embedded essence.
- Gallery stills are referenced in `Gallery.xml`, not stored as images in the ZIP (this sample is tiny: 8.9 KB).

## Member map

```
project.xml
MediaPool/Master/MpFolder.xml
SeqContainer/<timeline-uuid>.xml   # one per timeline
Gallery.xml
```

If bins existed, expect additional `MediaPool/<BinName>/...` paths. This export has **only Master**.

## XML shape (regex tag counts, not a schema)

`project.xml` is **not well-formed** for `xml.etree.ElementTree`. Parse error: `not well-formed (invalid token): line 9197, column 11`. Cause: `FieldsBlob` and similar nodes hold binary / UCS-2-looking blobs after a short XML wrapper.

Do **not** feed the whole file to a strict XML parser. Inspect should:

1. Confirm ZIP
2. List members + sizes
3. Read the `DbAppVer` / `DbPrjVer` comment from the first ~200 bytes
4. Optionally regex-count tags

High-frequency tags (illustrative, `project.xml`):

- `Element`, `FieldsBlob`, `DbSavedTime`, `BlobOwner`, `Sm2TiItemLockableBlob`

`MpFolder.xml` (pool):

- `Clip` (~393), `Name`, `MediaMetadata`, `UniqueMediaPoolItemId` (222 — matches live clip count)
- `MarkIn` / `MarkOut` (video and audio) on every pool item
- `MpFolder` (222) — folder records nested in Master

Each `SeqContainer/*.xml` (timeline):

- Repeated per timeline item: `PrettyType`, `Start`, `Duration`, `LinkedItemSync`, `WasDisbanded`, `MarkersBA`, `UiMemento`, `PriorityIndex`, `EffectFiltersBA`, `ImportExportMetadataBA`, `RenderTextEnabled`
- Item counts scale with timeline size (smallest ~24 `Start` tags, largest ~485)

## Stable vs fragile

**Likely stable across 21.x exports**

- ZIP container
- `DbAppVer` / `DbPrjVer` comment
- Split: project + MediaPool tree + SeqContainer UUID files + Gallery
- Media referenced by absolute filesystem path, not packaged

**Fragile / do not invent**

- `FieldsBlob` binary layout
- Lockable blob types (`Sm2TiItemLockableBlob`, `Sm2MpItemLockableBlob`)
- Exact child order / `DbPrjVer` meaning
- Mapping SeqContainer UUID → display name without Resolve

## Implications for this repo

- Offline `inspect` is ZIP + header + member list. That is enough for Phase 1.
- A genuine writable `.drp` still requires Resolve `ExportProject`.
- `Timeline.Export` (DRT/FCPXML/AAF) is a **different** file type. Do not confuse `.drt` with `.drp`.
- `ArchiveProject` packs media/cache. Also not a `.drp`.
