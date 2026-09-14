# Evidence

## Wave 6 independent findings and resolution

Independent verifier initially rejected the implementation based on synthetic probes:
lexical nonzero values underflowed during float parsing; distinct large integer
coordinates collapsed; duplicate attributes/subclasses hid geometry; fractional
integer tags were truncated; and CRLF input failed. These findings were not deferred.

Resolution: retain Decimal tokens through numeric validation, reject nonzero loss and
ordinate collisions, validate integer tokens and raw subclass/attribute structure,
reject application-data containers on polylines/vertices, compare entity counts before
and after parsing, and parse universal newlines while hashing original bytes. Reject
nonempty trailing data after EOF and require modern subclasses; R12 remains supported
with explicit missing-unit override. No geometric repair or projection was introduced.

A follow-up found Decimal's exponent-range exception; read_geojson now returns a fixed
INVALID_JSON code and the CLI has a final INTERNAL_ERROR boundary for unexpected
exceptions. Three exponent-limit subprocess regressions and a native-error probe pass.

Fixture regression exposed nondeterministic ezdxf CLASS ordering across process hash
seeds. The synthetic generator now explicitly sorts classes in addition to fixed
metadata. Generation matches tracked bytes across independent hash seeds.

Final local Python: 292 PASS (113 existing unchanged + 179 geometry: 73 GeoJSON,
75 DXF, 25 export/CLI, 6 integration). Existing Web 28, lint/types/build PASS. Web,
Project Schema, existing validation source/tests and Phase 0 historical artifacts are
unchanged from the exact base. pip check PASS; Shapely 2.1.2 / GEOS 3.13.1, ezdxf
1.4.4; NumPy 2.5.3 is transitive only.

Public boundary negative probes: 8 PASS; exactly the two synthetic geometry paths are
allowed, generic/extra geometry, runtime files and raw task snapshots are rejected.
Fixture metadata is fixed and anonymous. Snapshot SHA-256 MATCH, private probes ignored.
Remote read gate: repository PUBLIC, main remains exact base, no open Phase 1 PR.
Final independent verifier PASS at 2026-09-14T10:46:24Z; all 26 additional probes,
292 Python tests, 28 Web tests/lint/types/build, scan and diff checks confirmed.
No unresolved blocking finding. Exact-head GitHub Actions is pending at checkpoint;
its final result and Draft metadata will be recorded in the PR body/Completion Report.

## Wave 0

- Fresh fetch: origin/main exactly 8b673999118d7109c6530399e324c8fa324f83e1.
- GitHub PR #1 MERGED, mergeCommit equals expected base; mergedAt 2026-09-14T10:00:57Z.
- Clean tree verified before creating feat/phase1-geometry-foundation from origin/main.
- Exact packet SHA-256: 93fee6c5f33b17c412a3b2141a9ada385eded1dde3185f51e51565e21291efee.
- Read repository instructions, README, architecture, privacy boundary, pyproject,
  sole Project Schema, Python implementation/tests and historical resume artifacts.
- Existing authentication used for read-only merge evidence; no credential/store changes.
- No Phase 1 implementation checks run yet.

## Wave 0 checkpoint

Fresh gate complete. Implementation and required checks pending.
Snapshot rehash MATCH; branch/base MATCH.

## Wave 1 checkpoint

Contract and current-phase docs updated. Shapely 2.1.2 / ezdxf 1.4.4 editable install and imports PASS. NumPy installed only transitively. Geometry tests/export schema follow in dependent waves.
Snapshot rehash MATCH; branch/base MATCH.

## Wave 2 checkpoint

GeoJSON reader and shared ring normalization implemented; 70 geometry tests PASS. Common Shapely validity checks implemented early because safe readers depend on them. DXF import font-cache diagnostics observed during dependency smoke; eliminate disclosure in reader integration before delivery. No runtime input used.
Snapshot rehash MATCH; branch/base MATCH.

## Wave 3 checkpoint

122 geometry tests PASS (70 GeoJSON, 52 DXF). DXF m/mm and both polyline types equivalent at 220 m2. Unknown raw header units cannot inherit parser defaults; raw Z/nonfinite/zero-extrusion loss guarded. Diagnostic streams discarded and import font cache isolated to empty disposable cache; no input data or paths emitted.
Snapshot rehash MATCH; branch/base MATCH.

## Wave 4 checkpoint

256 Python tests PASS: existing 113 unchanged + geometry 143 (including 21 export/CLI tests). Independent CLI, deterministic schema-conformant export and summary, no overwrite, no argument/native diagnostic disclosure. Initial mapping import corrected to shapely.geometry before passing suite.
Snapshot rehash MATCH; branch/base MATCH.

## Wave 5 checkpoint

Synthetic fixture generation reproducible; m GeoJSON / mm DXF equivalent at 200 m2, difference 0, bounds [0,0,12,20]. 260 Python tests PASS (113 existing + 147 geometry), Web 28 PASS, lint/types/build PASS, both geometry CLI smokes PASS, public scan 64 files PASS, diff whitespace PASS. CI configured for Phase 1 branch; remote CI and independent verification pending.
Snapshot rehash MATCH; branch/base MATCH.

## Wave 6 checkpoint

Independent Verifier PASS; 292 Python (113 existing + 179 geometry), 28 Web, lint/types/build, CLI nondisclosure, reproducible synthetic equivalence at 200 m2/difference 0, public scan and diff checks PASS. All independent findings fixed and 18 reviewed file digests MATCH. Exact packet digest/branch/base MATCH. Next: push final checkpoint, require exact-head CI PASS, create Draft PR and STOP immediately. No further implementation changes. CI result and final Draft metadata go in PR body/Completion Report; no post-creation file writes.
Snapshot rehash MATCH; branch/base MATCH.
