# Phase 7 — Transitions and titles

**Status in this repo:** **`VALIDATED_IN_RESOLVE` on 2026-09-19** with DaVinci Resolve Studio 21.1.0.

## Goal

A safe subset: cut, cross dissolve, fade from/to black, generated title cards. Native Resolve titles only if the API is proven.

## Files

- `examples/poc_transitions_titles/story.yaml`
- `src/resolve_template/story.py`
- `src/resolve_template/placeholders.py`
- `src/resolve_template/resolve/roundtrip.py`
- `tests/resolve_roundtrip/test_transitions.py`

## Commands

```bash
.venv/bin/python -m resolve_template.cli resolve-build examples/poc_transitions_titles/story.yaml \
  --output output/poc_transitions_titles --overwrite
RESOLVE_ROUNDTRIP=1 .venv/bin/python -m pytest \
  tests/resolve_roundtrip/test_transitions.py::test_cross_dissolve_roundtrip_in_resolve
```

## Gate

**Gate passed.** Re-import matched:

- Two V1 clips, no gaps
- Three semantic transition roles in the validation report. Resolve implements
  each as a `TimelineItem.AddTransition` item named `Cross Dissolve`
  (`GetType() == "transition"`):
  - fade from black: shot 1, `position=start`, `alignment=right`, 6 frames
  - edit dissolve: after shot 1, `position=end`, `alignment=center`, 6 frames
  - fade to black: shot 2, `position=end`, `alignment=right`, 6 frames
- Title card `TITLE_01_OPENING.mp4` on V2, frames 0–25
- Relink of 3 media-pool clips (2 video + 1 title card)

Cuts remain implicit: no transition item is added.

Generated package: `output/poc_transitions_titles.zip` (ignored by git).

## API gaps (do not fake Fusion)

| Attempt | Result on 21.1.0 |
|---------|------------------|
| `TimelineItem.SetFades({FadeIn, FadeOut})` | Returns true in-session; **FadeIn was 0 after ExportProject / ImportProject**. Not used in the shipping path. |
| `AddTransition` type `Dip to Color` / `Dip To Color` / `Fade` | Returned `None` |
| `AddTransition` `start` + `left` or `center` | Returned `None`; `start` + `right` works |
| `Timeline.InsertTitleIntoTimeline("Text")` | Creates a **generator** item with `GetMediaPoolItem() is None` and default duration 125. `"Text+"` and other names returned `None`. |
| Setting the displayed title string | No proven public setter; MCP `set_title_text` is undocumented `SetProperty`. Not used. |
| `InsertFusionTitleIntoTimeline` | Returned `None` for names tried. Fusion comps are not authored. |
| One-frame PNG stills | Import succeeds, but `AppendToTimeline` duration stayed 1 frame. Frozen **MP4** title cards are used so duration matches the story. |
| ffmpeg `drawtext` | Not in this Homebrew ffmpeg. Title cards are a generated drawbox band; story `text` stays in YAML. |

Source handles: clips that need a cross dissolve are generated with 12 extra frames on each end so `AddTransition` has media to pull.
