# Evidence

Only executed checks are PASS. Private paths, runtime results and raw logs remain ignored.

## Wave 0

Fresh GitHub PR 4 MERGED with squash commit 6869e9e521d6ba490e82e1ca503e274cfd827ed9; main fast-forwarded; feature branch created at exact base with clean tree. Exact snapshot SHA-256 verified. No Vercel operations.

## Wave 1

Search contract, reused offline schema references and ADR 0005 defined. Offline Search schema construction PASS. Implementation and acceptance tests pending.

## Wave 2

Phase 3 scalar parser exposed without behavior changes. New search input tests and all four massing test modules PASS (130 selected cases). Missing/65+/numeric duplicate/invalid scalar boundaries exercised.

## Wave 3

Serial sweep reuses Phase 3 generator once per canonical point. Candidate canonical SHA-256 and duplicate identity guard added. Shared validation is outside the two-code per-point whitelist. Search input/sweep tests: 45 PASS, including synthetic, mixed, zero and actual resource limit.

## Wave 4

Public Search API, GFA/height/reference ranking, independent semantic export and fixed CLI implemented. Search input/engine/export 83 PASS; CLI 9 PASS including mixed/zero, input overwrite prevention and identical bytes for seeds 1/23/997 and shuffled/equivalent inputs. Candidate caps reused from Phase 3.

## Wave 5

Python 762 PASS = previous 641 + Phase 4 121. Web 28 PASS. npm lint (ESLint + TypeScript), build, pip check, public boundary (140 files) and git diff --check PASS. Nine isolated mutations M1..M9 KILLED by CLI test assertion failures; each pristine-copy baseline PASS, copied import paths confirmed, original source/schema/tests SHA-256 maps unchanged. Mutations: GFA order, height tie, duplicate height, skipped point, accepted count, fake candidate hash, infeasible whole-failure, review downgrade, input-order output. Initial false-review test retained an assumed Geometry status; fixture corrected to user_provided across all provenance and full suite passed. Docs/CI updated; no new dependencies, no old schema changes, no runtime artifact upload. Independent verifier and remote CI pending.
