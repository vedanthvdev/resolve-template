from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import pytest
from PIL import Image

from resolve_template.placeholders import (
    generate_placeholder_media,
    generate_placeholder_title_still,
    generate_placeholder_video,
)


def test_generated_placeholders_are_75_frames_and_three_seconds(tmp_path: Path) -> None:
    video, audio = generate_placeholder_media(
        tmp_path,
        video_filename="placeholder.mp4",
        audio_filename="placeholder.wav",
        fps=25,
        duration_frames=75,
    )

    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=nb_read_frames,r_frame_rate,width,height",
            "-of",
            "json",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    stream = json.loads(probe.stdout)["streams"][0]
    assert stream["nb_read_frames"] == "75"
    assert stream["r_frame_rate"] == "25/1"
    assert stream["width"] == 1920
    assert stream["height"] == 1080

    with wave.open(str(audio), "rb") as wav:
        assert wav.getframerate() == 48_000
        assert wav.getnchannels() == 1
        assert wav.getnframes() == 144_000


def test_generated_title_still_is_png(tmp_path: Path) -> None:
    still = generate_placeholder_title_still(
        tmp_path,
        filename="TITLE_01_OPENING.png",
        text="OPENING",
    )
    assert still.is_file()
    assert still.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert Image.open(still).size == (1920, 1080)


def test_png_title_does_not_require_ffmpeg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("resolve_template.placeholders.shutil.which", lambda _name: None)
    still = generate_placeholder_title_still(
        tmp_path,
        filename="TITLE.png",
        text="NO FFMPEG",
    )
    assert Image.open(still).size == (1920, 1080)


def test_title_text_changes_rendered_pixels(tmp_path: Path) -> None:
    opening = generate_placeholder_title_still(
        tmp_path,
        filename="opening.png",
        text="THE CAFE",
    )
    closing = generate_placeholder_title_still(
        tmp_path,
        filename="closing.png",
        text="THANK YOU",
    )
    assert opening.read_bytes() != closing.read_bytes()


def test_video_placeholder_can_include_silent_production_audio(tmp_path: Path) -> None:
    video = generate_placeholder_video(
        tmp_path,
        filename="camera.mp4",
        fps=25,
        duration_frames=50,
        linked_audio=True,
    )
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type",
            "-of",
            "json",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert [stream["codec_type"] for stream in json.loads(probe.stdout)["streams"]] == [
        "video",
        "audio",
    ]


def test_odd_frame_size_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="even integers"):
        generate_placeholder_video(
            tmp_path,
            filename="odd.mp4",
            fps=25,
            duration_frames=2,
            width=1921,
            height=1080,
        )
