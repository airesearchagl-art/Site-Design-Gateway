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

All mutation baselines imported the copied engine/inputs/model under an isolated temporary root.
Mutation runs exited 1 with AssertionError, not collection/setup errors; original source/schema/test SHA-256 maps matched before and after each run.

| Mutation | Focused test in test_search_cli.py | Result |
| --- | --- | --- |
| M1 GFA ascending | test_cli_success | KILLED |
| M2 height tie descending | test_cli_tie_ranking | KILLED |
| M3 duplicate rejection removed | test_cli_invalid_heights | KILLED |
| M4 one point skipped | test_cli_success | KILLED |
| M5 accepted count +1 | test_cli_success | KILLED |
| M6 fixed fake candidate hash | test_cli_success | KILLED |
| M7 infeasible becomes whole failure | test_cli_success | KILLED |
| M8 review false | test_cli_success | KILLED |
| M9 input order preserved | test_cli_determinism_subprocess | KILLED |

## Wave 6

Fresh Independent Verifier PASS, no P0/P1/P2 findings. Independently reviewed code head 5e8af0f3fedd6efbdd3dbcd689cc36bfa57b55e3; Python 762 + 23 independent probes, Web 28, lint/type/build, pip check, boundary140 and diff-check PASS. Eighteen synthetic conditions times eight heights matched direct Phase 3 candidate bytes/hash, partition and independent ordering; 3 input permutations and extreme 1e+/-1024 boundaries checked. Phase 3 engine AST unchanged except public parser name/docstring. Verifier did not repeat mutations or remote CI. Wave 6 changes are documentation/Run records only. Final checkpoint will be pushed and its exact-head CI must PASS before Draft creation; CI/Draft receipts belong to the final execution report because Draft creation is the last operation. Vercel NOT TOUCHED, D01/D02/D03 remain OPEN, Documentation Sync Trigger yes. Unverified: hosted preview, real legal rules/projects, cross-version determinism, actual OS write faults and actual symlink creation. No remaining local implementation work.
