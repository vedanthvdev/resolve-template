# Known risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| No Resolve install in CI/dev | Cannot prove native `.drp` | Label packages honestly; gate later phases on `VALIDATED_IN_RESOLVE` |
| Scripting API gaps (titles, Fusion) | Fake compositions | Document gaps; never invent Fusion graphs |
| Hand-crafted `.drp` looks real | User data loss / import failures | Forbid write-by-ZIP until proven impossible via API |
| Copyrighted placeholder audio | Legal / distribution | Silent / generated audio only |
| Relink path fragility | Broken media after unzip | Stable `Placeholder_Media/` layout + one-folder relink (Phase 6) |
| Version drift (Resolve 18 vs 21) | Export/import mismatch | Pin fixture version; re-validate on upgrades |
