"""Generate deterministic placeholder media without using real footage or audio."""

from __future__ import annotations

import shutil
import subprocess
import wave
from pathlib import Path


def generate_placeholder_video(
    media_dir: Path,
    *,
    filename: str,
    fps: int,
    duration_frames: int,
    color: str = "black",
) -> Path:
    """Create a solid-color MP4 with an exact frame count."""
    _require_positive(fps, duration_frames)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to generate the placeholder MP4")

    media_dir = Path(media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    video_path = media_dir / filename
    subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={color}:s=1280x720:r={fps}",
            "-frames:v",
            str(duration_frames),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(video_path),
        ],
        check=True,
    )
    return video_path


def generate_placeholder_audio(
    media_dir: Path,
    *,
    filename: str,
    fps: int,
    duration_frames: int,
    sample_rate: int = 48_000,
) -> Path:
    """Create a silent WAV with a duration that matches `duration_frames` at `fps`."""
    _require_positive(fps, duration_frames)
    if duration_frames * sample_rate % fps:
        raise ValueError("duration does not resolve to a whole number of audio samples")

    media_dir = Path(media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    audio_path = media_dir / filename
    sample_count = duration_frames * sample_rate // fps
    silence_chunk = b"\x00\x00" * min(sample_count, sample_rate)
    with wave.open(str(audio_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        remaining = sample_count
        while remaining:
            count = min(remaining, sample_rate)
            wav.writeframesraw(silence_chunk[: count * 2])
            remaining -= count
    return audio_path


def generate_placeholder_media(
    media_dir: Path,
    *,
    video_filename: str,
    audio_filename: str,
    fps: int,
    duration_frames: int,
    sample_rate: int = 48_000,
) -> tuple[Path, Path]:
    """Create a black MP4 and silent WAV with an exact frame-based duration."""
    video_path = generate_placeholder_video(
        media_dir,
        filename=video_filename,
        fps=fps,
        duration_frames=duration_frames,
    )
    audio_path = generate_placeholder_audio(
        media_dir,
        filename=audio_filename,
        fps=fps,
        duration_frames=duration_frames,
        sample_rate=sample_rate,
    )
    return video_path, audio_path


def generate_placeholder_title_still(
    media_dir: Path,
    *,
    filename: str,
    text: str = "TITLE",
    fps: int = 25,
    duration_frames: int = 1,
) -> Path:
    """Create a static title card. PNG is one frame; MP4 uses `duration_frames`."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to generate the placeholder title still")
    if duration_frames <= 0 or fps <= 0:
        raise ValueError("fps and duration_frames must be positive")

    media_dir = Path(media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    still_path = media_dir / filename
    band = 0.20 + (sum(ord(char) for char in text) % 20) / 100
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c=0x1a1a1a:s=1280x720:r={fps}",
        "-vf",
        f"drawbox=x=80:y=300:w=1120:h=120:color=white@{band:.2f}:t=fill",
        "-frames:v",
        str(duration_frames),
    ]
    if still_path.suffix.lower() == ".mp4":
        command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    command.append(str(still_path))
    subprocess.run(command, check=True)
    return still_path


def _require_positive(fps: int, duration_frames: int) -> None:
    if fps <= 0 or duration_frames <= 0:
        raise ValueError("fps and duration_frames must be positive")
