# Execution evidence

## Wave 0

Correct repository, clean initial tree. Fetch verified origin/main at exact expected
62529f4d3d92a03f02404f53434ea750adbb317e. Switched from retained preview branch
to existing main, ff-only confirmed up to date, then created dedicated Phase 3 branch.
Exact packet copied byte-for-byte to ignored snapshot; SHA-256 binding MATCH.
Phase 2 merge and Human Phase 3 exception are explicit in the packet. Prior closure
confirmed Git Integration DISCONNECTED and no live deployment/domain; no Vercel
operation repeated here. Public records omit private paths and deployment URLs.
Implementation/tests not yet claimed PASS. Historical Phase 0/1/2 records retained.

## Wave 1

- Added Massing contract/schema/ADR and immutable Constraint Result consumer.
- Reused Phase 2 computation path; existing 49 engine/provenance tests PASS.
- New reader checks: 6 PASS (roundtrip/canonical hash, three derived tamper cases, extreme derived decimal).
- No candidate generation or final integration PASS claimed at this checkpoint.

## Wave 2

- Reader and Massing input checks: 82 PASS after correcting a no-op review mutation fixture.
- Covered semantic/schema tampering, unavailable/absent states, strict JSON resources,
  exact Geometry reference mismatch at identical area/bounds, status binding and explicit floor height.
- Only validated immutable Constraint Result objects cross the Massing input boundary.

## Wave 3

- 23 footprint tests plus 110 Geometry geojson/normalized regressions: 133 PASS.
- Convex-only homothety, strict actual-area cap, containment, zero-underflow failure,
  deterministic context independence and exactly bounded 64 downward ULP adjustments verified.
- Extracted the existing normalize/orient operation as a shared Geometry helper; no repair added.
