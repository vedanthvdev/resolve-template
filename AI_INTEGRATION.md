# AI integration

Creative planning stays in `story.yaml`. Models should not emit Resolve XML or forged `.drp` bytes.

## Flow

1. Model (or human) writes `story.yaml` conforming to `schemas/story-v1.schema.json`.
2. CLI: `resolve-template resolve-build path/to/story.yaml --output out --overwrite`
3. Package is labeled `GENERATOR_EXISTS` or `VALIDATED_IN_RESOLVE`.

## Do not

- Ask the model to reverse-engineer `.drp` internals.
- Claim a package is Resolve-validated without the Phase 2 gate.

See Phase 8: [docs/phases/08-ai-story-workflow.md](docs/phases/08-ai-story-workflow.md).
