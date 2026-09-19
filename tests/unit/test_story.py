from __future__ import annotations

import json
from pathlib import Path

import pytest

from resolve_template.story import (
    STANDARD_BINS,
    StoryValidationError,
    bin_mapping,
    bins,
    load_story,
    validate_audio_tracks,
    validate_bins_and_markers,
    validate_contiguous_v1,
    validate_transitions_and_titles,
    validate_unique_media_filenames,
)


def test_ten_clip_story_is_contiguous() -> None:
    story = load_story(
        Path(__file__).resolve().parents[2] / "examples" / "poc_ten_clips" / "story.yaml"
    )
    assert len(story["video"]) == 10
    assert story["video"][0]["shot"] == 1
    assert story["video"][-1]["shot"] == 10
    assert story["video"][-1]["filename"] == "010_SHOT_10_PLACEHOLDER.mp4"


def test_gap_in_v1_is_rejected() -> None:
    story = {
        "fps": 25,
        "timeline": {"name": "PRE_EDIT_MAIN", "duration_frames": 50},
        "video": [
            {
                "shot": 1,
                "filename": "a.mp4",
                "track": "V1",
                "start_frame": 0,
                "duration_frames": 25,
            },
            {
                "shot": 2,
                "filename": "b.mp4",
                "track": "V1",
                "start_frame": 26,
                "duration_frames": 24,
            },
        ],
    }
    with pytest.raises(ValueError, match="gap or overlap"):
        validate_contiguous_v1(story)


def test_audio_tracks_story_loads() -> None:
    story = load_story(
        Path(__file__).resolve().parents[2] / "examples" / "poc_audio_tracks" / "story.yaml"
    )
    assert [clip["track"] for clip in story["audio"]] == ["A1", "A2", "A3", "A3"]


def test_audio_on_a4_is_rejected() -> None:
    story = {
        "fps": 25,
        "timeline": {"name": "PRE_EDIT_MAIN", "duration_frames": 25},
        "video": [
            {
                "shot": 1,
                "filename": "a.mp4",
                "track": "V1",
                "start_frame": 0,
                "duration_frames": 25,
            }
        ],
        "audio": [
            {
                "filename": "x.wav",
                "track": "A4",
                "start_frame": 0,
                "duration_frames": 25,
            }
        ],
    }
    with pytest.raises(ValueError, match="A1/A2/A3"):
        validate_audio_tracks(story)


def test_bins_and_markers_story_loads() -> None:
    story = load_story(
        Path(__file__).resolve().parents[2] / "examples" / "poc_bins_markers" / "story.yaml"
    )
    assert story["bins"] == list(STANDARD_BINS)
    assert [marker["name"] for marker in story["markers"]] == [
        "OPENING",
        "SFX_HIT_1",
        "MIDPOINT",
        "LAST_SHOT",
    ]


def test_duplicate_bin_names_are_rejected() -> None:
    story = {
        "fps": 25,
        "timeline": {"name": "PRE_EDIT_MAIN", "duration_frames": 25},
        "video": [
            {
                "shot": 1,
                "filename": "a.mp4",
                "track": "V1",
                "start_frame": 0,
                "duration_frames": 25,
            }
        ],
        "bins": ["Master", "Master"],
    }
    with pytest.raises(ValueError, match="bin names must be unique"):
        validate_bins_and_markers(story)


def test_transitions_and_titles_story_loads() -> None:
    story = load_story(
        Path(__file__).resolve().parents[2]
        / "examples"
        / "poc_transitions_titles"
        / "story.yaml"
    )
    assert [item["kind"] for item in story["transitions"]] == [
        "fade_from_black",
        "cross_dissolve",
        "fade_to_black",
    ]
    assert story["titles"][0]["filename"] == "TITLE_01_OPENING.mp4"
    assert story["titles"][0]["track"] == "V2"


def test_unknown_transition_kind_is_rejected() -> None:
    story = {
        "fps": 25,
        "timeline": {"name": "PRE_EDIT_MAIN", "duration_frames": 50},
        "video": [
            {
                "shot": 1,
                "filename": "a.mp4",
                "track": "V1",
                "start_frame": 0,
                "duration_frames": 25,
            },
            {
                "shot": 2,
                "filename": "b.mp4",
                "track": "V1",
                "start_frame": 25,
                "duration_frames": 25,
            },
        ],
        "transitions": [{"kind": "wipe", "after_shot": 1, "duration_frames": 6}],
    }
    with pytest.raises(ValueError, match="Phase 7 allows"):
        validate_transitions_and_titles(story)


def test_load_story_reports_schema_field_path(tmp_path: Path) -> None:
    path = tmp_path / "story.yaml"
    path.write_text(
        """
version: "1"
fps: 25
timeline:
  name: PRE_EDIT_MAIN
  duration_frames: 25
video:
  - shot: 1
    filename: a.mp4
    track: V3
    start_frame: 0
    duration_frames: 25
""",
        encoding="utf-8",
    )
    with pytest.raises(StoryValidationError, match=r"story\.video\.0\.track"):
        load_story(path)


def test_packaged_schema_matches_public_schema() -> None:
    root = Path(__file__).resolve().parents[2]
    public = json.loads((root / "schemas" / "story-v1.schema.json").read_text(encoding="utf-8"))
    packaged = json.loads(
        (root / "src" / "resolve_template" / "story-v1.schema.json").read_text(encoding="utf-8")
    )
    assert packaged == public


def test_duplicate_media_filenames_are_rejected() -> None:
    story = {
        "fps": 25,
        "timeline": {"name": "PRE_EDIT_MAIN", "duration_frames": 25},
        "video": [
            {
                "shot": 1,
                "filename": "duplicate.mp4",
                "track": "V1",
                "start_frame": 0,
                "duration_frames": 25,
            }
        ],
        "titles": [
            {
                "filename": "duplicate.mp4",
                "track": "V2",
                "start_frame": 0,
                "duration_frames": 25,
            }
        ],
    }
    with pytest.raises(ValueError, match="media filenames must be unique"):
        validate_unique_media_filenames(story)


def test_seconds_are_normalized_and_timeline_is_derived(tmp_path: Path) -> None:
    path = tmp_path / "seconds.yaml"
    path.write_text(
        """
version: "1"
fps: 25
timeline:
  name: PRE_EDIT_MAIN
video:
  - shot: 1
    filename: a.mp4
    track: V1
    duration: 1s
  - shot: 2
    filename: b.mp4
    track: V1
    duration: 1.48s
audio:
  - role: music
    filename: bed.wav
    track: A2
    start: 0s
    duration: 2.48s
markers:
  - at: 1.48s
    name: BEAT
    color: Blue
transitions:
  - kind: cross_dissolve
    after_shot: 1
    duration: 0.2s
""",
        encoding="utf-8",
    )
    story = load_story(path)
    assert [clip["start_frame"] for clip in story["video"]] == [0, 25]
    assert [clip["duration_frames"] for clip in story["video"]] == [25, 37]
    assert story["timeline"]["duration_frames"] == 62
    assert story["audio"][0]["duration_frames"] == 62
    assert story["markers"][0]["frame"] == 37
    assert story["transitions"][0]["duration_frames"] == 5


def test_seconds_must_land_on_a_whole_frame(tmp_path: Path) -> None:
    path = tmp_path / "fractional.yaml"
    path.write_text(
        """
version: "1"
fps: 25
timeline:
  name: PRE_EDIT_MAIN
video:
  - shot: 1
    filename: a.mp4
    track: V1
    duration: 0.01s
""",
        encoding="utf-8",
    )
    with pytest.raises(StoryValidationError, match=r"story\.video\.0\.duration"):
        load_story(path)


def test_bins_can_be_renamed_and_roles_omitted() -> None:
    story = {
        "bins": {
            "video": "Shots",
            "music": "Score",
            "graphics": "Cards",
        }
    }
    assert bins(story) == ["Shots", "Score", "Cards"]
    assert bin_mapping(story) == {
        "video": "Shots",
        "music": "Score",
        "graphics": "Cards",
    }


def test_legacy_bin_lists_route_by_role_order() -> None:
    assert bin_mapping({"bins": ["Shots", "Voice", "Score"]}) == {
        "video": "Shots",
        "vo": "Voice",
        "music": "Score",
    }
