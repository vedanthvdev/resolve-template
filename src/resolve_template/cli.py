"""CLI entrypoints for resolve-template."""

from __future__ import annotations

import argparse
import json
import sys
from importlib.resources import files
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resolve-template",
        description="Inspect Resolve projects and build placeholder templates from story.yaml",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_p = sub.add_parser("inspect", help="Inspect a .drp archive without Resolve")
    inspect_p.add_argument("drp", type=Path, help="Path to a .drp file")

    build_p = sub.add_parser(
        "resolve-build",
        help="Build the package; export a native .drp when Resolve is available",
    )
    build_p.add_argument("story", type=Path, help="Path to story.yaml")
    build_p.add_argument("--output", type=Path, default=Path("output"), help="Output directory")
    build_p.add_argument(
        "--overwrite",
        "--force",
        dest="overwrite",
        action="store_true",
        help="Replace an existing output directory and ZIP",
    )
    build_p.add_argument("--json", action="store_true", help="Print the machine-readable result")

    new_p = sub.add_parser("new", help="Create a full-story template")
    new_p.add_argument(
        "directory",
        type=Path,
        nargs="?",
        default=Path("full_story"),
        help="Directory to create (default: full_story)",
    )
    new_p.add_argument("--force", action="store_true", help="Replace an existing story.yaml")

    doctor_p = sub.add_parser("doctor", help="Check Python, ffmpeg, Resolve, and scripting")
    doctor_p.add_argument("--json", action="store_true", help="Print the machine-readable report")

    return parser


def cmd_inspect(drp: Path) -> int:
    from resolve_template.inspect_drp import inspect_drp

    result = inspect_drp(drp)
    print(json.dumps(result, indent=2))
    return 0


def cmd_resolve_build(story: Path, output: Path, overwrite: bool, as_json: bool = False) -> int:
    from resolve_template.resolve.roundtrip import resolve_build

    result = resolve_build(story, output=output, overwrite=overwrite)
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        _print_build_summary(result)
    if result.get("status") == "VALIDATED_IN_RESOLVE":
        return 0
    if result.get("status") == "GENERATOR_EXISTS":
        return 0
    return 1


def _print_build_summary(result: dict[str, Any]) -> None:
    summary = result["summary"]
    audio = summary["audio_by_track"]
    drp = result.get("drp")
    title_label = "title card" if summary["title_cards"] == 1 else "title cards"
    print(f"Build complete: {result['status']}")
    print(f"DRP: {drp or 'not created (Resolve is unavailable)'}")
    print(f"ZIP: {result['package_zip']}")
    print(
        f"Timeline: {summary['timeline_name']} — {summary['duration_seconds']:g} seconds "
        f"({summary['duration_frames']} frames at {summary['fps']:g} fps)"
    )
    print(
        f"Clips: {summary['video_clips']} video, {summary['audio_clips']} audio "
        f"(A1 {audio['A1']}, A2 {audio['A2']}, A3 {audio['A3']}), "
        f"{summary['title_cards']} generated {title_label}"
    )
    transition_names = ", ".join(name.replace("_", " ") for name in summary["transitions"])
    print(f"Transitions: {transition_names or 'cuts only'}")
    if drp:
        print(f"Open this in Resolve: {drp}")
    else:
        print("Next: start DaVinci Resolve, then rerun this command to export project.drp.")


def cmd_new(directory: Path, force: bool = False) -> int:
    story_path = directory / "story.yaml"
    if story_path.exists() and not force:
        print(f"Refusing to overwrite {story_path}; pass --force.", file=sys.stderr)
        return 1
    directory.mkdir(parents=True, exist_ok=True)
    template = files("resolve_template").joinpath("full_story.yaml").read_text(encoding="utf-8")
    story_path.write_text(template, encoding="utf-8")
    print(f"Created full-story template: {story_path.resolve()}")
    print(
        f"Build it: resolve-template resolve-build {story_path} "
        f"--output output/{directory.name} --force"
    )
    return 0


def cmd_doctor(as_json: bool = False) -> int:
    from resolve_template.doctor import doctor_report

    report = doctor_report()
    if as_json:
        print(json.dumps(report, indent=2))
    else:
        for check in report["checks"]:
            marker = "OK" if check["ok"] else "MISSING"
            print(f"[{marker}] {check['name']}: {check['detail']}")
            if check["fix"]:
                print(f"          Fix: {check['fix']}")
        print(
            "Ready for native Resolve builds."
            if report["resolve_ready"]
            else "Not ready for native Resolve builds; see fixes above."
        )
    return 0 if report["resolve_ready"] else 1


def main(argv: list[str] | None = None) -> int:
    from resolve_template.story import StoryValidationError

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            return cmd_inspect(args.drp)
        if args.command == "resolve-build":
            return cmd_resolve_build(args.story, args.output, args.overwrite, args.json)
        if args.command == "new":
            return cmd_new(args.directory, args.force)
        if args.command == "doctor":
            return cmd_doctor(args.json)
        parser.error(f"unknown command: {args.command}")
        return 2
    except StoryValidationError as exc:
        print("\n".join(exc.field_errors), file=sys.stderr)
        return 2
    except FileExistsError as exc:
        print(f"{exc} Rerun with --force.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
