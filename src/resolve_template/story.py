"""Load and lightly validate story.yaml documents."""

from __future__ import annotations

import json
from decimal import Decimal
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


class StoryValidationError(ValueError):
    """A story schema error with one field path per line."""

    def __init__(self, field_errors: list[str]) -> None:
        self.field_errors = field_errors
        details = "\n".join(f"- {error}" for error in field_errors)
        super().__init__(f"story.yaml failed schema validation:\n{details}")


def _story_schema() -> dict[str, Any]:
    resource = files("resolve_template").joinpath("story-v1.schema.json")
    with resource.open(encoding="utf-8") as handle:
        return json.load(handle)


def _schema_error_path(error: Any) -> str:
    parts = [str(part) for part in error.absolute_path]
    if error.validator == "required":
        missing = error.message.split("'")[1]
        parts.append(missing)
    return ".".join(["story", *parts])


def validate_story_schema(data: Any) -> None:
    errors = sorted(
        Draft202012Validator(_story_schema()).iter_errors(data),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if not errors:
        return
    raise StoryValidationError(
        [f"{_schema_error_path(error)}: {error.message}" for error in errors]
    )


def load_story(path: Path) -> dict[str, Any]:
    path = Path(path)
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    validate_story_schema(data)
    normalize_story_times(data)
    validate_contiguous_v1(data)
    validate_audio_tracks(data)
    validate_bins_and_markers(data)
    validate_transitions_and_titles(data)
    validate_unique_media_filenames(data)
    return data


def normalize_story_times(story: dict[str, Any]) -> None:
    """Convert seconds authoring fields to the canonical integer frame fields."""
    fps = int(story["fps"])
    expected_start = 0
    for index, clip in enumerate(story["video"]):
        _normalize_duration(clip, fps, f"story.video.{index}")
        if "start" in clip:
            clip["start_frame"] = _seconds_to_frames(
                clip.pop("start"), fps, f"story.video.{index}.start", positive=False
            )
        elif "start_frame" not in clip:
            clip["start_frame"] = expected_start
        expected_start = int(clip["start_frame"]) + int(clip["duration_frames"])

    timeline = story["timeline"]
    if "duration" in timeline:
        timeline["duration_frames"] = _seconds_to_frames(
            timeline.pop("duration"), fps, "story.timeline.duration", positive=True
        )
    elif "duration_frames" not in timeline:
        timeline["duration_frames"] = expected_start

    for section in ("audio", "titles"):
        for index, clip in enumerate(story.get(section) or []):
            path = f"story.{section}.{index}"
            _normalize_duration(clip, fps, path)
            if "start" in clip:
                clip["start_frame"] = _seconds_to_frames(
                    clip.pop("start"), fps, f"{path}.start", positive=False
                )

    for index, marker in enumerate(story.get("markers") or []):
        if "at" in marker:
            marker["frame"] = _seconds_to_frames(
                marker.pop("at"), fps, f"story.markers.{index}.at", positive=False
            )

    for index, transition in enumerate(story.get("transitions") or []):
        if "duration" in transition:
            transition["duration_frames"] = _seconds_to_frames(
                transition.pop("duration"),
                fps,
                f"story.transitions.{index}.duration",
                positive=True,
            )


def _normalize_duration(item: dict[str, Any], fps: int, path: str) -> None:
    if "duration" in item:
        item["duration_frames"] = _seconds_to_frames(
            item.pop("duration"), fps, f"{path}.duration", positive=True
        )


def _seconds_to_frames(value: Any, fps: int, path: str, *, positive: bool) -> int:
    raw = value[:-1] if isinstance(value, str) else value
    seconds = Decimal(str(raw))
    frames = seconds * fps
    if frames != frames.to_integral_value():
        raise StoryValidationError(
            [f"{path}: {value!r} does not land on a whole frame at {fps} fps"]
        )
    result = int(frames)
    if (positive and result <= 0) or (not positive and result < 0):
        relation = "greater than zero" if positive else "zero or greater"
        raise StoryValidationError([f"{path}: must be {relation}"])
    return result


def video_clips(story: dict[str, Any]) -> list[dict[str, Any]]:
    clips = story.get("video") or []
    if not isinstance(clips, list):
        raise TypeError("story video must be a list")
    if not clips:
        raise ValueError("story must list at least one video clip")
    return clips


def audio_clips(story: dict[str, Any]) -> list[dict[str, Any]]:
    clips = story.get("audio") or []
    if not isinstance(clips, list):
        raise TypeError("story audio must be a list when present")
    return clips


def validate_contiguous_v1(story: dict[str, Any]) -> None:
    """Require V1 clips to start at 0, follow shot order, and leave no gaps."""
    clips = video_clips(story)
    fps = int(story["fps"])
    if fps <= 0:
        raise ValueError("fps must be positive")

    expected_start = 0
    for index, clip in enumerate(clips, start=1):
        if clip.get("track") != "V1":
            raise ValueError(f"Phase 3 requires all video on V1, got {clip.get('track')}")
        if int(clip["shot"]) != index:
            raise ValueError(f"shot numbers must be 1..N in order, got {clip.get('shot')} at {index}")
        start = int(clip["start_frame"])
        duration = int(clip["duration_frames"])
        if duration <= 0:
            raise ValueError(f"clip {clip.get('filename')} duration_frames must be positive")
        if start != expected_start:
            raise ValueError(
                f"gap or overlap before {clip.get('filename')}: expected start {expected_start}, got {start}"
            )
        expected_start = start + duration

    timeline_duration = int(story["timeline"]["duration_frames"])
    if expected_start != timeline_duration:
        raise ValueError(
            f"timeline duration_frames {timeline_duration} does not match V1 coverage {expected_start}"
        )


def track_index(track: str) -> int:
    """Return 1-based Resolve track index from a story track label like V1 or A3."""
    if not isinstance(track, str) or len(track) < 2 or track[0] not in {"V", "A"}:
        raise ValueError(f"invalid track label: {track}")
    index = int(track[1:])
    if index < 1:
        raise ValueError(f"track index must be >= 1: {track}")
    return index


def validate_audio_tracks(story: dict[str, Any]) -> None:
    """Allow A1–A3 placeholders; reject unknown tracks and clips past the timeline end."""
    timeline_duration = int(story["timeline"]["duration_frames"])
    for clip in audio_clips(story):
        track = clip.get("track")
        if track not in {"A1", "A2", "A3"}:
            raise ValueError(f"Phase 4 allows A1/A2/A3 only, got {track}")
        start = int(clip["start_frame"])
        duration = int(clip["duration_frames"])
        if start < 0 or duration <= 0:
            raise ValueError(f"audio clip {clip.get('filename')} has invalid start or duration")
        if start + duration > timeline_duration:
            raise ValueError(
                f"audio clip {clip.get('filename')} extends past timeline end {timeline_duration}"
            )


STANDARD_BINS = (
    "01_VIDEO_PLACEHOLDERS",
    "02_AUDIO_VO",
    "03_AUDIO_MUSIC",
    "04_AUDIO_SFX",
    "05_GRAPHICS",
    "06_REFERENCE",
)

MARKER_COLORS = (
    "Blue",
    "Cyan",
    "Green",
    "Yellow",
    "Red",
    "Pink",
    "Purple",
    "Fuchsia",
    "Rose",
    "Lavender",
    "Sky",
    "Mint",
    "Lemon",
    "Sand",
    "Cocoa",
    "Cream",
)

BIN_BY_AUDIO_ROLE = {
    "vo": "02_AUDIO_VO",
    "music": "03_AUDIO_MUSIC",
    "sfx": "04_AUDIO_SFX",
}

DEFAULT_BIN_BY_ROLE = {
    "video": "01_VIDEO_PLACEHOLDERS",
    "vo": "02_AUDIO_VO",
    "music": "03_AUDIO_MUSIC",
    "sfx": "04_AUDIO_SFX",
    "graphics": "05_GRAPHICS",
    "reference": "06_REFERENCE",
}


def bins(story: dict[str, Any]) -> list[str]:
    configured = story.get("bins") or []
    if isinstance(configured, dict):
        return [str(name) for name in configured.values()]
    if isinstance(configured, list):
        return [str(name) for name in configured]
    raise TypeError("story bins must be a list or role-to-name mapping")


def bin_mapping(story: dict[str, Any]) -> dict[str, str]:
    configured = story.get("bins") or []
    if isinstance(configured, dict):
        return {str(role): str(name) for role, name in configured.items()}
    return dict(zip(DEFAULT_BIN_BY_ROLE, bins(story), strict=False))


def markers(story: dict[str, Any]) -> list[dict[str, Any]]:
    items = story.get("markers") or []
    if not isinstance(items, list):
        raise TypeError("story markers must be a list when present")
    return items


def bin_for_video(_clip: dict[str, Any], story: dict[str, Any] | None = None) -> str:
    if story is None:
        return DEFAULT_BIN_BY_ROLE["video"]
    return bin_mapping(story).get("video", "")


def bin_for_audio(clip: dict[str, Any], story: dict[str, Any] | None = None) -> str:
    role = str(clip.get("role") or "")
    if role not in BIN_BY_AUDIO_ROLE:
        raise ValueError(f"audio clip {clip.get('filename')} needs role vo, music, or sfx")
    if story is None:
        return BIN_BY_AUDIO_ROLE[role]
    return bin_mapping(story).get(role, "")


def validate_bins_and_markers(story: dict[str, Any]) -> None:
    names = bins(story)
    if len(names) != len(set(names)):
        raise ValueError("bin names must be unique")

    timeline_duration = int(story["timeline"]["duration_frames"])
    seen_frames: set[int] = set()
    for marker in markers(story):
        frame = int(marker["frame"])
        duration = int(marker.get("duration") or 1)
        name = marker.get("name")
        color = marker.get("color")
        if not name:
            raise ValueError("each marker needs a name")
        if color not in MARKER_COLORS:
            raise ValueError(f"invalid marker color: {color}")
        if frame < 0 or frame >= timeline_duration:
            raise ValueError(f"marker {name} frame {frame} is outside the timeline")
        if duration < 1:
            raise ValueError(f"marker {name} duration must be >= 1")
        if frame in seen_frames:
            raise ValueError(f"duplicate marker frame {frame}")
        seen_frames.add(frame)


SAFE_TRANSITION_KINDS = (
    "cut",
    "cross_dissolve",
    "fade_from_black",
    "fade_to_black",
)

TRANSITION_HANDLE_FRAMES = 12


def transitions(story: dict[str, Any]) -> list[dict[str, Any]]:
    items = story.get("transitions") or []
    if not isinstance(items, list):
        raise TypeError("story transitions must be a list when present")
    return items


def titles(story: dict[str, Any]) -> list[dict[str, Any]]:
    items = story.get("titles") or []
    if not isinstance(items, list):
        raise TypeError("story titles must be a list when present")
    return items


def bin_for_title(_clip: dict[str, Any], story: dict[str, Any] | None = None) -> str:
    if story is None:
        return DEFAULT_BIN_BY_ROLE["graphics"]
    return bin_mapping(story).get("graphics", "")


def needs_transition_handles(story: dict[str, Any]) -> bool:
    return any(item.get("kind") == "cross_dissolve" for item in transitions(story))


def source_handle_frames(story: dict[str, Any]) -> int:
    return TRANSITION_HANDLE_FRAMES if needs_transition_handles(story) else 0


def validate_transitions_and_titles(story: dict[str, Any]) -> None:
    clips = video_clips(story)
    timeline_duration = int(story["timeline"]["duration_frames"])
    shot_by_number = {int(clip["shot"]): clip for clip in clips}

    for item in transitions(story):
        kind = item.get("kind")
        if kind not in SAFE_TRANSITION_KINDS:
            raise ValueError(
                f"Phase 7 allows {list(SAFE_TRANSITION_KINDS)} only, got {kind}"
            )
        duration = int(item.get("duration_frames") or 0)
        if kind == "cut":
            continue
        if duration < 1:
            raise ValueError(f"{kind} needs duration_frames >= 1")
        if kind == "cross_dissolve":
            after_shot = int(item.get("after_shot") or 0)
            outgoing = shot_by_number.get(after_shot)
            incoming = shot_by_number.get(after_shot + 1)
            if outgoing is None or incoming is None:
                raise ValueError(
                    f"cross_dissolve after_shot {after_shot} needs two adjacent V1 clips"
                )
            limit = min(int(outgoing["duration_frames"]), int(incoming["duration_frames"]))
            if duration >= limit:
                raise ValueError(
                    f"cross_dissolve duration {duration} must be shorter than both clips"
                )
        elif kind == "fade_from_black":
            shot = int(item.get("shot") or 0)
            if shot != 1:
                raise ValueError("fade_from_black must target shot 1")
            if duration >= int(shot_by_number[1]["duration_frames"]):
                raise ValueError("fade_from_black duration must be shorter than shot 1")
        elif kind == "fade_to_black":
            shot = int(item.get("shot") or 0)
            last_shot = int(clips[-1]["shot"])
            if shot != last_shot:
                raise ValueError(f"fade_to_black must target the last shot ({last_shot})")
            if duration >= int(clips[-1]["duration_frames"]):
                raise ValueError("fade_to_black duration must be shorter than the last shot")

    for title in titles(story):
        filename = title.get("filename")
        if not filename:
            raise ValueError("each title needs a filename")
        track = title.get("track")
        if track != "V2":
            raise ValueError(f"Phase 7 places generated title stills on V2, got {track}")
        start = int(title["start_frame"])
        duration = int(title["duration_frames"])
        if start < 0 or duration <= 0:
            raise ValueError(f"title {filename} has invalid start or duration")
        if start + duration > timeline_duration:
            raise ValueError(f"title {filename} extends past timeline end {timeline_duration}")
        text = title.get("text")
        if text is not None and not isinstance(text, str):
            raise TypeError(f"title {filename} text must be a string")


def validate_unique_media_filenames(story: dict[str, Any]) -> None:
    filenames = [
        *(str(clip["filename"]) for clip in video_clips(story)),
        *(str(clip["filename"]) for clip in audio_clips(story)),
        *(str(title["filename"]) for title in titles(story)),
    ]
    duplicates = sorted({name for name in filenames if filenames.count(name) > 1})
    if duplicates:
        raise ValueError(f"media filenames must be unique, duplicates: {duplicates}")
