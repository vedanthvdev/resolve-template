# AI integration

Creative planning stays in `story.yaml`. Models should not emit Resolve XML or forged `.drp` bytes.

## Flow

1. Start from `examples/cafe/story.yaml`, `examples/full_story/story.yaml`,
   `examples/baby_shower/story.yaml`, or `resolve-template new --template cafe`.
2. Model (or human) edits only `story.yaml`, conforming to
   `schemas/story-v1.schema.json`.
3. CLI: `resolve-template resolve-build path/to/story.yaml --output out --force`
4. Package is labeled `GENERATOR_EXISTS` or `VALIDATED_IN_RESOLVE`.

Schema violations report field paths such as `story.video.0.track`. Semantic
checks then enforce contiguous V1 placement and valid transition targets.

Models may author `start`, `duration`, marker `at`, marker `duration`, and
transition `duration` in seconds (`2s`, `0.24s`). Optional `width` and `height`
must be even integers of at least 16 and default to 1920×1080. V1 starts, timeline duration,
media filenames, labels, and clip colors are derived when omitted. Video colors
accept Resolve's full 16-value clip-color set (`Orange` through `Chocolate`). Timeline
clips are named from those labels. `bins` may
be omitted or supplied as a partial role-to-name mapping; the canonical full
story demonstrates the preferred form.

Video clips may set `linked_audio: true` when a camera-style placeholder should
carry silent production audio linked on A4. Leave it false or omit it for
video-only B-roll and for stories driven entirely by VO/music/SFX beds.

The `titles` section creates generated title-card MP4 placeholders with visible
rendered text on V2. It does not author Resolve Text, Text+, or Fusion
compositions.

## Do not

- Ask the model to reverse-engineer `.drp` internals.
- Claim a package is Resolve-validated unless that invocation exported and
  re-imported the project through Resolve.

See Phase 8: [docs/phases/08-ai-story-workflow.md](docs/phases/08-ai-story-workflow.md).
