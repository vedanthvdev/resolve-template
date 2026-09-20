"""Resolve round-trip build entrypoints for one-clip and multi-clip stories."""

from __future__ import annotations

import fcntl
import shutil
import zipfile
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from resolve_template.package import write_package_sidecars
from resolve_template.placeholders import (
    generate_placeholder_audio,
    generate_placeholder_title_still,
    generate_placeholder_video,
)
from resolve_template.resolve.api import get_resolve
from resolve_template.story import (
    audio_clips,
    audio_display_name,
    bin_mapping,
    bins,
    load_story,
    markers,
    source_handles,
    title_display_name,
    titles,
    track_index,
    transitions,
    video_clips,
    video_display_name,
)

DISPOSABLE_PROJECT_PREFIX = "_rt_resolve_template_"
PROTECTED_PROJECT_NAMES = {"paris", "Copy of paris"}
RESOLVE_LOCK_PATH = Path("/tmp/resolve-template-resolve.lock")
PLACEHOLDER_VIDEO_COLORS = {
    "Blue": "0x315c8a",
    "Green": "0x3f7d5a",
    "Yellow": "0xa8842f",
    "Pink": "0x8f4f70",
    "Purple": "0x624f82",
}
TRACK_NAMES = {
    ("video", 1): "Picture",
    ("video", 2): "Titles",
    ("audio", 1): "VO",
    ("audio", 2): "Music",
    ("audio", 3): "SFX",
    ("audio", 4): "Production",
}


def resolve_build(
    story_path: Path,
    *,
    output: Path,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Build a placeholder package from story.yaml.

    When Resolve is unavailable, write a GENERATOR_EXISTS package that never
    pretends a native .drp was exported.
    """
    story_path = Path(story_path)
    output = Path(output)
    story = load_story(story_path)

    if output.exists():
        if not overwrite:
            raise FileExistsError(f"Output already exists: {output}.")
        shutil.rmtree(output)
    output.mkdir(parents=True)

    package_zip = output.with_suffix(".zip")
    if package_zip.exists():
        if not overwrite:
            raise FileExistsError(f"Package already exists: {package_zip}.")
        package_zip.unlink()

    timeline_spec = story["timeline"]
    fps = int(story["fps"])
    width = int(story["width"])
    height = int(story["height"])
    videos = video_clips(story)
    audios = audio_clips(story)
    title_specs = titles(story)
    transition_specs = transitions(story)
    bin_names = bins(story)
    bin_destinations = bin_mapping(story)
    marker_specs = markers(story)
    video_handles = source_handles(story)
    summary = _story_summary(story)

    media_dir = output / "Placeholder_Media"
    video_paths = [
        generate_placeholder_video(
            media_dir,
            filename=clip["filename"],
            fps=fps,
            duration_frames=max(
                2,
                (
                    int(clip["duration_frames"])
                    + video_handles[int(clip["shot"])]["head"]
                    + video_handles[int(clip["shot"])]["tail"]
                ),
            ),
            color=PLACEHOLDER_VIDEO_COLORS[str(clip["color"])],
            linked_audio=bool(clip["linked_audio"]),
            width=width,
            height=height,
        )
        for clip in videos
    ]
    audio_paths = [
        generate_placeholder_audio(
            media_dir,
            filename=clip["filename"],
            fps=fps,
            duration_frames=int(clip["duration_frames"]),
        )
        for clip in audios
    ]
    title_paths = [
        generate_placeholder_title_still(
            media_dir,
            filename=title["filename"],
            text=str(title.get("text") or "TITLE"),
            fps=fps,
            duration_frames=int(title["duration_frames"]),
            width=width,
            height=height,
        )
        for title in title_specs
    ]
    (output / "story.snapshot.yaml").write_text(
        story_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    write_package_sidecars(output, story)

    resolve = get_resolve()
    if resolve is None:
        (output / "README.md").write_text(_package_readme(False), encoding="utf-8")
        _write_package_zip(output, package_zip)
        return {
            "status": "GENERATOR_EXISTS",
            "output": str(output.resolve()),
            "timeline": timeline_spec.get("name"),
            "drp": None,
            "package_zip": str(package_zip.resolve()),
            "summary": summary,
            "note": "DaVinci Resolve scripting not available; no ExportProject ran.",
        }

    drp_path = output / "project.drp"
    with _resolve_lock():
        validation = _resolve_roundtrip(
            resolve,
            project_name=f"{DISPOSABLE_PROJECT_PREFIX}{uuid4().hex[:10]}",
            imported_name=f"{DISPOSABLE_PROJECT_PREFIX}import_{uuid4().hex[:10]}",
            timeline_name=timeline_spec["name"],
            fps=fps,
            width=width,
            height=height,
            videos=videos,
            audios=audios,
            titles=title_specs,
            transitions=transition_specs,
            video_paths=video_paths,
            audio_paths=audio_paths,
            title_paths=title_paths,
            bin_names=bin_names,
            bin_destinations=bin_destinations,
            marker_specs=marker_specs,
            video_handles=video_handles,
            media_dir=media_dir,
            drp_path=drp_path,
        )
    (output / "README.md").write_text(_package_readme(True), encoding="utf-8")
    _write_package_zip(output, package_zip)
    return {
        "status": "VALIDATED_IN_RESOLVE",
        "output": str(output.resolve()),
        "timeline": timeline_spec["name"],
        "drp": str(drp_path.resolve()),
        "package_zip": str(package_zip.resolve()),
        "summary": summary,
        "validation": validation,
    }


@contextmanager
def _resolve_lock() -> Iterator[None]:
    """Serialize access to Resolve's single scripting process."""
    with RESOLVE_LOCK_PATH.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _story_summary(story: dict[str, Any]) -> dict[str, Any]:
    fps = float(story["fps"])
    picture_frames = int(story["timeline"]["duration_frames"])
    fade_tail_frames = max(
        (
            int(item["duration_frames"])
            for item in transitions(story)
            if item.get("kind") == "fade_to_black"
        ),
        default=0,
    )
    duration_frames = picture_frames + fade_tail_frames
    audios = audio_clips(story)
    return {
        "timeline_name": story["timeline"]["name"],
        "fps": fps,
        "width": int(story["width"]),
        "height": int(story["height"]),
        "duration_frames": duration_frames,
        "duration_seconds": duration_frames / fps,
        "picture_duration_frames": picture_frames,
        "picture_duration_seconds": picture_frames / fps,
        "fade_tail_frames": fade_tail_frames,
        "video_clips": len(video_clips(story)),
        "linked_video_clips": sum(
            1 for clip in video_clips(story) if clip["linked_audio"]
        ),
        "audio_clips": len(audios),
        "audio_by_track": {
            label: sum(1 for clip in audios if clip["track"] == label)
            for label in ("A1", "A2", "A3")
        },
        "title_cards": len(titles(story)),
        "transitions": [item["kind"] for item in transitions(story)],
    }


def _resolve_roundtrip(
    resolve: Any,
    *,
    project_name: str,
    imported_name: str,
    timeline_name: str,
    fps: int,
    width: int,
    height: int,
    videos: list[dict[str, Any]],
    audios: list[dict[str, Any]],
    titles: list[dict[str, Any]],
    transitions: list[dict[str, Any]],
    video_paths: list[Path],
    audio_paths: list[Path],
    title_paths: list[Path],
    bin_names: list[str],
    bin_destinations: dict[str, str],
    marker_specs: list[dict[str, Any]],
    video_handles: dict[int, dict[str, int]],
    media_dir: Path,
    drp_path: Path,
) -> dict[str, Any]:
    project_manager = resolve.GetProjectManager()
    original_name, stale_projects_deleted = _prepare_project_manager(project_manager)
    disposable_names = (project_name, imported_name)
    media_paths = [str(path.resolve()) for path in [*video_paths, *audio_paths, *title_paths]]

    try:
        project = project_manager.CreateProject(project_name)
        if project is None:
            raise RuntimeError(f"Resolve could not create disposable project {project_name}")
        if not project.SetSettings({"timelineFrameRate": float(fps)}):
            raise RuntimeError(f"Resolve rejected timelineFrameRate={fps}")
        _apply_timeline_resolution(project, width, height)

        media_pool = project.GetMediaPool()
        imported = _import_media(media_pool, media_paths)
        clips = {item.GetName(): item for item in imported}
        missing = [Path(path).name for path in media_paths if Path(path).name not in clips]
        if missing:
            raise RuntimeError(f"Resolve import returned unexpected clips, missing {missing}")
        _apply_clip_metadata(clips, videos)
        if bin_names:
            _organize_bins(
                media_pool,
                clips,
                videos,
                audios,
                titles,
                bin_names,
                bin_destinations,
            )
        root_folder = media_pool.GetRootFolder()
        if not media_pool.SetCurrentFolder(root_folder):
            raise RuntimeError("Resolve could not restore the Master media-pool folder")

        timeline = media_pool.CreateEmptyTimeline(timeline_name)
        if timeline is None or not project.SetCurrentTimeline(timeline):
            raise RuntimeError(f"Resolve could not create timeline {timeline_name}")
        _apply_timeline_format(timeline, width=width, height=height)
        _ensure_audio_tracks(timeline, audios, videos)
        _ensure_video_tracks(timeline, titles)
        _name_tracks(timeline)

        video_infos = [
            {
                "mediaPoolItem": clips[path.name],
                "startFrame": video_handles[int(clip["shot"])]["head"],
                "endFrame": (
                    video_handles[int(clip["shot"])]["head"]
                    + int(clip["duration_frames"])
                ),
                "mediaType": 1,
                "trackIndex": 1,
                "recordFrame": int(clip["start_frame"]),
            }
            for clip, path in zip(videos, video_paths, strict=True)
        ]
        appended_video = media_pool.AppendToTimeline(video_infos)
        if appended_video is None or len(appended_video) != len(videos):
            raise RuntimeError(
                f"Resolve appended {0 if appended_video is None else len(appended_video)} "
                f"V1 items instead of {len(videos)}"
            )
        _apply_timeline_labels(appended_video, videos)

        linked_video_indexes = [
            index for index, clip in enumerate(videos) if clip["linked_audio"]
        ]
        if linked_video_indexes:
            production_audio_infos = [
                {
                    "mediaPoolItem": clips[video_paths[index].name],
                    "startFrame": video_handles[int(videos[index]["shot"])]["head"],
                    "endFrame": (
                        video_handles[int(videos[index]["shot"])]["head"]
                        + int(videos[index]["duration_frames"])
                    ),
                    "mediaType": 2,
                    "trackIndex": 4,
                    "recordFrame": int(videos[index]["start_frame"]),
                }
                for index in linked_video_indexes
            ]
            appended_production = media_pool.AppendToTimeline(production_audio_infos)
            if appended_production is None or len(appended_production) != len(
                linked_video_indexes
            ):
                raise RuntimeError("Resolve did not append the expected production audio")
            for video_index, audio_item in zip(
                linked_video_indexes, appended_production, strict=True
            ):
                _set_timeline_item_name(
                    audio_item,
                    f"{video_display_name(videos[video_index])} (cam)",
                    videos[video_index]["filename"],
                )
                if not timeline.SetClipsLinked(
                    [appended_video[video_index], audio_item], True
                ):
                    raise RuntimeError(
                        f"Resolve could not link production audio for "
                        f"{videos[video_index]['filename']}"
                    )

        if audios:
            audio_infos = [
                {
                    "mediaPoolItem": clips[path.name],
                    "startFrame": 0,
                    "endFrame": int(clip["duration_frames"]),
                    "mediaType": 2,
                    "trackIndex": track_index(clip["track"]),
                    "recordFrame": int(clip["start_frame"]),
                }
                for clip, path in zip(audios, audio_paths, strict=True)
            ]
            appended_audio = media_pool.AppendToTimeline(audio_infos)
            if appended_audio is None or len(appended_audio) != len(audios):
                raise RuntimeError("Resolve did not append the expected audio clips")
            for item, clip in zip(appended_audio, audios, strict=True):
                _set_timeline_item_name(
                    item, audio_display_name(clip), clip["filename"]
                )

        if titles:
            title_infos = [
                {
                    "mediaPoolItem": clips[path.name],
                    "startFrame": 0,
                    "endFrame": int(title["duration_frames"]),
                    "mediaType": 1,
                    "trackIndex": track_index(title["track"]),
                    "recordFrame": int(title["start_frame"]),
                }
                for title, path in zip(titles, title_paths, strict=True)
            ]
            appended_titles = media_pool.AppendToTimeline(title_infos)
            if appended_titles is None or len(appended_titles) != len(titles):
                raise RuntimeError("Resolve did not append the expected title stills")
            for item, title in zip(appended_titles, titles, strict=True):
                _set_timeline_item_name(
                    item, title_display_name(title), title["filename"]
                )

        _apply_transitions(timeline, videos, transitions)

        for marker in marker_specs:
            if not timeline.AddMarker(
                int(marker["frame"]),
                marker["color"],
                str(marker["name"]),
                str(marker.get("note") or ""),
                int(marker["duration_frames"]),
            ):
                raise RuntimeError(f"Resolve rejected marker {marker['name']}")

        project_manager.SaveProject()
        if not project_manager.ExportProject(project_name, str(drp_path.resolve()), False):
            raise RuntimeError("Resolve ExportProject returned false")
        if not drp_path.is_file() or not zipfile.is_zipfile(drp_path):
            raise RuntimeError("ExportProject did not create a ZIP-based .drp")

        project_manager.CloseProject(project)
        if not project_manager.ImportProject(str(drp_path.resolve()), imported_name):
            raise RuntimeError("Resolve ImportProject returned false")
        roundtrip_project = project_manager.LoadProject(imported_name)
        if roundtrip_project is None:
            raise RuntimeError("Resolve could not load the re-imported project")
        relinked = _relink_placeholder_media(roundtrip_project, media_dir)

        result = _validate_roundtrip(
            roundtrip_project,
            timeline_name=timeline_name,
            fps=fps,
            width=width,
            height=height,
            videos=videos,
            audios=audios,
            titles=titles,
            transitions=transitions,
            bin_names=bin_names,
            bin_destinations=bin_destinations,
            marker_specs=marker_specs,
            relinked=relinked,
        )
        result["stale_projects_deleted"] = stale_projects_deleted
        return result
    finally:
        current = project_manager.GetCurrentProject()
        if (
            current
            and current.GetName() in disposable_names
            and not project_manager.CloseProject(current)
        ):
            raise RuntimeError(f"Resolve could not close disposable project {current.GetName()}")
        _delete_projects(project_manager, disposable_names)
        if original_name and project_manager.LoadProject(original_name) is None:
            raise RuntimeError(f"Resolve could not restore original project {original_name}")


def _prepare_project_manager(project_manager: Any) -> tuple[str | None, list[str]]:
    current = project_manager.GetCurrentProject()
    original_name = current.GetName() if current else None
    if original_name in PROTECTED_PROJECT_NAMES:
        raise RuntimeError(
            f"Refusing to run while protected project {original_name!r} is current. "
            "Load a different project first."
        )
    if original_name and original_name.startswith(DISPOSABLE_PROJECT_PREFIX):
        if not project_manager.CloseProject(current):
            raise RuntimeError(f"Resolve could not close stale project {original_name}")
        original_name = None

    projects = project_manager.GetProjectListInCurrentFolder() or []
    stale = [
        name
        for name in projects
        if name.startswith(DISPOSABLE_PROJECT_PREFIX) and name not in PROTECTED_PROJECT_NAMES
    ]
    _delete_projects(project_manager, stale)
    return original_name, stale


def _apply_timeline_resolution(project: Any, width: int, height: int) -> None:
    for key, value in (
        ("timelineResolutionWidth", width),
        ("timelineResolutionHeight", height),
    ):
        if project.SetSettings({key: float(value)}):
            continue
        if project.SetSettings({key: str(value)}):
            continue
        raise RuntimeError(f"Resolve rejected {key}={value}")


def _apply_timeline_format(timeline: Any, *, width: int, height: int) -> None:
    if not hasattr(timeline, "SetSetting"):
        raise RuntimeError("Resolve timeline does not expose SetSetting")
    for key, value in (
        ("useCustomSettings", "1"),
        ("timelineResolutionWidth", str(width)),
        ("timelineResolutionHeight", str(height)),
    ):
        if not timeline.SetSetting(key, value):
            raise RuntimeError(f"Resolve rejected timeline {key}={value}")


def _setting_int(settings: dict[str, Any], key: str) -> int:
    value = settings.get(key)
    if value in (None, ""):
        raise RuntimeError(f"Re-imported timeline is missing {key}")
    return int(float(value))


def _delete_projects(project_manager: Any, names: Iterable[str]) -> None:
    existing = set(project_manager.GetProjectListInCurrentFolder() or [])
    failures = [
        name for name in names if name in existing and not project_manager.DeleteProject(name)
    ]
    if failures:
        raise RuntimeError(f"Resolve could not delete disposable projects: {failures}")


def _organize_bins(
    media_pool: Any,
    clips: dict[str, Any],
    videos: list[dict[str, Any]],
    audios: list[dict[str, Any]],
    titles: list[dict[str, Any]],
    bin_names: list[str],
    bin_destinations: dict[str, str],
) -> None:
    root = media_pool.GetRootFolder()
    folders = {}
    for name in bin_names:
        folder = media_pool.AddSubFolder(root, name)
        if folder is None:
            raise RuntimeError(f"Resolve could not create bin {name}")
        folders[name] = folder

    grouped: dict[str, list[Any]] = {name: [] for name in bin_names}
    video_bin = bin_destinations.get("video")
    for clip in videos:
        if video_bin:
            grouped[video_bin].append(clips[clip["filename"]])
    for clip in audios:
        audio_bin = bin_destinations.get(str(clip["role"]))
        if audio_bin:
            grouped[audio_bin].append(clips[clip["filename"]])
    graphics_bin = bin_destinations.get("graphics")
    for title in titles:
        if graphics_bin:
            grouped[graphics_bin].append(clips[title["filename"]])
    for name, items in grouped.items():
        if items and not media_pool.MoveClips(items, folders[name]):
            raise RuntimeError(f"Resolve could not move clips into {name}")


def _apply_clip_metadata(
    clips: dict[str, Any],
    videos: list[dict[str, Any]],
) -> None:
    for clip in videos:
        item = clips[clip["filename"]]
        if not item.SetClipColor(str(clip["color"])):
            raise RuntimeError(f"Resolve could not color video clip {clip['filename']}")


def _apply_timeline_labels(items: list[Any], videos: list[dict[str, Any]]) -> None:
    for item, clip in zip(items, videos, strict=True):
        color = str(clip["color"])
        label = video_display_name(clip)
        _set_timeline_item_name(item, label, clip["filename"])
        if not item.SetClipColor(color):
            raise RuntimeError(f"Resolve could not color timeline clip {clip['filename']}")
        if not item.AddMarker(0, color, label, f"Shot {clip['shot']}", 1):
            raise RuntimeError(f"Resolve could not label timeline clip {clip['filename']}")


def _set_timeline_item_name(item: Any, name: str, context: str) -> None:
    setter = getattr(item, "SetName", None)
    if setter is None:
        raise RuntimeError(f"Resolve TimelineItem.SetName is unavailable for {context}")
    setter(name)
    actual = str(item.GetName())
    if actual != name:
        raise RuntimeError(
            f"Resolve could not name timeline clip {context} {name!r}, got {actual!r}"
        )


def _ensure_video_tracks(timeline: Any, titles: list[dict[str, Any]]) -> None:
    needed = max((track_index(title["track"]) for title in titles), default=1)
    while timeline.GetTrackCount("video") < needed:
        if not timeline.AddTrack("video"):
            raise RuntimeError("Resolve could not add a video track for title stills")


def _apply_transitions(
    timeline: Any,
    videos: list[dict[str, Any]],
    transition_specs: list[dict[str, Any]],
) -> None:
    items = _video_clip_items(timeline.GetItemListInTrack("video", 1) or [])
    if len(items) != len(videos):
        raise RuntimeError("Cannot apply transitions before V1 clips match the story")
    by_shot = {int(clip["shot"]): items[index] for index, clip in enumerate(videos)}

    for spec in transition_specs:
        kind = spec.get("kind")
        duration = int(spec.get("duration_frames") or 0)
        if kind in {None, "cut"}:
            continue
        if kind == "cross_dissolve":
            _add_simple_transition(
                by_shot[int(spec["after_shot"])],
                position="end",
                alignment="center",
                duration=duration,
            )
        elif kind == "fade_from_black":
            _add_simple_transition(
                by_shot[int(spec["shot"])],
                position="start",
                alignment="right",
                duration=duration,
            )
        elif kind == "fade_to_black":
            _add_simple_transition(
                by_shot[int(spec["shot"])],
                position="end",
                alignment="right",
                duration=duration,
            )
        else:
            raise RuntimeError(f"unhandled transition kind {kind}")


def _add_simple_transition(item: Any, *, position: str, alignment: str, duration: int) -> None:
    created = item.AddTransition(
        {
            "type": "Cross Dissolve",
            "category": "simple",
            "position": position,
            "alignment": alignment,
            "duration": duration,
        }
    )
    if created is None:
        raise RuntimeError(
            f"Resolve AddTransition Cross Dissolve returned None ({position}/{alignment})"
        )


def _item_type(item: Any) -> str:
    getter = getattr(item, "GetType", None)
    if getter is None:
        return "video"
    return str(getter() or "video")


def _video_clip_items(items: list[Any]) -> list[Any]:
    return [item for item in items if _item_type(item) != "transition"]


def _transition_items(items: list[Any]) -> list[Any]:
    return [item for item in items if _item_type(item) == "transition"]


def _ensure_audio_tracks(
    timeline: Any,
    audios: list[dict[str, Any]],
    videos: list[dict[str, Any]],
) -> None:
    needed = max((track_index(clip["track"]) for clip in audios), default=0)
    if any(clip["linked_audio"] for clip in videos):
        needed = max(needed, 4)
    while timeline.GetTrackCount("audio") < needed:
        if not timeline.AddTrack("audio"):
            raise RuntimeError("Resolve could not add an audio track for A2/A3 placeholders")


def _name_tracks(timeline: Any) -> None:
    for (track_type, index), name in TRACK_NAMES.items():
        if index > timeline.GetTrackCount(track_type):
            continue
        if not timeline.SetTrackName(track_type, index, name):
            raise RuntimeError(f"Resolve could not name {track_type} track {index} {name!r}")


def _import_media(media_pool: Any, media_paths: list[str]) -> list[Any]:
    imported = []
    for path in media_paths:
        result = media_pool.ImportMedia([path])
        if result is None or len(result) != 1:
            count = 0 if result is None else len(result)
            raise RuntimeError(f"Resolve imported {count} items for {Path(path).name}, expected 1")
        item = result[0]
        if item.GetName() != Path(path).name:
            raise RuntimeError(
                f"Resolve imported {item.GetName()!r} for {Path(path).name!r}"
            )
        imported.append(item)
    return imported


def _validate_roundtrip(
    project: Any,
    *,
    timeline_name: str,
    fps: int,
    width: int,
    height: int,
    videos: list[dict[str, Any]],
    audios: list[dict[str, Any]],
    titles: list[dict[str, Any]],
    transitions: list[dict[str, Any]],
    bin_names: list[str],
    bin_destinations: dict[str, str],
    marker_specs: list[dict[str, Any]],
    relinked: dict[str, Any] | None = None,
) -> dict[str, Any]:
    timelines = [
        project.GetTimelineByIndex(index) for index in range(1, project.GetTimelineCount() + 1)
    ]
    timeline = next((item for item in timelines if item.GetName() == timeline_name), None)
    if timeline is None:
        raise RuntimeError(f"Re-imported project has no timeline named {timeline_name}")
    root = project.GetMediaPool().GetRootFolder()
    master_timelines = [
        item.GetName() for item in (root.GetClipList() or []) if _looks_like_timeline(item)
    ]
    if timeline_name not in master_timelines:
        raise RuntimeError(f"Timeline {timeline_name} is not in the Master media-pool folder")

    settings = timeline.GetSettings()
    actual_fps = float(settings["timelineFrameRate"])
    raw_video_items = timeline.GetItemListInTrack("video", 1) or []
    video_items = _video_clip_items(raw_video_items)
    transition_items = _transition_items(raw_video_items)
    if actual_fps != float(fps):
        raise RuntimeError(f"Expected {fps} fps after re-import, got {actual_fps}")
    actual_width = _setting_int(settings, "timelineResolutionWidth")
    actual_height = _setting_int(settings, "timelineResolutionHeight")
    if actual_width != width or actual_height != height:
        raise RuntimeError(
            f"Expected {width}x{height} after re-import, got {actual_width}x{actual_height}"
        )
    if len(video_items) != len(videos):
        raise RuntimeError(f"Expected {len(videos)} V1 clips, got {len(video_items)}")

    video_names = [item.GetName() for item in video_items]
    video_starts = [int(item.GetStart()) for item in video_items]
    video_durations = [int(item.GetDuration()) for item in video_items]
    expected_names = [video_display_name(clip) for clip in videos]
    expected_starts = [int(clip["start_frame"]) for clip in videos]
    expected_durations = [int(clip["duration_frames"]) for clip in videos]
    if video_names != expected_names:
        raise RuntimeError(f"V1 names {video_names} do not match {expected_names}")
    if video_starts != expected_starts:
        raise RuntimeError(f"V1 starts {video_starts} do not match {expected_starts}")
    if video_durations != expected_durations:
        raise RuntimeError(f"V1 durations {video_durations} do not match {expected_durations}")
    shot_labels = []
    clip_colors = []
    for item, clip in zip(video_items, videos, strict=True):
        item_markers = item.GetMarkers() or {}
        label = next(
            (
                str(info.get("name"))
                for info in item_markers.values()
                if isinstance(info, dict) and info.get("name")
            ),
            "",
        )
        if label != str(clip["label"]):
            raise RuntimeError(
                f"Timeline clip {clip['filename']} label {label!r} "
                f"does not match {clip['label']!r}"
            )
        color = str(item.GetClipColor())
        if color != str(clip["color"]):
            raise RuntimeError(
                f"Timeline clip {clip['filename']} color {color!r} "
                f"does not match {clip['color']!r}"
            )
        shot_labels.append(label)
        clip_colors.append(color)

    gaps = [
        {
            "after": video_names[index],
            "expected_start": video_starts[index] + video_durations[index],
            "next_start": video_starts[index + 1],
        }
        for index in range(len(video_items) - 1)
        if video_starts[index] + video_durations[index] != video_starts[index + 1]
    ]
    if gaps:
        raise RuntimeError(f"V1 has gaps or overlaps: {gaps}")

    audio_by_track = _audio_items_by_track(timeline, audios)
    production_audio = _validate_production_audio(timeline, videos)
    picture_duration = video_starts[-1] + video_durations[-1] if video_items else 0
    fade_tail = max(
        (
            int(spec["duration_frames"])
            for spec in transitions
            if spec.get("kind") == "fade_to_black"
        ),
        default=0,
    )
    timeline_duration = int(timeline.GetEndFrame()) - int(timeline.GetStartFrame())
    expected_timeline_duration = picture_duration + fade_tail
    if timeline_duration != expected_timeline_duration:
        raise RuntimeError(
            f"Timeline duration {timeline_duration} does not match picture "
            f"{picture_duration} plus fade tail {fade_tail}"
        )

    result: dict[str, Any] = {
        "fps": actual_fps,
        "width": actual_width,
        "height": actual_height,
        "video_items_v1": len(video_items),
        "audio_items_a1": len(audio_by_track["A1"]["items"]),
        "audio_items_a2": len(audio_by_track["A2"]["items"]),
        "audio_items_a3": len(audio_by_track["A3"]["items"]),
        "audio_items_a4": len(production_audio["items"]),
        "audio_names_by_track": {
            track: data["names"] for track, data in audio_by_track.items()
        },
        "production_audio_names": production_audio["names"],
        "linked_production_audio": production_audio["linked"],
        "video_names": video_names,
        "video_starts": video_starts,
        "video_durations": video_durations,
        "picture_duration_frames": picture_duration,
        "timeline_duration_frames": timeline_duration,
        "fade_tail_frames": fade_tail,
        "gaps": gaps,
        "shot_labels": shot_labels,
        "clip_colors": clip_colors,
        "timeline_folder": "Master",
        "track_names": _validate_track_names(timeline),
    }
    if video_items:
        result["video_name"] = video_names[0]
        result["video_duration_frames"] = video_durations[0]
    a1_items = audio_by_track["A1"]["items"]
    if a1_items:
        result["audio_name"] = a1_items[0].GetName()
        result["audio_duration_frames"] = int(a1_items[0].GetDuration())
    result["bin_names"] = _validate_bins(
        project, bin_names, bin_destinations, videos, audios, titles
    )
    result["marker_names"] = _validate_markers(timeline, marker_specs)
    result["marker_count"] = len(result["marker_names"])
    result.update(_validate_transitions(transition_items, transitions))
    result.update(_validate_titles(timeline, titles))
    if relinked:
        result.update(relinked)
    return result


def _validate_track_names(timeline: Any) -> dict[str, str]:
    actual: dict[str, str] = {}
    for (track_type, index), expected in TRACK_NAMES.items():
        if index > timeline.GetTrackCount(track_type):
            continue
        name = str(timeline.GetTrackName(track_type, index))
        if name != expected:
            raise RuntimeError(
                f"{track_type} track {index} is named {name!r}, expected {expected!r}"
            )
        prefix = "V" if track_type == "video" else "A"
        actual[f"{prefix}{index}"] = name
    return actual


def _audio_items_by_track(timeline: Any, audios: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for label in ("A1", "A2", "A3"):
        index = track_index(label)
        items = []
        if timeline.GetTrackCount("audio") >= index:
            items = timeline.GetItemListInTrack("audio", index) or []
        expected = [clip for clip in audios if clip["track"] == label]
        names = [item.GetName() for item in items]
        expected_names = [audio_display_name(clip) for clip in expected]
        if names != expected_names:
            raise RuntimeError(f"{label} names {names} do not match {expected_names}")
        starts = [int(item.GetStart()) for item in items]
        expected_starts = [int(clip["start_frame"]) for clip in expected]
        durations = [int(item.GetDuration()) for item in items]
        expected_durations = [int(clip["duration_frames"]) for clip in expected]
        if starts != expected_starts or durations != expected_durations:
            raise RuntimeError(f"{label} placement does not match the story spec")
        result[label] = {"items": items, "names": names}
    return result


def _validate_production_audio(
    timeline: Any,
    videos: list[dict[str, Any]],
) -> dict[str, Any]:
    expected = [clip for clip in videos if clip["linked_audio"]]
    items = []
    if timeline.GetTrackCount("audio") >= 4:
        items = timeline.GetItemListInTrack("audio", 4) or []
    names = [item.GetName() for item in items]
    expected_names = [
        f"{video_display_name(clip)} (cam)" for clip in expected
    ]
    if names != expected_names:
        raise RuntimeError(f"A4 names {names} do not match {expected_names}")
    starts = [int(item.GetStart()) for item in items]
    durations = [int(item.GetDuration()) for item in items]
    if starts != [int(clip["start_frame"]) for clip in expected] or durations != [
        int(clip["duration_frames"]) for clip in expected
    ]:
        raise RuntimeError("A4 production audio placement does not match linked V1 clips")

    linked = []
    for item, clip in zip(items, expected, strict=True):
        getter = getattr(item, "GetLinkedItems", None)
        if getter is None:
            raise RuntimeError("Resolve TimelineItem.GetLinkedItems is unavailable")
        linked_names = [linked_item.GetName() for linked_item in (getter() or [])]
        is_linked = video_display_name(clip) in linked_names
        if not is_linked:
            raise RuntimeError(f"Production audio for {clip['filename']} is not linked")
        linked.append(is_linked)
    return {"items": items, "names": names, "linked": linked}


def _validate_bins(
    project: Any,
    bin_names: list[str],
    bin_destinations: dict[str, str],
    videos: list[dict[str, Any]],
    audios: list[dict[str, Any]],
    titles: list[dict[str, Any]],
) -> list[str]:
    if not bin_names:
        return []
    root = project.GetMediaPool().GetRootFolder()
    folders = {folder.GetName(): folder for folder in root.GetSubFolderList() or []}
    missing = [name for name in bin_names if name not in folders]
    if missing:
        raise RuntimeError(f"Re-imported project missing bins {missing}")

    expected: dict[str, list[str]] = {name: [] for name in bin_names}
    video_bin = bin_destinations.get("video")
    for clip in videos:
        if video_bin:
            expected[video_bin].append(str(clip["filename"]))
    for clip in audios:
        audio_bin = bin_destinations.get(str(clip["role"]))
        if audio_bin:
            expected[audio_bin].append(str(clip["filename"]))
    graphics_bin = bin_destinations.get("graphics")
    for title in titles:
        if graphics_bin:
            expected[graphics_bin].append(str(title["filename"]))
    for name, filenames in expected.items():
        actual_media = [
            item.GetName()
            for item in (folders[name].GetClipList() or [])
            if not _looks_like_timeline(item)
        ]
        if sorted(actual_media) != sorted(filenames):
            raise RuntimeError(
                f"Bin {name} clips {sorted(actual_media)} do not match {sorted(filenames)}"
            )
    return bin_names


def _looks_like_timeline(item: Any) -> bool:
    getter = getattr(item, "GetClipProperty", None)
    if getter is None:
        return False
    props = getter() or {}
    if isinstance(props, dict):
        type_name = str(props.get("Type") or props.get("type") or "")
        return type_name.lower() == "timeline"
    return False


def _validate_markers(timeline: Any, marker_specs: list[dict[str, Any]]) -> list[str]:
    if not marker_specs:
        return []
    found_raw = timeline.GetMarkers() or {}
    found = {int(frame): info for frame, info in found_raw.items()}
    expected_frames = [int(marker["frame"]) for marker in marker_specs]
    actual_frames = sorted(int(frame) for frame in found)
    if actual_frames != sorted(expected_frames):
        raise RuntimeError(f"marker frames {actual_frames} do not match {sorted(expected_frames)}")
    names = []
    for marker in marker_specs:
        info = found[int(marker["frame"])]
        name = info.get("name") if isinstance(info, dict) else None
        if name != marker["name"]:
            raise RuntimeError(
                f"marker at {marker['frame']} named {name!r}, expected {marker['name']!r}"
            )
        names.append(str(name))
    return names


def _validate_transitions(
    transition_items: list[Any],
    transition_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    expected = [
        spec
        for spec in transition_specs
        if spec.get("kind") in {"cross_dissolve", "fade_from_black", "fade_to_black"}
    ]
    if len(transition_items) != len(expected):
        raise RuntimeError(
            f"Expected {len(expected)} V1 transitions, got {len(transition_items)}"
        )
    names = [item.GetName() for item in transition_items]
    if any("dissolve" not in name.lower() for name in names):
        raise RuntimeError(f"unexpected transition names after re-import: {names}")
    report = [
        {
            "story_kind": spec["kind"],
            "resolve_implementation": item.GetName(),
            "duration_frames": int(spec["duration_frames"]),
        }
        for spec, item in zip(expected, transition_items, strict=True)
    ]
    return {
        "transition_count": len(transition_items),
        "transition_validation": report,
        "fade_from_black": any(spec.get("kind") == "fade_from_black" for spec in expected),
        "fade_to_black": any(spec.get("kind") == "fade_to_black" for spec in expected),
    }


def _validate_titles(timeline: Any, title_specs: list[dict[str, Any]]) -> dict[str, Any]:
    if not title_specs:
        return {"title_names": [], "title_count": 0}
    needed = max(track_index(title["track"]) for title in title_specs)
    if timeline.GetTrackCount("video") < needed:
        raise RuntimeError("Re-imported project is missing the title video track")
    items = timeline.GetItemListInTrack("video", needed) or []
    names = [item.GetName() for item in items]
    expected_names = [title_display_name(title) for title in title_specs]
    if names != expected_names:
        raise RuntimeError(f"title names {names} do not match {expected_names}")
    starts = [int(item.GetStart()) for item in items]
    durations = [int(item.GetDuration()) for item in items]
    expected_starts = [int(title["start_frame"]) for title in title_specs]
    expected_durations = [int(title["duration_frames"]) for title in title_specs]
    if starts != expected_starts or durations != expected_durations:
        raise RuntimeError("title still placement does not match the story spec")
    return {"title_names": names, "title_count": len(names)}


def _media_pool_clips(media_pool: Any) -> list[Any]:
    clips: list[Any] = []

    def walk(folder: Any) -> None:
        for item in folder.GetClipList() or []:
            if not _looks_like_timeline(item):
                clips.append(item)
        for subfolder in folder.GetSubFolderList() or []:
            walk(subfolder)

    walk(media_pool.GetRootFolder())
    return clips


def _clip_file_path(item: Any) -> Path:
    path = item.GetClipProperty("File Path")
    if not path:
        props = item.GetClipProperty() or {}
        path = props.get("File Path") if isinstance(props, dict) else ""
    return Path(str(path))


def _relink_placeholder_media(project: Any, media_dir: Path) -> dict[str, Any]:
    relink_dir = media_dir.resolve()
    media_pool = project.GetMediaPool()
    clips = _media_pool_clips(media_pool)
    if not clips:
        raise RuntimeError("Re-imported project has no media-pool clips to relink")
    if not media_pool.RelinkClips(clips, str(relink_dir)):
        raise RuntimeError("Resolve RelinkClips to package Placeholder_Media returned false")

    relinked_names = []
    for item in clips:
        path = _clip_file_path(item)
        if path.parent.resolve() != relink_dir or not path.is_file():
            raise RuntimeError(f"{item.GetName()} did not relink into {relink_dir}, got {path}")
        relinked_names.append(item.GetName())
    return {
        "relink_folder": str(relink_dir),
        "relinked_clip_count": len(relinked_names),
        "relinked_names": sorted(relinked_names),
    }


def _write_package_zip(output: Path, package_zip: Path) -> None:
    with zipfile.ZipFile(package_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(output))


def _package_readme(validated: bool) -> str:
    label = "VALIDATED_IN_RESOLVE" if validated else "GENERATOR_EXISTS"
    drp_line = (
        "`project.drp` was exported by DaVinci Resolve `ExportProject`.\n"
        if validated
        else "`project.drp` is omitted because Resolve did not export it.\n"
    )
    return (
        f"# resolve-template package\n\n"
        f"**Validation label:** `{label}`\n\n"
        f"{drp_line}\n"
        "Contents:\n"
        "- `Placeholder_Media/` — generated color-coded MP4s, optional silent linked "
        "production audio, silent WAVs, and title-card MP4s (not real footage)\n"
        "- `shot_tracker.csv` — timeline durations plus source-handle metadata\n"
        "- `timeline_map.md` — V1/V2/A1–A3 layout, markers, and transitions\n"
        "- `story.snapshot.yaml` — the story used to build this package\n\n"
        "Titles are generated title-card MP4 placeholders on V2, not native Resolve Text/Text+ titles. "
        "The story `text` field is visibly rendered into each card.\n\n"
        "To relink after unzip: in Resolve, select the offline clips and relink "
        "once to this package's `Placeholder_Media/` folder.\n"
    )
