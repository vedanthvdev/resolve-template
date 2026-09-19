# AI integration

Creative planning stays in `story.yaml`. Models should not emit Resolve XML or forged `.drp` bytes.

## Flow

1. Start from `examples/full_story/story.yaml` or run `resolve-template new`.
2. Model (or human) edits only `story.yaml`, conforming to
   `schemas/story-v1.schema.json`.
3. CLI: `resolve-template resolve-build path/to/story.yaml --output out --overwrite`
4. Package is labeled `GENERATOR_EXISTS` or `VALIDATED_IN_RESOLVE`.

Schema violations report field paths such as `story.video.0.track`. Semantic
checks then enforce contiguous V1 placement and valid transition targets.

Models may author `start`, `duration`, marker `at`, and transition `duration`
in seconds (`2s`, `0.24s`). V1 starts and timeline duration are derived when
omitted. `bins` may be omitted or supplied as a partial role-to-name mapping;
the canonical full story demonstrates the preferred form.

The `titles` section creates generated title-card MP4 placeholders on V2. It
does not author Resolve Text, Text+, or Fusion compositions.

## Do not

- Ask the model to reverse-engineer `.drp` internals.
- Claim a package is Resolve-validated unless that invocation exported and
  re-imported the project through Resolve.

See Phase 8: [docs/phases/08-ai-story-workflow.md](docs/phases/08-ai-story-workflow.md).
