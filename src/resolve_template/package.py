"""Sidecar files for the Phase 6 story package."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from resolve_template.story import (
    audio_clips,
    bin_for_audio,
    bin_for_title,
    bin_for_video,
    bins,
    markers,
    source_handles,
    titles,
    transitions,
    video_clips,
)

TRACKER_FIELDS = (
    "kind",
    "shot",
    "filename",
    "track",
    "start_frame",
    "duration_frames",
    "source_duration_frames",
    "head_handle_frames",
    "tail_handle_frames",
    "linked_audio",
    "bin",
    "role",
)


def write_package_sidecars(output: Path, story: dict[str, Any]) -> dict[str, Path]:
    tracker = output / "shot_tracker.csv"
    timeline_map = output / "timeline_map.md"
    write_shot_tracker(tracker, story)
    write_timeline_map(timeline_map, story)
    return {"shot_tracker": tracker, "timeline_map": timeline_map}


def tracker_rows(story: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    has_bins = bool(bins(story))
    handles = source_handles(story)
    for clip in video_clips(story):
        clip_handles = handles[int(clip["shot"])]
        duration = int(clip["duration_frames"])
        rows.append(
            {
                "kind": "video",
                "shot": int(clip["shot"]),
                "filename": clip["filename"],
                "track": clip["track"],
                "start_frame": int(clip["start_frame"]),
                "duration_frames": duration,
                "source_duration_frames": (
                    duration + clip_handles["head"] + clip_handles["tail"]
                ),
                "head_handle_frames": clip_handles["head"],
                "tail_handle_frames": clip_handles["tail"],
                "linked_audio": bool(clip["linked_audio"]),
                "bin": bin_for_video(clip, story) if has_bins else "",
                "role": "",
            }
        )
    for clip in audio_clips(story):
        rows.append(
            {
                "kind": "audio",
                "shot": "",
                "filename": clip["filename"],
                "track": clip["track"],
                "start_frame": int(clip["start_frame"]),
                "duration_frames": int(clip["duration_frames"]),
                "source_duration_frames": int(clip["duration_frames"]),
                "head_handle_frames": 0,
                "tail_handle_frames": 0,
                "linked_audio": False,
                "bin": bin_for_audio(clip, story) if has_bins else "",
                "role": clip.get("role") or "",
            }
        )
    for title in titles(story):
        rows.append(
            {
                "kind": "title",
                "shot": "",
                "filename": title["filename"],
                "track": title["track"],
                "start_frame": int(title["start_frame"]),
                "duration_frames": int(title["duration_frames"]),
                "source_duration_frames": int(title["duration_frames"]),
                "head_handle_frames": 0,
                "tail_handle_frames": 0,
                "linked_audio": False,
                "bin": bin_for_title(title, story) if has_bins else "",
                "role": "still",
            }
        )
    return rows


def write_shot_tracker(path: Path, story: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRACKER_FIELDS)
        writer.writeheader()
        writer.writerows(tracker_rows(story))


def write_timeline_map(path: Path, story: dict[str, Any]) -> None:
    timeline = story["timeline"]
    lines = [
        f"# Timeline map — {timeline['name']}",
        "",
        f"- fps: {story['fps']}",
        f"- duration_frames: {timeline['duration_frames']}",
        "- source handles: only the head/tail frames required by each transition",
        "",
        "## Video V1",
        "",
    ]
    for clip in video_clips(story):
        end = int(clip["start_frame"]) + int(clip["duration_frames"])
        lines.append(
            f"- shot {clip['shot']}: {clip['start_frame']}–{end} `{clip['filename']}`"
        )
    lines.extend(["", "## Audio", ""])
    audio = audio_clips(story)
    linked_video = [clip for clip in video_clips(story) if clip["linked_audio"]]
    if not audio and not linked_video:
        lines.append("- none")
    for clip in audio:
        end = int(clip["start_frame"]) + int(clip["duration_frames"])
        role = clip.get("role") or "audio"
        lines.append(
            f"- {clip['track']} {role}: {clip['start_frame']}–{end} `{clip['filename']}`"
        )
    for clip in linked_video:
        end = int(clip["start_frame"]) + int(clip["duration_frames"])
        lines.append(
            f"- A4 production (linked to V1): {clip['start_frame']}–{end} "
            f"`{clip['filename']}`"
        )
    lines.extend(["", "## Markers", ""])
    marker_specs = markers(story)
    if not marker_specs:
        lines.append("- none")
    for marker in marker_specs:
        lines.append(
            f"- {marker['frame']} `{marker['name']}` ({marker.get('color', '')})"
        )
    lines.extend(["", "## Transitions", ""])
    transition_specs = transitions(story)
    if not transition_specs:
        lines.append("- none (cuts only)")
    for item in transition_specs:
        kind = item.get("kind")
        duration = item.get("duration_frames", "")
        if kind == "cross_dissolve":
            lines.append(
                f"- cross dissolve after shot {item.get('after_shot')} ({duration} frames)"
            )
        elif kind == "fade_from_black":
            lines.append(f"- fade from black on shot {item.get('shot')} ({duration} frames)")
        elif kind == "fade_to_black":
            lines.append(f"- fade to black on shot {item.get('shot')} ({duration} frames)")
        else:
            lines.append(f"- {kind}")
    lines.extend(["", "## Titles", ""])
    title_specs = titles(story)
    if not title_specs:
        lines.append("- none")
    for title in title_specs:
        end = int(title["start_frame"]) + int(title["duration_frames"])
        lines.append(
            f"- {title['track']}: {title['start_frame']}–{end} `{title['filename']}`"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
