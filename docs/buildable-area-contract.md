# Supplied buildable area / Explicit footprint domain

Phase 12 accepts a polygon already supplied by a human, CAD or deterministic upstream calculation.
It does not derive geometry from setbacks, road boundaries, slope planes, districts or legal text.
The supplied buildable area is an explicit footprint domain. This does not prove regulatory compliance.

## Explicit version matrix

| Package | Project | Site | Buildable area | Constraint | Massing | Search | Manifest | Files |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v0.1 | 0.1 | 0.1 | absent | 0.1 | 0.1 | 0.2 | 0.1 | 5 |
| v0.2 | 0.2 | 0.1 | absent | 0.2 | 0.1 | 0.3 | 0.2 | 5 |
| v0.3 | 0.3 | 0.1 | absent | 0.3 | 0.1 | 0.4 | 0.3 | 5 |
| v0.4 | 0.4 | 0.1 | 0.1 | 0.4 | 0.2 | 0.5 | 0.4 | 6 |

No automatic upgrade, latest fallback or mixed artifacts. All fifteen legacy schemas, existing fixtures,
five-file packages and canonical bytes remain unchanged. Search0.1 remains supported for direct viewing.
Six new schemas reference the existing canonical definitions; Python and offline Ajv use the same files.

## Inputs and provenance

Project0.4 preserves every Project0.3 scalar contract and requires
`spatialConstraints.buildableArea = {kind: "explicit_buildable_area", status: <existing status>}`.
No filename, path, URL, address, client, arbitrary description or legal rule is added to this object.

`bve.spatial.read_buildable_area` reuses the existing Geometry GeoJSON/DXF readers, size and numeric limits,
unit conversion and ambiguity rejection. GeoJSON requires explicit unit, local_xy and sourceStatus.
DXF retains the existing layer/unit contract, including `user_provided` for explicit unknown-unit overrides.
Raw input can be m/mm; normalized geometry is local XY meters.

Only valid, finite, closed, positive-area, convex, hole-free single Polygon is supported. No geographic/3D
input, curves, ambiguous boundaries, MultiPolygon or repair. The convex-hull equality check is a predicate;
its result never replaces the supplied shape. No buffer(0), make_valid, snap or tolerance correction.
The site must also retain the existing convex/no-hole Massing support boundary.

Python requires `site.polygon.covers(buildable.polygon)`: complete equality and boundary touch are allowed;
any outside portion, including a very small protrusion, fails with `BUILDABLE_AREA_OUTSIDE_SITE`.
Project status and `properties.sourceStatus` must match exactly or fail with `BUILDABLE_AREA_STATUS_MISMATCH`.

The immutable `ValidatedBuildableArea` retains distinct references:

- sourceReference: exact original buildable input bytes, from the shared Geometry reader.
- siteReference: exact canonical packaged site.geojson bytes.
- reference: exact canonical normalized buildable-area.geojson bytes, including fixed role and siteReference.
- Internal Project binding: the validated Project hash, checked against Constraint0.4 in Massing/Search.

Normalized loading reuses Geometry metric validation and checks canonical bytes, shape, containment,
site reference and Project status. No original source filename or arbitrary metadata is retained.
Hashes provide artifact integrity, not authorship or truth of the declared provenance.

## Constraints, Massing and Search

Constraint0.4 changes only version/Project binding. BCR, FAR/height Decimal semantics, calculation IDs,
statuses and area selection remain unchanged. Buildable geometry is not copied into Constraint Result.
`load_constraint_result(payload)` checks internal consistency; `project=validated_project` additionally
binds to the source. Package0.4 requires the Project-bound API, as Package0.3 does.

**BCR/FAR denominators and areaBasis remain SITE-based.** Buildable area is a footprint generation domain only.
Constraint0.4 requires the explicit `buildable_area` keyword on Massing and Search; legacy constraints reject it.
Target area is min(site area, buildable area, site-based BCR cap, effective FAR total-area cap).
If target reaches the domain area, use the canonical supplied polygon; otherwise reuse existing homothetic shrink.
Final guards require BOTH buildable.covers(footprint) AND site.covers(footprint), along with all scalar caps.

Candidate0.2 uses `max_footprint_stack_v0.2` and `convex_homothetic_buildable_area_v0.1`, and binds buildableArea
in inputReferences. Floors, height and GFA keep existing semantics. Search0.5 copies scalar context and an
authoritative spatialContext with role, artifact/site/source references, status, area, review and geometry.
Export verifies exact spatial copy and every candidate reference. Ranking remains GFA descending, floor height
ascending, candidateReference final. No footprint exploration, new scoring or legal inference.

Spatial review is true for llm_researched / assumed / unknown / review_required; false from status alone for
official_verified / user_provided / drawing_derived. Candidate and Search review OR this with scalar review.
Project validation UI also flags the new spatial statuses. Existing review policies remain unchanged.
FAR0/height0 preserve completed zero-accepted Search; invalid/outside geometry is a hard input failure.

## Run Package0.4

Fixed files: manifest.json, project.json, site.geojson, buildable-area.geojson, constraints.json, search-result.json.
Legacy packages remain exactly five files and reject the additional file. Manifest0.4 adds the fixed buildableArea
artifact path/reference. It contains no clock, source path, hostname or user metadata.

```sh
python -m bve.run create --project cases/example-urban-office/project-buildable-area.json --geometry cases/example-urban-office/site.geojson --format geojson --buildable-geometry cases/example-urban-office/buildable-area.geojson --buildable-format geojson --area-basis declared_project_area --floor-height-m 4 --floor-height-m 5 --floor-height-m 6 --floor-height-m 7 --floor-height-m 8 --output runtime-data/buildable-run
python -m bve.run verify --package runtime-data/buildable-run
```

Create the runtime-data parent first; output must not exist. DXF supports --buildable-layer and --buildable-unit m|mm.
Project0.4 requires both buildable input/format; legacy projects reject every buildable argument.
All examples use public synthetic inputs. The supplied rectangle is 98m² within the 200m² site. BCR80% stays
160m², FAR400% stays800m², height24m stays24m. At 4m floor height the canonical engine produces6floors/GFA588m².

Verifier lstat-checks the directory, lists direct names, reads only bounded fixed-name manifest.json, validates
the manifest, selects its fixed file set, checks exact names and then reads constant artifact names. Manifest
paths are never used for traversal. Regular files, no links/reparse, exact hashes, matrix, canonical artifacts,
status/site binding, containment, Project-bound constraints, scalar replay and exact Search replay are required.
Creation fully verifies staging before atomic no-replace publication. Failure leaves no final package.

## Browser boundary

Search0.5 and Package0.4 are read-only. All21 schemas are registered offline. For package files, every File.size
is checked before any arrayBuffer; actual buffers are checked again. Manifest/Project256KiB, Site/Buildable/
Constraints4MiB, Search8MiB; depth64/250,000 nodes preflight precedes JSON.parse. VIEWER_LIMIT is separate from INVALID.
Browser checks schema, hashes, fixed paths, file set/version matrix, source status and artifact references.
Python `bve.run verify` remains the authoritative semantic verifier. No browser containment, polygon validity,
area/min/tie/ranking recomputation or legal verification. JavaScript Number fidelity remains D04 OPEN.

The panel displays authoritative area/status/role/review. SVG shows supplied domain and candidate in distinct
styles, using source coordinates with display-only XY viewport transformation. It never infers a site outline.
Required notices are rendered verbatim:

> The supplied buildable area is an explicit footprint domain.
> SDG did not derive this geometry from setback or slope regulations.
> This does not prove regulatory compliance.

Input remains in browser memory. No network, telemetry, persistent storage or filesystem write is added.
Clear releases package/Search/spatial/candidate/SVG/input state and cancels pending handoff through Abort/generation guards.
Only public synthetic data is used in tests, CI and local browser smoke; runtime packages are never tracked.

D02 OPEN / PLATFORM_BLOCKED; D04 OPEN. VMVP-001 PASS WITH TARGET ANOMALY is inherited only. Vercel NOT TOUCHED.
Documentation Sync Trigger: yes — Phase 12 major spatial geometry / Massing domain contract.
Final exit: Draft PR then STOP; no Ready, merge, Phase13, Notion or Obsidian writes.
