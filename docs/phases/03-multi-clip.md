# Phase 3 — Multi-clip timeline

**Do not start until Phase 2 is VALIDATED_IN_RESOLVE.**

## Goal

Ten sequential video placeholders on V1. Filenames, shot numbers and timeline order must match.

## Planned work

- Example spec with 10 contiguous shots
- Round-trip asserts clip count = 10 and no gaps
- Keep a single audio clip or silent bed only if it does not hide video bugs

## Gate

Re-imported timeline has 10 video clips, expected duration frames, matching names.
