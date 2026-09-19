from __future__ import annotations

import csv
from pathlib import Path

from resolve_template.package import TRACKER_FIELDS, tracker_rows, write_shot_tracker
from resolve_template.story import load_story


def test_tracker_rows_match_shot_numbers_and_filenames() -> None:
    story = load_story(
        Path(__file__).resolve().parents[2] / "examples" / "poc_bins_markers" / "story.yaml"
    )
    rows = tracker_rows(story)
    video_rows = [row for row in rows if row["kind"] == "video"]
    assert [row["shot"] for row in video_rows] == list(range(1, 11))
    assert [row["filename"] for row in video_rows] == [
        f"{index:03d}_SHOT_{index:02d}_PLACEHOLDER.mp4" for index in range(1, 11)
    ]
    audio_rows = [row for row in rows if row["kind"] == "audio"]
    assert [row["filename"] for row in audio_rows] == [
        "VO_01_BED_PLACEHOLDER.wav",
        "MUSIC_01_BED_PLACEHOLDER.wav",
        "SFX_01_HIT_PLACEHOLDER.wav",
        "SFX_02_HIT_PLACEHOLDER.wav",
    ]


def test_shot_tracker_csv_round_trip(tmp_path: Path) -> None:
    story = load_story(
        Path(__file__).resolve().parents[2] / "examples" / "poc_bins_markers" / "story.yaml"
    )
    path = tmp_path / "shot_tracker.csv"
    write_shot_tracker(path, story)
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0].keys()) == list(TRACKER_FIELDS)
    assert rows[0]["shot"] == "1"
    assert rows[0]["filename"] == "001_SHOT_01_PLACEHOLDER.mp4"


def test_tracker_includes_title_stills() -> None:
    story = load_story(
        Path(__file__).resolve().parents[2]
        / "examples"
        / "poc_transitions_titles"
        / "story.yaml"
    )
    rows = tracker_rows(story)
    title_rows = [row for row in rows if row["kind"] == "title"]
    assert title_rows[0]["filename"] == "TITLE_01_OPENING.mp4"
    assert title_rows[0]["track"] == "V2"


def test_tracker_records_cross_dissolve_source_handles() -> None:
    story = load_story(
        Path(__file__).resolve().parents[2]
        / "examples"
        / "poc_transitions_titles"
        / "story.yaml"
    )
    video_row = next(row for row in tracker_rows(story) if row["kind"] == "video")
    assert video_row["duration_frames"] == 50
    assert video_row["source_duration_frames"] == 74
    assert video_row["head_handle_frames"] == 12
    assert video_row["tail_handle_frames"] == 12
