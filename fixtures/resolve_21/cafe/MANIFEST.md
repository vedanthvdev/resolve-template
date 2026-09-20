# Cafe placeholder fixture (Resolve 21.1)

## Location

`fixtures/resolve_21/cafe/project.drp`

This is a native `ProjectManager.ExportProject` archive from
`examples/cafe/story.yaml`. It contains only generated placeholder media
references, not personal footage or Desktop paths.

Do not hand-craft or patch this ZIP. Regenerate it with:

```bash
RESOLVE_ROUNDTRIP=1 .venv/bin/python -m pytest \
  tests/resolve_roundtrip/test_cafe.py::test_cafe_roundtrip_in_resolve
cp output/cafe/project.drp fixtures/resolve_21/cafe/project.drp
```

## Identity

- Size: about 35 KB
- Format: ZIP / deflate, 9 XML members
- `DbAppVer="21.1.0.0014"` `DbPrjVer="17"`
- App match: DaVinci Resolve Studio 21.1.0

## Inspect

```bash
.venv/bin/resolve-template inspect fixtures/resolve_21/cafe/project.drp
```

Expect: `is_zip: true`, 9 members, `status: INSPECT_ONLY`.

The historical paris export remains outside git. See
`fixtures/resolve_21/paris/MANIFEST.md`.
