"""CLI entrypoints for resolve-template."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


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
        help="Build a project via Resolve scripting (requires Resolve)",
    )
    build_p.add_argument("story", type=Path, help="Path to story.yaml")
    build_p.add_argument("--output", type=Path, default=Path("output"), help="Output directory")
    build_p.add_argument("--overwrite", action="store_true", help="Overwrite existing output")

    return parser


def cmd_inspect(drp: Path) -> int:
    from resolve_template.inspect_drp import inspect_drp

    result = inspect_drp(drp)
    print(json.dumps(result, indent=2))
    return 0


def cmd_resolve_build(story: Path, output: Path, overwrite: bool) -> int:
    from resolve_template.resolve.roundtrip import resolve_build

    result = resolve_build(story, output=output, overwrite=overwrite)
    print(json.dumps(result, indent=2))
    if result.get("status") == "VALIDATED_IN_RESOLVE":
        return 0
    if result.get("status") == "GENERATOR_EXISTS":
        print(
            "Note: Resolve was not available; no native .drp was exported.",
            file=sys.stderr,
        )
        return 0
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "inspect":
        return cmd_inspect(args.drp)
    if args.command == "resolve-build":
        return cmd_resolve_build(args.story, args.output, args.overwrite)
    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
