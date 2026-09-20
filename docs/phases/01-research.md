# Phase 1 — Research

**Status in this repo:** **complete.** Offline ZIP inspect and live API confirmation were documented; Phase 2 later proved native export and re-import.

Findings are in the files listed below so they do not need to be re-probed unless Resolve’s version or `paris.drp` changes.

## Goal

Learn how real Resolve projects are stored and which official APIs can create a genuine `.drp`.

## Files

- `fixtures/resolve_21/cafe/project.drp` — tiny native `ExportProject` from the cafe template
- `fixtures/resolve_21/cafe/MANIFEST.md`
- `fixtures/resolve_21/paris/MANIFEST.md` — historical personal export, not in git
- `docs/reference_project_analysis.md`
- `docs/file_format_observations.md`
- `docs/resolve_scripting.md`
- `docs/resolve_generation_strategy.md`
- `docs/architecture.md`
- `docs/known_risks.md`

## Commands

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/resolve-template inspect fixtures/resolve_21/cafe/project.drp
.venv/bin/python -m pytest tests/unit/test_inspect.py
```

## Gate

- Offline inspect of a real `.drp` works.
- Observations and scripting notes are written so Phase 2 can target official APIs only.

**Gate met.** Contributors inspect the committed cafe export. The original paris
archive stays outside git because it contains personal media paths.
