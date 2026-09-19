# Resolve generation strategy

## Preferred path (unchanged, now API-backed)

1. Author `story.yaml` (human or AI).
2. Generate placeholder media with deterministic names.
3. Drive Resolve scripting:
   - `CreateProject`
   - `ImportMedia` for each file
   - `CreateEmptyTimeline` + `AppendToTimeline` with `mediaType` / `trackIndex` / `recordFrame`
   - later: `AddSubFolder`, `AddMarker`
4. `ProjectManager.ExportProject(name, path)` → native `.drp`.
5. Package ZIP with `Placeholder_Media/` + tracker + honest README.
6. Round-trip: `ImportProject` and assert structure.

## Rejected path (reinforced by paris.drp)

The export is ZIP+XML with **binary `FieldsBlob` nodes**. It is not a clean schema. Hand-writing or mutating members will not be treated as a genuine project.

Also reject:

- Renaming a `.zip` of invented XML to `.drp`
- Using `Timeline.Export` (`.drt` / FCPXML) and calling it a Resolve project
- Using `ArchiveProject` as the user-facing template (it is a media archive)

## Phase 2 recipe (validated 2026-09-18)

Disposable project only.

1. Create project (name prefix `_rt_` or `_mcp_`).
2. Set timeline/project fps to **25** (paris was 30 — do not inherit).
3. Import `001_OPENING_PLACEHOLDER.mp4` and `VO_01_OPENING_PLACEHOLDER.wav`.
4. `CreateEmptyTimeline("PRE_EDIT_MAIN")`.
5. Append video: `mediaType=1`, `trackIndex=1`, `startFrame=0`, `endFrame=75` (exclusive), `recordFrame=0`.
6. Append audio: `mediaType=2`, `trackIndex=1`, same frames.
7. `ExportProject` to a temp `.drp`.
8. `ImportProject` under a new name; assert clip names, tracks, duration 75 @ 25 fps.
9. Delete disposable projects.

Resolve 21.1 treats `endFrame` as **exclusive**. The first probe with 74 produced 74-frame items; 75 produced the required 75-frame items.

## Phase 3 recipe (validated 2026-09-19)

Same disposable-project path as Phase 2, with ten contiguous V1 clips and **no audio**.

1. Generate `001_SHOT_01_PLACEHOLDER.mp4` … `010_SHOT_10_PLACEHOLDER.mp4` (25 frames each).
2. `ImportMedia` the ten paths.
3. `CreateEmptyTimeline("PRE_EDIT_MAIN")`.
4. `AppendToTimeline` with `recordFrame` 0, 25, … 225 and exclusive `endFrame=25`.
5. Export, re-import, assert names, starts, durations, and no gaps.
6. Delete disposable projects.

A single silent bed was skipped on purpose so a missing or overlapping V1 clip cannot hide under A1.

## Phase 4 recipe (validated 2026-09-19)

Same disposable-project path, keeping the ten V1 shots and adding generated silence only:

1. Generate `VO_01_BED_PLACEHOLDER.wav` (A1, 250 frames), `MUSIC_01_BED_PLACEHOLDER.wav` (A2, 250 frames), and two 25-frame SFX hits on A3.
2. `CreateEmptyTimeline("PRE_EDIT_MAIN")`.
3. `AddTrack("audio")` until three audio tracks exist.
4. `AppendToTimeline` with `mediaType=2` and `trackIndex` 1/2/3.
5. Export, re-import, assert per-track counts and names.
6. Delete disposable projects.

## Phase 5 recipe (validated 2026-09-19)

1. `AddSubFolder` for `01_VIDEO_PLACEHOLDERS` … `06_REFERENCE`.
2. `MoveClips` video into 01; VO/music/SFX into 02–04 by `role`. Leave 05/06 empty.
3. After the timeline exists, `AddMarker` from the story list.
4. Export, re-import, assert bin names, clip membership, marker frames and names.

## Phase 6 recipe (validated 2026-09-19)

1. Write `shot_tracker.csv` and `timeline_map.md` beside `Placeholder_Media/`.
2. README states `VALIDATED_IN_RESOLVE` only if `ExportProject` ran; otherwise `GENERATOR_EXISTS` and no `.drp`.
3. After re-import, `RelinkClips(all media-pool items, Placeholder_Media/)`.
4. Assert each clip `File Path` is inside that folder and the file exists.

## Relink lesson from paris

`full` had **346** timeline items whose `file_path` did not exist on disk. A `.drp` without sibling media is expected to go offline. Phase 6 must keep media next to the project and document one-folder relink.

## Titles / generators (Phase 7)

Do not reverse-engineer SeqContainer XML. Shipping path:

1. `AddTransition` Cross Dissolve for edit dissolves and fade from/to black.
2. Generate frozen title-card MP4s and `AppendToTimeline` on V2.
3. Do not author Fusion comps. `InsertTitleIntoTimeline("Text")` exists but the displayed string is unproven.

## Phase coupling

- Phase 1: **documented** (this pass)
- Phase 2: one-clip export/import — **validated**
- Phase 3: ten sequential V1 clips — **validated**
- Phase 4: A1 VO / A2 music / A3 SFX — **validated**
- Phase 5: bins + markers — **validated**
- Phase 6: full package + one-folder relink — **validated**
- Phase 7: transitions + generated title cards — **validated**
- Phase 8: canonical AI/human `story.yaml` workflow — **validated**
