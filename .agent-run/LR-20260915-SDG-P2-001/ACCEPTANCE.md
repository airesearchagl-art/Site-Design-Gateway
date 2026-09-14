# Phase 2 acceptance

This is the local pre-delivery checkpoint. Exact pushed head/CI and Draft metadata
are recorded in the PR body and Completion Report after delivery. Draft creation
is the final operation; PR-triggered CI must remain explicitly unobserved.

| Requirement | Local evidence |
| --- | --- |
| Exact base and feature branch | origin/main eb4d3ea4711955bf137bc27137a71c3e55787787, fresh clean tree, Phase 1 merge observed; dedicated feature branch |
| Original contracts and sample retained | Project/Geometry schemas, synthetic inputs, dependencies, Web source and all existing tests unchanged |
| Explicit basis and area comparison | Both bases tested; missing/invalid basis rejected; selected null declared area rejected; signed declared-minus-geometry difference retained without thresholds |
| Synthetic fixed calculations | 160 m2 footprint, 1200 m2 floor area, 31 m height; reviewRequired=true |
| Divergence | Project 200 / Geometry 198: declared 160/1200, geometry 158.4/1188, difference 2 |
| Missing/null | Individual UNAVAILABLE; absent height ABSENT; 0% COMPUTED; unselected null declared area/difference preserved |
| Provenance/review | Seven statuses retained across five source fields; separate area/ratio trace; no promotion; unselected comparison source retained in overall review |
| Geometry integrity | Offline schema plus existing finite/ring/Polygon checks and recomputed area/bounds; tampering rejected |
| Determinism and references | Exact bytes SHA-256; Decimal without rounding/float conversion; fixed identifiers/order; repeated and hashseed 1/23 bytes/summary equality |
| Export/CLI | Output schema validation, exclusive new file only, fixed codes/counts, no path/input/coordinate/exception disclosure |
| Regression | Python 492 PASS (346 retained + 146 new), Web 28 PASS, lint/type/build/pip check/public scan/diff check PASS |
| Mutation probes | Isolated baseline 53 PASS; promotion/default basis/metadata bypass/fake hashes killed by 5/1/5/8 assertion failures; original source/test digests unchanged |
| Documentation and next gate | Current Phase 2 recorded; Vercel NOT RUN; Preview Smoke REQUIRED BEFORE PHASE 3 in separate run |
| Independent verification | PASS, no blocking findings. Separate-context Python 492 / Web 28 / all required local checks; independent 184 assertions and all four mutation probes PASS. Tested bytes recorded for 48 files in INDEPENDENT_VERIFICATION.md |
| Remote CI and Draft | Pending exact-head push CI, then Draft creation and immediate STOP |

No geometry/area/arithmetic/provenance/privacy defect is deferred as debt.
Inherited D01/D02/D03 and explicit unverified deployment/distribution/service items
remain documented in QUALITY_DEBT.md and the contract. No additional legal or
shape-generation feature, Web compute bridge, credentials or permissions introduced.

Documentation Sync Trigger: yes. Canonical facts changed: Phase 2 contract, explicit
area basis, three caps and trace/review states, normalized Geometry consumer,
Constraint Result schema, Decimal/exact input references, CLI/export, regression/CI
and mandatory Vercel transition gate. No Vault/Notion direct writes.

STOP — Independent Review required. Ready/merge/deployment/Phase 3 prohibited.
