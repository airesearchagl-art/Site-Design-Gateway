# Focused test hardening repair

Run: LR-20260915-SDG-P3-001. Task Packet LRP-20260915-SDG-P3-001,
Revision 1 retained; exact packet SHA-256 remains
67ccd7881329c13616437f3e124cdfe2e095d5926e89de5cb10bfd879af0152a.

Previous reviewed head: 305be0d717ed52c034caca86af407fe9fe3dfafa.
Base: 62529f4d3d92a03f02404f53434ea750adbb317e.
Fresh Gate confirmed clean tree, the expected feature branch, equal local/remote/PR
heads, and PR 4 OPEN / Draft / merged=false. Existing push and PR CI were SUCCESS.

Human supplied Independent FULL Review result: B, two Required Fixes.
This repair adds regression coverage for existing safety guards. It does not change
the Phase 3 objective, Task Packet revision or production implementation.

## RF-P3-01: independent final FAR and height guard tests

- FAR: generate a valid synthetic baseline with explicit floor height3, then replace
  floor count with8. Actual footprint is within BCR/target and inside site, height24
  is below31, but GFA exceeds1200. Only floor-count consistency is fault-injected
  to return8. The final FAR guard must raise GEOMETRY_GENERATION_FAILED.
- Height: generate with explicit floor height4.5, replace floor count with7. GFA is
  below1200, footprint is within BCR/target and inside site, but height31.5 exceeds31.
  Only floor-count consistency is fault-injected to return7. The final height guard
  must raise GEOMETRY_GENERATION_FAILED.
- Each test asserts the other caps, target, geometry and count invariants before
  checking its guard. Removing only its guard makes only that new test fail.

## RF-P3-02: strict containment with partial overlap

A synthetic 4m2 convex rectangle crosses a synthetic square site boundary.
The test explicitly asserts intersects=true, covers=false, validity, convexity,
no holes, finite 2D coordinates, positive area and area below target100.
The containment guard must raise GEOMETRY_GENERATION_FAILED. Replacing covers
with intersects makes this new test fail.

## Scope and verification

Production source changes: NONE. Changes are the two test files and Run evidence.
Existing strategies, supported geometry, constraints, schema, Web, dependencies,
floor arithmetic, review propagation and deterministic output remain unchanged.

Parent focused run: 51 collected / 51 passed. Full Python: 641 collected / 641 passed
(previous638 + three added cases). Fail/skip/xfail/xpass/collection error: all0.
Web:28 passed; lint/tsc/build, pip check, public boundary and diff check PASS.
Three isolated mutations: 3/3 KILLED by assertion failure, collection errors0.
See FOCUSED_REPAIR_VERIFICATION.md for hashes and independent verification.

This repair checkpoint precedes remote delivery. After push, local/origin/PR must
agree on the repair commit and both available push/PR CI must succeed. Their exact
head and run URLs are recorded in the PR body and completion report. Existing PR
history is preserved; no new PR, comment or Formal Review is posted.

Vercel NOT TOUCHED. SDG-VP-001 BLOCKED_EXTERNAL; D02 OPEN / PLATFORM_BLOCKED;
Git Integration DISCONNECTED and Human Phase 3 exception AUTHORIZED are retained.
Documentation Sync Trigger: yes.
Human Gate: STOP — Focused Independent Re-Review required after delivery.
