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

## Wave 4

- Added immutable Candidate with derived actual metrics, integer stack, export validation and standalone CLI.
- 41 engine/CLI checks PASS: synthetic 7 floors / 28 m, site/BCR/FAR caps, Fraction floor oracle,
  resource limit, ambient Decimal isolation, exclusive I/O, fixed diagnostics and hash-seed determinism.
- Pipeline output bytes identical for seeds 1/23/997 and three seed-23 repetitions.
- Output schema uses offline references to the unchanged Geometry/Constraint contracts.

## Wave 5

- Full Python: 638 PASS = existing 492 + Phase 3 146. Web: 28 PASS.
- npm lint (ESLint + tsc), npm build, pip check, public boundary and git diff --check PASS.
- Existing Project/Geometry/Constraint schemas, Web sources/tests and dependency manifests unchanged.
- Synthetic actual Shapely area 160.0 m2 (not rounded to target), target160, floors7,
  floorHeight4, height28, GFA1120.0, caps160/1200/31, inside=true, reviewRequired=true.
- Shapely2.1.2 / GEOS3.13.1; candidate SHA-256
  bb37010bbae5fe9f4b85fdb2b08f28c4a129c7df3fb1ee1d53756614b53d84aa.
- CI extended with Phase 3 branch trigger and synthetic massing CLI; no Vercel job.
- Current-phase docs updated with the Human exception and retained two-attempt failure history.

### Isolated mutation verification

Every probe ran its selected test baseline PASS in a fresh copy, confirmed imports
from that copy, applied one mutation, and observed pytest assertion failure (KILLED).
Original source/test/schema SHA-256 map unchanged. No mutation touched the working source.

| Mutation | Oracle | Result |
| --- | --- | --- |
| Remove Geometry reference check | same shape/area/bounds with different input bytes | KILLED |
| Remove final maxFootprint cap check | faulty geometry-stage actual area161 with other caps fitting | KILLED |
| Remove site.covers | small outside footprint with area below target | KILLED |
| Remove concavity rejection | unsupported-site fixed-code contract | KILLED |
| Default floorHeight=4 | missing public API design input | KILLED |
| floor to ceil | independent Fraction floor oracle | KILLED |
| reviewRequired to false | synthetic inherited review flag | KILLED |
| Bypass semantic comparison | schema-valid derived cap tampering | KILLED |

Hosted state is carried from prior closure, not rechecked in Phase 3. No Vercel
operation/deployment triggered by this agent. GitHub CI observation remains pending.

## Wave 6 independent verification

Independent Verifier PASS / no Required fix on implementation head
d32cb50fceeb8f6eb5b592eb451804c753c3ad27. Exact packet hash matched and tree was clean.
Final checkpoint only adds handoff evidence; source/tests remain that verified implementation.

- 56 individual Constraint Result scalar mutations: all rejected.
- 240 varied convex-site/cap/floor-height probes: 191 generated candidates passed
  reloaded-coordinate area/containment, all caps, independent Fraction floors and repeat bytes.
- 11 GEOMETRY_GENERATION_FAILED and 38 NO_FEASIBLE_MASSING were conservative fixed-code
  failures; no out-of-site or cap-exceeding candidate was accepted.
- 15 API/binding/immutability checks and 9 CLI/privacy/exclusive-I/O checks PASS.
- Explicit 4e0 accepted. Negative scientific notation rejected without disclosure;
  separated -1e3 is argparse INVALID_ARGUMENTS, equals-form is INVALID_FLOOR_HEIGHT.
- Old schemas/Web/dependencies unchanged; no Vercel operation by verifier.
- Verifier did not duplicate parent regression/mutation runs or claim remote CI.

Limits: finite-double geometry may conservatively fail on a valid convex site.
No cross-version bit identity, source authenticity without original Project, legal
compliance, real-project verification or hosted Preview PASS is claimed.
Windows symlink rejection was simulated; OS output errors can leave a partial new file.

Required local checks and convergence are complete. Delivery must observe the
carrying commit's push CI before Draft creation. Its URL/result and Draft URL are
recorded in the PR/completion report without another source commit or post-Draft action.
Human Gate: STOP — Independent Review required after Draft creation.
