from __future__ import annotations

import json
from pathlib import Path

import pytest

from resolve_template import cli
from resolve_template.cli import _print_build_summary, build_parser, cmd_new, main
from resolve_template.story import load_story


def test_new_creates_the_full_story_template(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "my_story"
    assert cmd_new(target) == 0
    canonical = (
        Path(__file__).resolve().parents[2] / "examples" / "full_story" / "story.yaml"
    ).read_text(encoding="utf-8")
    assert (target / "story.yaml").read_text(encoding="utf-8") == canonical
    story = load_story(target / "story.yaml")
    assert len(story["video"]) == 10
    assert {clip["track"] for clip in story["audio"]} == {"A1", "A2", "A3"}
    assert story["bins"]
    assert story["markers"]
    assert story["titles"][0]["track"] == "V2"
    assert {item["kind"] for item in story["transitions"]} == {
        "fade_from_black",
        "cross_dissolve",
        "fade_to_black",
    }
    output = capsys.readouterr().out
    assert f"resolve-template resolve-build {target / 'story.yaml'}" in output
    assert f"--output output/{target.name} --force" in output


def test_new_refuses_to_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "my_story"
    target.mkdir()
    story_path = target / "story.yaml"
    story_path.write_text("keep me", encoding="utf-8")
    assert cmd_new(target) == 1
    assert story_path.read_text(encoding="utf-8") == "keep me"


def test_human_build_summary_omits_internal_relink_path(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = {
        "status": "VALIDATED_IN_RESOLVE",
        "drp": "/package/project.drp",
        "package_zip": "/package/full_story.zip",
        "summary": {
            "timeline_name": "PRE_EDIT_MAIN",
            "duration_seconds": 10.24,
            "duration_frames": 256,
            "picture_duration_seconds": 10.0,
            "picture_duration_frames": 250,
            "fade_tail_frames": 6,
            "fps": 25.0,
            "video_clips": 10,
            "audio_clips": 4,
            "audio_by_track": {"A1": 1, "A2": 1, "A3": 2},
            "title_cards": 1,
            "transitions": ["fade_from_black", "cross_dissolve", "fade_to_black"],
        },
        "validation": {"relink_folder": "/var/folders/internal"},
    }
    _print_build_summary(result)
    output = capsys.readouterr().out
    assert "DRP: /package/project.drp" in output
    assert "ZIP: /package/full_story.zip" in output
    assert "10 seconds" in output
    assert "10.24 seconds including 6 fade-tail frames" in output
    assert "10 video, 4 audio" in output
    assert "Open this in Resolve: /package/project.drp" in output
    assert "/var/folders" not in output


def test_machine_summary_stays_json_serializable() -> None:
    result = {"status": "GENERATOR_EXISTS", "summary": {"duration_seconds": 10.0}}
    assert json.loads(json.dumps(result)) == result


def test_build_force_alias_sets_overwrite() -> None:
    args = build_parser().parse_args(["resolve-build", "story.yaml", "--force"])
    assert args.overwrite is True


def test_schema_error_prints_fields_without_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    story = tmp_path / "bad.yaml"
    story.write_text(
        """
version: "1"
timeline:
  name: PRE_EDIT_MAIN
video: []
""",
        encoding="utf-8",
    )
    assert main(["resolve-build", str(story), "--output", str(tmp_path / "out")]) == 2
    error = capsys.readouterr().err
    assert "story.fps:" in error
    assert "Traceback" not in error
    assert "story.yaml failed schema validation" not in error


def test_new_can_build_immediately(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "cafe"
    output = tmp_path / "package"
    called: list[tuple[Path, Path, bool]] = []

    def fake_build(story: Path, build_output: Path, overwrite: bool) -> int:
        called.append((story, build_output, overwrite))
        return 0

    monkeypatch.setattr(cli, "cmd_resolve_build", fake_build)
    assert cmd_new(target, build=True, output=output) == 0
    assert called == [(target / "story.yaml", output, False)]
