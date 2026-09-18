# Resolve scripting notes

Official DaVinci Resolve scripting is the intended path to a genuine `.drp`.

## Expected surface (to verify on a live install)

- Connect via `DaVinciResolveScript.scriptapp("Resolve")`
- Project Manager: create/load project
- Media Pool: import file / create timeline
- Timeline: append clips to V1 / A1
- Project: `ExportProject` (exact symbol/signature to confirm)

## Local setup checklist

- Resolve Studio or free Resolve with external scripting enabled
- Python that matches Blackmagic’s supported version for the install
- `RESOLVE_SCRIPT_API` / module path configured per Blackmagic docs

## Honesty

Until Phase 2 is `VALIDATED_IN_RESOLVE`, treat every scripting call as experimental.
