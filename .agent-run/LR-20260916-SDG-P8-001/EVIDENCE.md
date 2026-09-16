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

## Final local gates

- Final Python full suite: **891 PASS** (779 existing + 112 package tests), 33.05 seconds,
  no skipped/failed tests. `python -m pytest -p no:cacheprovider` with an ignored synthetic basetemp.
- Web: **69 PASS**, with a final `test:ci` rerun also passing. Web source and tests unchanged.
- `npm run lint` (ESLint / TypeScript), `npm run build`, `python -m pip check`: PASS.
- Explicit 128 MiB heap probes wide4 / wide6 / wide8 / deep6: **4/4 PASS**.
- Real module CLI GeoJSON create / verify: PASS, evaluated 5 / accepted 5 / rejected 0.
- Real module CLI DXF create / verify: PASS, explicit SITE layer and geometry basis,
  evaluated 2 / accepted 1 / rejected 1. Zero accepted is also exercised by integration tests.
- `git diff --check` and public boundary scan: PASS, 190 tracked/public-candidate files.
- Existing six schemas, Geometry/Massing/Search source, Web production source, dependency
  manifests and lockfile are byte-unchanged from the exact base.
- Core extension is limited to exposing the existing Decimal encoder for complete Project
  canonicalization and registering the additional Python-only manifest schema.
- Packet SHA-256 rechecked. Snapshot, raw logs and runtime packages are Git ignored.
- Git reports the pre-existing unreadable pytest-cache directory; permissions and contents
  are not changed. Tracked/public-candidate boundary scan itself completed successfully.

## Isolated mutation verification

Final controls and mutations use separate Git-archive copies of checkpoint
`a41d1623bee326ee32d88ee72843318f5fc58b8b`. Each subprocess explicitly imports that copy's `src`.
All controls PASS. All modified modules compile. Each kill is a targeted pytest assertion
failure, never a syntax/import error. Working source is not mutated.

| ID | Mutation | Assertion target |
| --- | --- | --- |
| M-P8-01 | Disable exact-byte hash guard | exact_artifact_byte_tamper_detected |
| M-P8-02 | Disable constraints input-reference guard | reference_guard_independently, constraints/project |
| M-P8-03 | Disable Search input-reference guard | reference_guard_independently, search/constraints |
| M-P8-04 | Disable early existing-output guard | exclusive_output_guard_independently |
| M-P8-05 | Remove explicit staging cleanup | interrupt_before_publication_cleans_owned_staging |
| M-P8-06 | Disable closed manifest schema/path guard | manifest_path_leak_mutation_rejected |
| M-P8-07 | Replace explicit requested heights with a different search set | manual_cli_equivalence, GeoJSON/DXF |
| M-P8-08 | Remove regular/reparse artifact guard | reparse_file_guard_without_following_it |

**8/8 KILLED**. Reference guards are tested independently because replay supplies an additional
defense. Reparse guard is tested independently of the OS's no-follow defense, in addition to
real artifact symlink integration tests.

The initial cleanup mutation survived because TemporaryDirectory garbage collection also cleans.
The test was strengthened to retain the staging owner through the assertion, proving explicit
cleanup before object finalization. The strengthened control and all eight final mutations passed.

## Delivery seal

All local gates are complete. Remaining authorized operations are final commit / clean check,
feature-branch push, inspection of that exact head's branch CI, Draft PR creation and immediate STOP.
CI is implemented for full Python/Web, pip check, lint, build, public boundary, resource probes,
and runner-temp GeoJSON/DXF create/verify with no artifact upload.
Exact delivered head, branch CI result and Draft PR URL are recorded in the completion report;
this artifact is not rewritten after Draft PR creation.
Vercel NOT TOUCHED; VMVP-001 PASS WITH TARGET ANOMALY, SDG-VP-001 BLOCKED_EXTERNAL,
D02 OPEN / PLATFORM_BLOCKED, D04 OPEN. Documentation Sync Trigger: yes.
