# Focused repair verification

Previous reviewed head: 305be0d717ed52c034caca86af407fe9fe3dfafa.
Production source changes: NONE. Original source hashes were recorded before
test edits, checked after each isolated mutation and checked after full regression.

## Test identity

| File | SHA-256 |
| --- | --- |
| tests/test_massing_engine.py | de9f8b57a084d20e0dc1874fba2a11abff8772ba77bd0d319969e0e2a61d5c9d |
| tests/test_massing_footprint.py | 8cd1a828f15c5d51800afcc2e0ad5d8f6f2f0e75a5a1f74e8ed1d9848437fccb |
| src/bve/massing/engine.py | 5af6f5d4094953d4905bfac9295fdb3c66f963c0795afd1e7f80544971f780a9 |
| src/bve/massing/model.py | 35240e1b3f7d078ee833d00e16b50f92ee11d88af8307a05b0db0dd7d18ac3ad |

All30 production source files are unchanged. SHA-256 of their sorted compact JSON
mapping from repository-relative filename to file SHA-256:
be766b1bf33133a5cf1609d8cc92744d9fa756bff75bab94b2b6771ad3777341.
All47 protected source/schema/Web/dependency files remain unchanged.
No runtime log, mutation copy or exact private packet is tracked.

## Parent isolated mutation results

Each new copy contains the current tests and unmodified source. Import origin was
asserted to be that copy's engine.py. The full focused pair ran before and after
one source mutation. JUnit cases and pytest output confirmed one DID NOT RAISE
MassingError assertion failure, no collection/setup error and no skipped tests.

| Mutation | Baseline | Mutant | Failed test |
| --- | --- | --- | --- |
| M1 remove only FAR predicate from final combined guard | 51 PASS | 50 PASS / 1 FAIL | test_final_far_cap_guard_survives_faulty_floor_count |
| M2 remove only height predicate from final combined guard | 51 PASS | 50 PASS / 1 FAIL | test_final_height_cap_guard_survives_faulty_floor_count |
| M3 replace site.covers with site.intersects | 51 PASS | 50 PASS / 1 FAIL | test_containment_rejects_partial_overlap_despite_intersection |

Result: 3/3 KILLED. Original source SHA-256 before/after identical.

## Parent full regression

- Focused:51 collected/passed; Python full:641 collected/passed.
- Failed/skipped/xfail/xpass/collection errors:0.
- Web:28 passed, failed/skipped0.
- npm lint including tsc, npm build, pip check, public boundary and git diff --check PASS.
- New tests PASS on unchanged current source; no production regression discovered.

## Independent Focused Verifier

PASS / no Required Fix. The verifier started in a new context without inherited
implementation/repair history and independently read the request, source and test diff.
It checked that each test isolates its intended final guard and preserves the other
caps, target, shape, containment and injected count-consistency requirements.

- Three independently created copies confirmed copy import origin.
- Every mutation baseline:51 passed. Every mutant:50 passed / exactly1 failed,
  with the same targeted new-test identity as the table above.
- Every failure was DID NOT RAISE MassingError; collection/setup errors0. Result3/3 KILLED.
- Independent full Python:641 collected / 641 passed; fail/skip/xfail/xpass/errors0.
- Independent Web:28 passed; fail/cancelled/skipped/todo0.
- Independent lint/tsc/build, pip check, public boundary and diff check PASS.
- Its49 selected protected files all matched previous-reviewed commit bytes before
  and after verification. The two test hashes and engine/model hashes match the table.
- Exact original Task Packet digest matched. No tracked-file, PR or Vercel mutation.

Parent and verifier protection manifests use different target sets/formats; individual
file hashes establish agreement. The full Human Focused Independent Re-Review remains
a separate gate and is not replaced by this focused implementation-stage verifier.
