# PR #2 Required Fix Repair

Same campaign: LR-20260914-SDG-P1-001 / LRP-20260914-SDG-P1-001 revision 1.
Original exact packet SHA-256 remains
93fee6c5f33b17c412a3b2141a9ada385eded1dde3185f51e51565e21291efee.
Human authorized a focused Repair Wave after Independent FULL Review. Objective,
scope and hard boundaries are unchanged; no new packet revision or Phase 2 work.

## Fresh gate

Before edits: fetch completed; PR #2 OPEN and Draft; feature branch, local HEAD,
origin feature and PR head all 03c9e775ee9828bddcb5d1daea630d153d32f55b;
origin/main 8b673999118d7109c6530399e324c8fa324f83e1; working tree clean.
Original exact packet rehashed MATCH. Repair instructions retained privately under
the ignored local directory; no personal paths or raw instruction packet published.

## Findings

| Finding | Implementation evidence | Independent closure |
| --- | --- | --- |
| RF-01 unsupported curve entity | ARC/CIRCLE/SPLINE/ELLIPSE rejected in selected modelspace/layer, alone or mixed with a valid polyline; explicit SITE ignores OTHER curves; paperspace/block definitions excluded | FIXED |
| RF-02 missing SEQEND | ordered raw POLYLINE / zero-or-more VERTEX / exactly one SEQEND checked before ezdxf.read; eight malformed sequences rejected before parser invocation; valid INSERT/ATTRIB terminator retained | FIXED |
| RF-03 source digest test weakness | exact SHA-256 of input bytes independently calculated in ten bytes/UTF-8-str cases, including Unicode, whitespace and DXF newline variants | FIXED |
| RF-04 logging restore test weakness | four fresh subprocess cases record state before runtime import; normal/exception exits restore logging disable and identical stdout/stderr objects | FIXED |

RF-03/RF-04 production behavior was already correct; only tests changed for these
findings. README, architecture, Geometry Contract, dependencies and schema unchanged.
The pre-existing blocks/paperspace test keeps its NO_BOUNDARY assertion after
checking the newly required UNSUPPORTED_CURVE result and removing the synthetic
circle from the in-memory test document. No existing test was removed or weakened.

## Regression evidence

- Before implementation: targeted regression tests reproduced 28 failures covering
  RF-01 and RF-02. Exact digest and fresh restoration tests passed existing code.
- After implementation: `python -m pytest` PASS, 346 tests (292 existing + 54 added).
  Executed using the project Python virtual environment and isolated pytest caches.
- Focused DXF/GeoJSON suite: 202 PASS. New repair cases: 54 PASS.
- `npm run test`: 28 PASS; `npm run lint`: ESLint and TypeScript PASS;
  `npm run build`: static build PASS.
- `python -m pip check`: PASS, no broken requirements.
- `npm run check:boundary`: PASS, 68 public-candidate files including the independent
  report. `git diff --check`: PASS.
- Existing unit override, mm-to-m, polygon validity, open/ambiguous boundary,
  non-zero Z, bulge/fit, width and thickness tests retained and passing.

## Isolated mutation probes

Fresh temporary source/test copies only; each process asserts that its module is
loaded from its copy. PYTHONPATH is inherited by fresh subprocess tests. No mutant
is applied to the repository sources. Copy baseline: all 54 repair cases PASS.

| Probe | Isolated change | Result |
| --- | --- | --- |
| RF-01 | bypass selected-scope curve rejection | KILLED: 20 tests failed, pytest exit 1 |
| RF-02 | remove ordered raw sequence guard | KILLED: 8 tests failed, pytest exit 1 |
| RF-03 | replace GeoJSON and DXF digest with 64 zeroes | KILLED: 10 tests failed, pytest exit 1 |
| RF-04 | replace finally logging.disable(previous) with pass | KILLED: 4 tests failed, pytest exit 1 |

These are assertion failures, not collection/import failures. Source SHA-256 values
for all BVE Python files and the two modified tests match before/after the probes.
Private scripts, copies and detailed results remain in ignored `local/`; only this
synthetic verification summary is public. No raw input/parser diagnostic dumps,
personal paths, real geometry, credentials or secrets are included in Git changes.

## Delivery boundary

Separate-context focused verifier judged all four RFs FIXED. It independently ran
202 focused tests and 44 additional synthetic adversarial cases, verified retention
of the existing tests, and inspected copy isolation plus actual mutation outputs.
See FOCUSED_REPAIR_VERIFICATION.md for per-RF evidence and source/test SHA-256.
No RF is deferred as debt. This focused verification does not replace Re-Review.
Inherited D01/D02/D03 remain unchanged. The original exact packet must be rehashed
before commit; revision 1 and its digest remain unchanged.
Then checkpoint/push the same branch, observe exact-head CI and retain Draft #2.
Record the delivery head and CI receipt in the PR body and completion report.
STOP — Independent Re-Review required before Ready / merge.
