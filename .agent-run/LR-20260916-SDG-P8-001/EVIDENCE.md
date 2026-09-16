# Evidence

Only executed checks are PASS. Exact packet, temporary synthetic packages, mutation copies
and raw logs are ignored. No Phase 6 private input or report is read.

## Implementation checkpoint

- Exact base and clean tree confirmed after fetch; main synchronized with ff-only.
- Baseline: Python 779 PASS; Web 69 PASS, no skipped tests.
- Added package suite: 112 PASS, including real Windows symlinks, native no-replace
  target-race test, GeoJSON/DXF manual CLI equivalence and all failure stages.
- Full Python: 891 PASS (779 existing + 112), 32.74 seconds.
- Production Web build PASS; explicit 128 MiB probes wide4/wide6/wide8/deep6 4/4 PASS.
- pip check PASS; diff check PASS; public boundary 190 candidates, no flagged content.
- Initial integration exposed Decimal/int schema validation differences in serialized Search.
  The bounded reader now preserves integer tokens for schema validation; Core semantics unchanged.
- Canonical Project is serialized before the existing manual CLI comparison, so every downstream
  reference binds packaged bytes rather than the source file's pretty-print whitespace.
- GeoJSON/DXF have the same fixture shape but different source provenance, therefore downstream
  bytes differ across formats; each format independently matches its manual pipeline exactly.
- No tracked package fixture: temporary integration/CI generation provides exact-byte regression
  without duplicating runtime artifacts in public Git.
