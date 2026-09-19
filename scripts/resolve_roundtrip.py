#!/usr/bin/env python3
"""Convenience wrapper for Phase 2 Resolve round-trip experiments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from resolve_template.resolve.roundtrip import resolve_build


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve one-clip round-trip helper")
    parser.add_argument("story", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    result = resolve_build(args.story, output=args.output, overwrite=args.overwrite)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") in {"GENERATOR_EXISTS", "VALIDATED_IN_RESOLVE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
