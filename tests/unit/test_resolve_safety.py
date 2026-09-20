from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from resolve_template.resolve.roundtrip import (
    _apply_timeline_format,
    _import_media,
    _prepare_project_manager,
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
