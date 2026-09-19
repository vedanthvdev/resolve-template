# Known risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| No Resolve in CI | Cannot prove native `.drp` | GitHub Actions runs offline lint/tests only; live gates retain `VALIDATED_IN_RESOLVE` |
| Hand-crafted ZIP XML | Import failure / corrupt DB | Forbid write-by-ZIP; `FieldsBlob` is binary and not a public schema |
| Strict XML inspect crashes | False “invalid drp” | Inspect ZIP + header comment only; paris `project.xml` is not well-formed |
| Confusing `.drt` / archive with `.drp` | Wrong artifact shipped | `.drp` = `ExportProject`; `.drt` = timeline export; archive = media pack |
| `endFrame` off-by-one | Wrong duration | Resolve 21.1 is exclusive: use `endFrame=75` for frames 0–74 |
| Inheriting paris settings | Wrong fps (30 vs 25) | Phase 2 sets 25 fps explicitly |
| Mutating the user’s `paris` project | Data loss | Refuse builds while `paris` / `Copy of paris` is current; disposable `_rt_` projects only |
| Resolve bulk import intermittently misses a clip | Flaky or incomplete timelines | Serialize Resolve builds; import and verify exactly one path at a time |
| Crashed run leaves disposable projects | Project Manager clutter | Sweep `_rt_resolve_template_` leftovers before each run and verify deletion |
| Offline media after re-import | Empty timeline in UI | Ship `Placeholder_Media/`; paris `full` already had 346 missing files |
| Titles / Fusion via XML | Fake comps | Phase 7: generated title-card MP4s; `InsertTitle` text unproven |
| Copyrighted placeholder audio | Legal | Silent / generated audio only (paris used commercial mp3s — do not copy into packages) |
| Version drift (18 vs 21) | Export mismatch | Fixture pinned to DbAppVer `21.1.0.0014` / DbPrjVer `17` |
| External Python vs ResolvePython 3.14 | `scriptapp` fails | Follow official env vars or bundled interpreter |
| Absolute paths in `.drp` | Relink required on every machine | Phase 6 one-folder relink; never assume Desktop/paris paths |
