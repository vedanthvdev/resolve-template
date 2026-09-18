# Phase 1 — Research

**Status in this repo:** complete enough to inspect `paris.drp` without Resolve.

## Goal

Learn how real Resolve projects are stored and which official APIs can create a genuine `.drp`.

## Files

- `fixtures/resolve_21/paris/paris.drp`
- `fixtures/resolve_21/paris/MANIFEST.md`
- `docs/reference_project_analysis.md`
- `docs/file_format_observations.md`
- `docs/resolve_scripting.md`
- `docs/resolve_generation_strategy.md`
- `docs/architecture.md`
- `docs/known_risks.md`

## Commands

```bash
python3 -m pip install -e ".[dev]"
python3 -m resolve_template.cli inspect fixtures/resolve_21/paris/paris.drp
python3 -m pytest tests/unit/test_inspect.py
```

## Gate

- Offline inspect of a real `.drp` works.
- Observations and scripting notes are written so Phase 2 can target official APIs only.
