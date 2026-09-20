"""Generate deterministic placeholder media without using real footage or audio."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import textwrap
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def generate_placeholder_video(
    media_dir: Path,
    *,
    filename: str,
    fps: int,
    duration_frames: int,
    color: str = "black",
    linked_audio: bool = False,
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """Create a solid-color MP4, optionally with a silent production-audio stream."""
    _require_positive(fps, duration_frames)
    _require_frame_size(width, height)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to generate the placeholder MP4")

    media_dir = Path(media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    video_path = media_dir / filename
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={color}:s={width}x{height}:r={fps}",
    ]
    if linked_audio:
        command.extend(
            [
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=48000:cl=stereo",
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
            ]
        )
    command.extend(
        [
            "-frames:v",
            str(duration_frames),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
        ]
    )
    if linked_audio:
        command.extend(["-c:a", "aac", "-b:a", "128k", "-shortest"])
    command.append(str(video_path))
    subprocess.run(command, check=True)
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
    width: int = 1920,
    height: int = 1080,
) -> tuple[Path, Path]:
    """Create a black MP4 and silent WAV with an exact frame-based duration."""
    video_path = generate_placeholder_video(
        media_dir,
        filename=video_filename,
        fps=fps,
        duration_frames=duration_frames,
        width=width,
        height=height,
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
    width: int = 1920,
    height: int = 1080,
) -> Path:
    """Create a static title card with visible text."""
    if duration_frames <= 0 or fps <= 0:
        raise ValueError("fps and duration_frames must be positive")
    _require_frame_size(width, height)

    media_dir = Path(media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    still_path = media_dir / filename
    if still_path.suffix.lower() == ".png":
        _render_title_image(still_path, text, width=width, height=height)
        return still_path

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to generate the placeholder title video")

    with tempfile.TemporaryDirectory(prefix="resolve-template-title-") as temp_dir:
        source_image = Path(temp_dir) / "title.png"
        _render_title_image(source_image, text, width=width, height=height)
        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-loop",
            "1",
            "-framerate",
            str(fps),
            "-i",
            str(source_image),
            "-frames:v",
            str(duration_frames),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(still_path),
        ]
        subprocess.run(command, check=True)
    return still_path


def _render_title_image(path: Path, text: str, *, width: int, height: int) -> None:
    image = Image.new("RGB", (width, height), "#17191d")
    draw = ImageDraw.Draw(image)
    margin_x = int(width * 0.0625)
    box_top = int(height * 0.35)
    box_bottom = int(height * 0.65)
    radius = max(8, int(height * 0.033))
    draw.rounded_rectangle(
        (margin_x, box_top, width - margin_x, box_bottom),
        radius=radius,
        fill="#f4f4f2",
    )
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", max(24, int(height * 0.1)))
    except OSError:
        font = ImageFont.load_default()
    wrapped = "\n".join(textwrap.wrap(text.strip() or "TITLE", width=26))
    draw.multiline_text(
        (width // 2, height // 2),
        wrapped,
        font=font,
        fill="#17191d",
        anchor="mm",
        align="center",
        spacing=max(6, int(height * 0.014)),
    )
    image.save(path, format="PNG")


def _require_positive(fps: int, duration_frames: int) -> None:
    if fps <= 0 or duration_frames <= 0:
        raise ValueError("fps and duration_frames must be positive")


def _require_frame_size(width: int, height: int) -> None:
    if width < 16 or height < 16 or width % 2 or height % 2:
        raise ValueError("width and height must be even integers of at least 16")
