from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from resolve_template.resolve.roundtrip import (
    _apply_timeline_format,
    _apply_timeline_labels,
    _import_media,
    _prepare_project_manager,
    _require_distinct_artifact_paths,
    _require_safe_output_removal,
    _require_safe_package_removal,
    resolve_build,
)


class FakeProjectManager:
    def __init__(self, current: str | None, projects: list[str]) -> None:
        self.current = SimpleNamespace(GetName=lambda: current) if current else None
        self.projects = projects
        self.deleted: list[str] = []

    def GetCurrentProject(self) -> object | None:
        return self.current

    def CloseProject(self, _project: object) -> bool:
        self.current = None
        return True

    def GetProjectListInCurrentFolder(self) -> list[str]:
        return self.projects

    def DeleteProject(self, name: str) -> bool:
        self.deleted.append(name)
        self.projects.remove(name)
        return True


def test_prepare_refuses_to_run_from_protected_project() -> None:
    manager = FakeProjectManager("paris", ["paris"])
    with pytest.raises(RuntimeError, match="protected project"):
        _prepare_project_manager(manager)
    assert manager.deleted == []


def test_prepare_deletes_only_stale_disposable_projects() -> None:
    stale = "_rt_resolve_template_old"
    manager = FakeProjectManager("baby", ["baby", "paris", stale])
    original, deleted = _prepare_project_manager(manager)
    assert original == "baby"
    assert deleted == [stale]
    assert manager.deleted == [stale]
    assert manager.projects == ["baby", "paris"]


def test_import_media_is_one_path_at_a_time_and_name_strict() -> None:
    calls: list[list[str]] = []

    def import_media(paths: list[str]) -> list[object]:
        calls.append(paths)
        return [SimpleNamespace(GetName=lambda: Path(paths[0]).name)]

    media_pool = SimpleNamespace(ImportMedia=import_media)
    imported = _import_media(media_pool, ["/media/a.mp4", "/media/b.wav"])
    assert len(imported) == 2
    assert calls == [["/media/a.mp4"], ["/media/b.wav"]]


def test_import_media_rejects_an_unexpected_name() -> None:
    item = SimpleNamespace(GetName=lambda: "renamed.mp4")
    media_pool = SimpleNamespace(ImportMedia=lambda _paths: [item])
    with pytest.raises(RuntimeError, match="renamed.mp4"):
        _import_media(media_pool, ["/media/expected.mp4"])


def test_timeline_format_rejects_silent_setting_failure() -> None:
    calls: list[tuple[str, str]] = []

    def set_setting(key: str, value: str) -> bool:
        calls.append((key, value))
        return key != "timelineResolutionWidth"

    timeline = SimpleNamespace(SetSetting=set_setting)
    with pytest.raises(RuntimeError, match="timelineResolutionWidth=3840"):
        _apply_timeline_format(timeline, width=3840, height=2160)
    assert calls[-1] == ("timelineResolutionWidth", "3840")


def _labelled_marker(color: str) -> tuple[object, ...]:
    markers: list[tuple[object, ...]] = []
    item = SimpleNamespace(
        SetName=lambda _name: True,
        GetName=lambda: "Interview",
        SetClipColor=lambda value: value == color,
        AddMarker=lambda *args: markers.append(args) or True,
    )
    _apply_timeline_labels(
        [item],
        [
            {
                "shot": 1,
                "filename": "interview.mp4",
                "label": "Interview",
                "color": color,
            }
        ],
    )
    return markers[0]


def test_clip_only_color_falls_back_to_a_valid_marker_color() -> None:
    assert _labelled_marker("Orange") == (0, "Blue", "Interview", "Shot 1", 1)


def test_shared_color_still_labels_the_marker_to_match_the_clip() -> None:
    assert _labelled_marker("Purple") == (0, "Purple", "Interview", "Shot 1", 1)


def test_force_refuses_to_delete_directory_containing_story(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    story = source / "story.yaml"
    story.write_text(
        """
version: "1"
fps: 25
timeline:
  name: SAFE
  duration_frames: 25
video:
  - shot: 1
    track: V1
    start_frame: 0
    duration_frames: 25
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsafe output directory"):
        resolve_build(story, output=source, overwrite=True)
    assert story.is_file()


@pytest.mark.parametrize("target", [Path("/"), Path.home(), Path.cwd()])
def test_unsafe_output_roots_are_rejected(target: Path, tmp_path: Path) -> None:
    story = tmp_path / "story.yaml"
    story.touch()
    with pytest.raises(ValueError, match="unsafe output directory"):
        _require_safe_output_removal(story, target)


def test_symlinked_output_is_rejected(tmp_path: Path) -> None:
    story = tmp_path / "story.yaml"
    story.touch()
    target = tmp_path / "target"
    target.mkdir()
    output = tmp_path / "output"
    output.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symlinked output directory"):
        _require_safe_output_removal(story, output)


def test_package_cannot_replace_source_story(tmp_path: Path) -> None:
    story = tmp_path / "story.zip"
    story.touch()
    output = tmp_path / "story.build"
    with pytest.raises(ValueError, match="distinct paths"):
        _require_distinct_artifact_paths(story, output, output.with_suffix(".zip"))


def test_package_directory_is_not_unlinked(tmp_path: Path) -> None:
    story = tmp_path / "story.yaml"
    story.touch()
    package = tmp_path / "output.zip"
    package.mkdir()
    with pytest.raises(ValueError, match="package directory"):
        _require_safe_package_removal(story, package)


def test_existing_package_fails_before_output_is_created(tmp_path: Path) -> None:
    story = tmp_path / "story.yaml"
    story.write_text(
        """
version: "1"
fps: 25
timeline:
  name: SAFE
  duration_frames: 25
video:
  - shot: 1
    track: V1
    start_frame: 0
    duration_frames: 25
""",
        encoding="utf-8",
    )
    output = tmp_path / "output"
    output.with_suffix(".zip").touch()

    with pytest.raises(FileExistsError, match="Package already exists"):
        resolve_build(story, output=output)
    assert not output.exists()
