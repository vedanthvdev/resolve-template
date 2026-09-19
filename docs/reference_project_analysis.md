# Reference project analysis

Inspected **2026-09-18** on this laptop. Source file:

`/Users/chintuvedanth/Downloads/paris.drp`

The binary is **not** committed (personal media paths, 3.8 MB). Structural facts below are enough to skip re-opening the ZIP unless the export version changes.

Live Resolve counterpart (read-only): database projects `paris` and `Copy of paris`. Open project at inspect time: **`Copy of paris`**. Nothing was imported, exported, or saved.

## Status

| Item | Result |
|------|--------|
| Offline ZIP inspect | Done |
| Naive XML parse | Fails (binary blobs) |
| Live scripting connected | Yes (Resolve Studio 21.1.0) |
| Phase 2 `ExportProject` round-trip | **Validated separately on 2026-09-18** |

## Ground-truth header

Every XML member starts with:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!--DbAppVer="21.1.0.0014" DbPrjVer="17"-->
```

Matches app bundle:

- Path: `/Applications/DaVinci Resolve/DaVinci Resolve.app`
- `CFBundleShortVersionString`: `21.1.0`
- `CFBundleVersion`: `21.1.00014`

Root of `project.xml`:

```xml
<SM_Project DbId="6e69db33-b695-4c1b-b375-fdaade7602f9">
```

## Archive layout

`file(1)`: Zip archive, deflate, ZIP v2.0. Empty ZIP comment. **12 members, all `.xml`.**

| Member | Uncompressed | Compressed | Role |
|--------|-------------:|-----------:|------|
| `project.xml` | 1,728,085 | 743,896 | Project settings / lockable blobs |
| `MediaPool/Master/MpFolder.xml` | 1,431,206 | 302,765 | Entire media pool (no sub-bins in this export) |
| `SeqContainer/068209f6-066c-4c85-bbf5-1909495b396e.xml` | 775,032 | 240,530 | Timeline |
| `SeqContainer/100934f0-18f1-4f1a-976f-222e3a8c8bd8.xml` | 54,507 | 6,757 | Timeline (smallest) |
| `SeqContainer/135e1bf7-2819-4222-8243-5aa6a51cda85.xml` | 947,641 | 386,286 | Timeline |
| `SeqContainer/3387c7e1-1a42-4891-9f6d-bd907eb3fc49.xml` | 486,054 | 179,765 | Timeline |
| `SeqContainer/5efeb38f-790f-4e02-a697-d110c94a56d7.xml` | 87,344 | 39,646 | Timeline |
| `SeqContainer/78988156-eb66-4194-81d6-5bb319b03d72.xml` | 2,599,218 | 890,663 | Timeline (largest) |
| `SeqContainer/978a2fb6-0f5e-4f21-8065-352db92cc341.xml` | 2,570,094 | 875,670 | Timeline |
| `SeqContainer/a6d80cad-37ec-4e7e-aae5-a825718f4c44.xml` | 1,649,491 | 299,928 | Timeline |
| `SeqContainer/e40002d4-4e76-4ea1-aa6c-c30624c7421c.xml` | 204,098 | 34,923 | Timeline |
| `Gallery.xml` | 8,919 | 1,210 | Gallery stills |

**9 `SeqContainer` files = 9 timelines** in the live project. Filename is the timeline UUID, not the display name.

No SQLite, no media files, no LUTs inside this `.drp`.

## Live project (Copy of paris)

Read via Resolve scripting / MCP. Do not treat this as the Phase 2 POC.

### Project settings (relevant subset)

- Resolution: 1920×1080
- `timelineFrameRate`: **30** (not 25 — Phase 2 spec is 25 fps)
- Color: `davinciYRGBColorManagedv2`, timeline Rec.709 (Scene), output Rec.709 Gamma 2.4
- Sample rate: 48000
- `projectMediaLocation`: `/Users/chintuvedanth/DaVinci Resolve Media`

### Timelines (index order)

1. Vazhithunaiye
2. Anthu Inthu
3. Mental Manadhil
4. Piya O re piya
5. Interview
6. ranjith test
7. **full** (current at inspect time)
8. cursor
9. MOVIE

### Media Pool Master (no subfolders)

222 clips:

| Type | Count |
|------|------:|
| Video + Audio | 180 |
| Audio | 13 |
| Still | 13 |
| Timeline | 9 |
| Video | 7 |

213 clips had a `file_path`. Typical video: `/Users/chintuvedanth/Desktop/paris/.../*.MP4`. Audio/stills also under Downloads and Desktop/vlog.

### Timeline `full` (id `404e3e97-15fe-4ecd-b4eb-47821e5ec534`)

- Start frame 0, end frame **12785**, start TC `00:00:00:00` (~7:06 at 30 fps)
- **423** timeline items
- **0** timeline markers
- 10 video tracks, 10 audio tracks

Item counts:

| Track | Items | First item notes |
|-------|------:|------------------|
| V1 | 124 | `earth.png` still, then camera clips |
| V2 | 53 | Generator `Digital Glitch` — **no media pool id** |
| V3 | 13 | stills |
| V4 | 3 | **Text+** — no media pool id |
| V5 | 1 | PNG still |
| V6 | 1 | Text+ |
| V7 | 0 | empty |
| V8 | 22 | camera `a70326.MP4` |
| V9 | 5 | camera `a70327.MP4` |
| V10 | 2 | generator `Fade On` — no media pool id |
| A1 | 105 | camera-embedded audio |
| A2 | 30 | |
| A3 | 10 | |
| A4 | 2 | SFX mp3 |
| A5 | 17 | `Airplane Sound Effect.mp3` from start |
| A6 | 4 | cinematic SFX |
| A7 | 0 | empty |
| A8 | 24 | linked with V8 |
| A9 | 3 | |
| A10 | (few) | |

`detect_missing_media` on `full`: **346 missing**, **present_count** implied by remainder. Example missing path: `/Users/chintuvedanth/Desktop/paris/drone/DJI_20260531101625_0086_D.MP4` (`file_exists: false`). Relink is a Phase 6 concern; this fixture already shows why packages must ship `Placeholder_Media/` beside the `.drp`.

## What this project is useful for

- Real 21.1 export layout and version stamps
- Proof that timelines are separate XML files keyed by UUID
- Proof that titles/generators exist as timeline items without media-pool items (Phase 7)
- Proof that media stays on disk and goes offline easily

## What this project is **not**

- Not a 25 fps / 75-frame one-clip POC
- Not a clean bin layout (`01_VIDEO_PLACEHOLDERS` …)
- Not a source to hand-edit into a template

The Phase 2 test used disposable projects and restored `Copy of paris`; neither reference project was mutated.
