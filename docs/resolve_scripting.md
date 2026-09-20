# Resolve scripting notes

Verified **2026-09-18** against **DaVinci Resolve Studio 21.1.0** on this Mac, with the app running and external scripting responding.

**Phase 2 `ExportProject` + re-import passed on 2026-09-18.**

## Local install

| Item | Value |
|------|--------|
| App | `/Applications/DaVinci Resolve/DaVinci Resolve.app` |
| Version | 21.1.0 (build 21.1.00014) |
| Scripting docs / module | `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/` |
| Python stub (source of truth) | `.../Scripting/DaVinciResolveScript.pyi` (Last Updated in README: 31 Aug 2026) |
| Loader | `.../Scripting/Modules/DaVinciResolveScript.py` |
| Fusion lib | `/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so` |
| Bundled interpreter | `/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Applications/ResolvePython` (Python 3.14; `import DaVinciResolveScript` works without env vars) |

README: Preferences → System → General → External scripting = Local or Network. Studio listens on port **1144**.

External CPython still needs:

```sh
RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
```

Example connector: `Scripting/Examples/python_get_resolve.py`.

## Connect

```python
import DaVinciResolveScript as dvr
resolve = dvr.scriptapp("Resolve")
projectManager = resolve.GetProjectManager()
```

Live at inspect: `GetCurrentProject()` name **`Copy of paris`**, id `f0a5a901-a6f1-4a12-a20c-46cdc4735f6f`.

## ProjectManager — native `.drp`

Confirmed present (`project_capabilities`):

```python
projectManager.ExportProject(projectName: str, filePath: str, withStillsAndLUTs=True) -> bool
projectManager.ImportProject(filePath: str, projectName: str | None = None) -> bool
projectManager.CreateProject(name) -> Project
projectManager.LoadProject(name) -> Project
projectManager.SaveProject() -> bool
projectManager.CloseProject(project) -> bool
projectManager.DeleteProject(name) -> bool
projectManager.ArchiveProject(...)   # NOT a .drp
projectManager.RestoreProject(...)
```

Validated Phase 2 write path:

```text
CreateProject → (build) → SaveProject → ExportProject(name, "/path/out.drp")
→ ImportProject("/path/out.drp", "roundtrip_name") → assert timelines/clips
```

Use a **disposable** project name. Do not load or overwrite `paris`.

Cursor MCP wrappers (same APIs, optional dry-run): `project_manager` actions `export_project`, `import_project`, `safe_project_export`, `safe_project_import`. Disposable prefix documented as `_mcp_`.

## MediaPool — Phase 2–5

Confirmed present:

```python
mediaPool.ImportMedia([{"FilePath": path, "StartIndex"?: int, "EndIndex"?: int}, ...]) -> [MediaPoolItem]
mediaPool.AddSubFolder(folder, name) -> Folder
mediaPool.SetCurrentFolder(folder) -> bool
mediaPool.GetRootFolder() -> Folder
mediaPool.CreateEmptyTimeline(name) -> Timeline
mediaPool.CreateTimelineFromClips(name, clipInfos) -> Timeline
mediaPool.AppendToTimeline(clipInfos) -> [TimelineItem]
mediaPool.RelinkClips(clips, folderPath) -> bool
```

`AppendClipInfo` (from the `.pyi`):

| Key | Meaning |
|-----|---------|
| `mediaPoolItem` | required object |
| `startFrame` / `endFrame` | source trim |
| `mediaType` | **1 = video only, 2 = audio only** |
| `trackIndex` | destination track (1-based) |
| `recordFrame` | timeline position |

`CreateTimelineClipInfo` has `mediaPoolItem`, `startFrame`, `endFrame`, `recordFrame` (no `mediaType` / `trackIndex` in the stub). For V1+A1 placement, prefer empty timeline + two `AppendToTimeline` calls with `mediaType` + `trackIndex`.

Observed on 21.1:

- `endFrame` is **exclusive**: use `startFrame=0`, `endFrame=75` for 75 frames.
- Typed-dict `ImportMedia([{"FilePath": ...}])` returned `None` at runtime despite
  the stub. The implementation uses the working path-list form one file at a
  time and verifies exactly one item with the expected name. Resolve builds are
  serialized because all callers share one running application.

## Timeline — settings, markers, export-not-drp

```python
timeline.SetSetting / GetSetting   # fps, resolution; useCustomSettings first
timeline.AddMarker(frameId, color, name, note, duration, customData=None)
timeline.GetItemListInTrack / GetTrackCount
timeline.Export(fileName, exportType, exportSubtype)  # AAF, EDL, FCPXML, DRT, OTIO — NOT .drp
```

`TimelineExportType` includes `EXPORT_DRT` (timeline, not project).

Titles: live `full` timeline has **Text+** items with `media_pool_item_id = None`. On 21.1.0, `InsertTitleIntoTimeline("Text")` creates a generator with no media-pool item; `"Text+"` returned `None`. Displayed title text is unproven, so Phase 7 ships generated title-card MP4s on V2 instead of Fusion.

`TimelineItem.AddTransition({type: "Cross Dissolve", category: "simple", position, alignment, duration})` is the shipping transition API. `SetFades` did not survive ExportProject / ImportProject.

## Project settings keys used by paris (30 fps HD)

Do not copy these blindly into the 25 fps POC. Useful keys:

- `timelineFrameRate` (float `30.0` on paris)
- `timelineResolutionWidth` / `Height` (`1920` / `1080`)
- `timelinePlaybackFrameRate`
- `timelineSampleRate` (`48000`)

Phase 2 spec wants **25 fps**, 75 frames, timeline name `PRE_EDIT_MAIN`.

Only `Project.SetSettings({"timelineFrameRate": 25.0})` was required. A combined update containing playback rate and resolution returned false, so settings are not batch-assumed.

## Phase 2 validated result

- Generated video: black H.264 MP4, 1280×720, 25 fps, exactly 75 frames
- Generated audio: mono PCM WAV, 48 kHz, 144,000 silent samples (3 seconds)
- Timeline: `PRE_EDIT_MAIN`
- Re-import: one 75-frame item on V1 and one 75-frame item on A1 with expected names
- Exported `.drp`: 23,542-byte ZIP from `ProjectManager.ExportProject`
- Outer package: `output/poc_one_clip.zip`
- Cleanup: both disposable projects removed and `Copy of paris` restored

## What was live-probed (do not repeat unless version changes)

- `project_manager.list` — many user projects including `paris` and `Copy of paris`
- `project_capabilities` — `ExportProject` / `ImportProject` true
- `project_settings_snapshot` — settings + 9 timelines
- `timeline.list` — names above
- `timeline.probe_timeline_structure` on `full` — 423 items, track counts
- `media_pool.probe_media_pool` — Master, 222 clips, 0 subfolders
- `timeline.detect_missing_media` — 346 missing on `full`

## Phase 3 validated result

- Ten generated 25-frame black MP4s on V1, shot numbers 1–10, names `001_SHOT_01_PLACEHOLDER.mp4` … `010_SHOT_10_PLACEHOLDER.mp4`
- Starts 0, 25, … 225; no gaps; timeline coverage 250 frames at 25 fps
- No A1 clip (video-only so order bugs stay visible)
- `AppendToTimeline` accepted a list of ten clip-info dicts with explicit `recordFrame`
- Exported `.drp`: ZIP with one `SeqContainer`
- Cleanup: disposable projects removed; `Copy of paris` restored

## Phase 4 validated result

- A1: 1 silent VO bed, 250 frames
- A2: 1 silent music bed, 250 frames
- A3: 2 silent SFX hits at frames 50 and 175
- `Timeline.AddTrack("audio")` used to create A2 and A3 on a new timeline
- No copyrighted or real-world audio files

## Phase 5 validated result

- Bins `01_VIDEO_PLACEHOLDERS` … `06_REFERENCE` survived `ExportProject` / `ImportProject`
- Video clips in 01; VO/music/SFX in 02–04; 05 and 06 empty
- Four timeline markers: OPENING, SFX_HIT_1, MIDPOINT, LAST_SHOT

## Phase 6 validated result

- Package ZIP: `.drp` + `Placeholder_Media/` + `shot_tracker.csv` + `timeline_map.md` + honest README
- `RelinkClips` to the package’s persistent `Placeholder_Media/` folder; 14 clips online
- Tracker shots 1–10 match placeholder filenames

## Phase 7 validated result

- Cross Dissolve via `AddTransition` survived export/re-import (`GetType() == "transition"`)
- Fade from/to black implemented as Cross Dissolve on the first clip start (`alignment=right`) and last clip end (`alignment=right`)
- Title card: generated static MP4 with visibly rendered text on V2 (not Fusion,
  not `InsertTitleIntoTimeline`)
- Source handles: only the head/tail frames required by each transition

## Phase 8 validated result

- Canonical `examples/full_story/story.yaml` uses the complete safe subset
- JSON Schema validation runs before semantic validation and reports field paths
- Re-import matched 10 labeled, color-coded V1 clips, 4 audio clips, 5 renamed
  bins, 4 markers, 3 transition roles, and 1 generated title card on V2
- Timeline remained in Master; tracks remained named Picture, Titles, VO,
  Music, and SFX
- `TimelineItem.SetName` persisted clip labels through export/re-import; media-pool
  filenames stayed as generated files for relink
- All 15 media items relinked to the persistent package media folder
- `examples/baby_shower/story.yaml` later proved a 28-shot event-film cut on the
  same path: 150s picture, 1.2s fade tail, 15 A1–A3 beds, 3 titles, 10 markers,
  and 46 relinked media items

## Phase 9 validated result

- A generated MP4 with silent stereo AAC appended picture to V1 and production
  audio to named A4
- `Timeline.SetClipsLinked([video_item, audio_item], True)` persisted through
  export/re-import
- `TimelineItem.GetLinkedItems()` proved the V1/A4 relationship after re-import
- Video-only placeholders and independent A1–A3 beds remained unchanged

## Honesty

Phase 2 output can now be labeled `VALIDATED_IN_RESOLVE` only when this live export/re-import validation completes. Offline generation remains `GENERATOR_EXISTS`.
