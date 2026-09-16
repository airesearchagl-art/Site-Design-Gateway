# Evidence

Run/Packet/digest/base/branch are bound in RUN_MANIFEST.md. Exact task snapshot and local runtime evidence
are ignored, not public artifacts. Validation used only example-urban-office and synthetic test variations.
Implementation checkpoint: d90aace72746e255013daadad8dc25a465992bc3.

## Regression and boundaries

- Baseline Python1061 / Web180 PASS; current Python1165 / Web205 PASS. No existing tests removed.
- Python full suite48.64s; unique run-local basetemp with cache disabled avoids default temp access errors.
- npm lint (ESLint/TypeScript), production build (Next static routes), pip check, public boundary and diff PASS.
- 128MiB wide4/wide6/wide8/deep6:4/4 PASS, including before-parse resource protection.
- All four package CLI create/verify routes PASS. Three legacy package hashes frozen before edits and compared
  exactly, including nested Candidate0.1/Search artifacts and manifests.
- Exact-base diff confirms all fifteen legacy schemas, prior public fixtures, dependency manifests/lockfile
  unchanged. Only the specifically permitted Project/buildable synthetic inputs were added.

P12-PROJ/GEO/CON evidence: tests/test_buildable_geometry.py covers required spatial inputs, legacy/unknown
versions, closed/finite/unit/CRS/2D/duplicate/ambiguity failures, DXF reuse, contained/equal/touch/outside/crossing,
concave/hole/MultiPolygon/self-intersection, source status, canonical/site/source hashes and scalar/source binding.

P12-MASS/SEARCH evidence: tests/test_buildable_massing_search.py covers explicit required/prohibited APIs,
98m² domain, site-based BCR/FAR limits, independent final domain/site guards, unchanged site support, spatial
review OR, canonical references/context, all seven spatial tamper fields, ranking and zero accepted behavior.

P12-RUN evidence: tests/test_buildable_run.py covers deterministic six files, four versioned CLI routes,
argument rejection, five/six-file guards before artifact reads, hashes/mixed versions, rehashed semantic
tamper, traversal, outside failure without final package, mandatory Project binding and frozen legacy bytes.

P12-WEB evidence: apps/web/tests/buildable-area.test.ts plus existing tests cover direct Search0.1-0.5,
Package0.1-0.4, missing/extra/duplicate files, all-size preflight/actual recheck, buildable hash and references,
status comparison, authoritative area/review, actual TSX disclaimer rendering, SVG and cancellation.
Intentionally schema-valid but semantically invalid input remains a Python responsibility; browser tests
explicitly confirm no containment/review/geometry recomputation. D04 remains OPEN.

## Local production smoke

Dedicated temporary Playwright harness; no dependency installation or persistent environment change.
HTTP200, direct Search0.5/legacy0.4, Package0.4 folder/six-file fallback, all legacy five-file packages,
sample5/5/0, rank1-5, FAR/height/domain panels, Constraint Usage, review and legal notices PASS.
Synthetic GFA order588/392/392/294/294. BCR40m² shrink within98m² domain and height0 zero-accepted scenarios PASS.
Buildable/candidate SVG outlines and390x844 root/body overflow checks PASS. Desktop/mobile images viewed.
Clear during pending buildable arrayBuffer read leaves EMPTY and prevents late Search/panel/SVG handoff.

Initial same-origin framework/static GETs were recorded separately. After local input selection:
new requests0, POST0, input-bearing0, external0; localStorage0, sessionStorage0, IndexedDB0, CacheStorage0,
service workers0; app-origin console/runtime errors0. Browser closed; local server port confirmed closed.
This is local synthetic smoke, not a Vercel re-verification or a guarantee about every possible environment.

## Mutation verification

Each mutation used its own clean git archive of the implementation checkpoint. Python imports were asserted
to resolve inside that archive; TS/TSX syntax checks and actual targeted test imports succeeded. Every control
passed. Only targeted assertion failure (including expected fixed-code/raise assertions) counts as KILLED;
no compile/import/fixture preparation failure was counted.

| Mutation | Removed/changed guard | Assertion failures | Result |
| --- | --- | --- | --- |
| M-P12-01 | site containment | 4 | KILLED |
| M-P12-02 | convex/no-hole support | 2 | KILLED |
| M-P12-03 | Project/source status binding | 7 | KILLED |
| M-P12-04 | normalized siteReference binding | 1 | KILLED |
| M-P12-05 | target includes buildable area | 1 | KILLED |
| M-P12-06 | final domain covers | 1 | KILLED |
| M-P12-07 | Candidate buildable reference | 1 | KILLED |
| M-P12-08 | Search spatial exact copy | 7 | KILLED |
| M-P12-09 | Package0.4 six-file guard | 1 | KILLED |
| M-P12-10 | legacy five-file guard | 3 | KILLED |
| M-P12-11 | browser buildable hash | 1 | KILLED |
| M-P12-12 | rendered legal disclaimer | 1 | KILLED |
| M-P12-13 | candidate spatial review OR | 2 | KILLED |
| M-P12-14 | CacheStorage/privacy source guard | 1 | KILLED |

## Corrected checks during implementation

Initial normalized export schema check received Shapely tuple coordinates; validation now reads its actual
canonical JSON bytes so the Schema sees JSON arrays. Initial synthetic equality/review tests were corrected
to use the existing site's actual polygon and source status. Neither legacy fixture was changed.
Default pytest temp/cache permissions intermittently failed; unique ignored basetemp solved this without
credential/permission changes. A staged trailing blank line was removed before the checkpoint commit.
All affected checks were rerun and passed. No private data, Vercel or external documentation was accessed.

Documentation Sync Trigger: yes.
Reason: Phase 12 major spatial geometry / Massing domain contract.
