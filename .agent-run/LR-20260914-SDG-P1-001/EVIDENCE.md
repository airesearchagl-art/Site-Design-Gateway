# Evidence

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
