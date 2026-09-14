# Public contract summary

Human authorized Phase 1 after independent FULL review and squash merge of Phase 0
PR #1. Start only from the exact base in RUN_MANIFEST.md with a clean tree and a fresh
fetch. Stop BASE_DRIFT on mismatch. Work only on the specified feature branch.

Implement a minimal Python geometry foundation under src/bve/geometry: explicitly
declared local Cartesian XY GeoJSON Polygon/Feature and closed DXF LWPOLYLINE/2D
POLYLINE to a valid Shapely Polygon in meters. Add Shapely and ezdxf, preserve existing
jsonschema and pytest. No general CRS conversion or speculative dependencies.

SiteGeometry retains polygon, area_m2, bounds, source_format, source_unit,
normalized_unit=m, source_status, path-free source_reference and warnings. Export
normalized GeoJSON and summary JSON to explicit runtime paths. A separate normalized
geometry schema is permitted; the Project Schema remains the sole project contract.

Require m/mm units; never guess unknown units or interpret geographic/unknown CRS as
square meters. DXF unit override is explicit and never official_verified. Multiple
boundaries require explicit selection; never select largest area. Reject curves,
open boundaries, invalid/self-intersecting/zero-area/nonfinite/non-2D polygons. No
automatic repair. Geometry calculations use Shapely alone.

Only invented synthetic fixtures in cases/example-urban-office are publishable.
DXF and GeoJSON represent the same invented site. Test meters/mm, irregular shapes,
equivalence, invalid inputs, unknown units/CRS, curves, ambiguity, tiny polygons,
orientation, duplicate closure, precision, determinism and CLI nondisclosure.

Existing Python project CLI and Web behavior remain separate and compatible. No
Web Python subprocess, compute API, TypeScript geometry copy, auth, storage, Bridge,
setbacks, massing, building rules, optimization or Phase 2 work. Input and coordinates
must not leak through stdout/stderr, exceptions, public paths, CI or runtime dumps.

Update current-phase documentation, preserve historical Phase 0 facts. No direct main
commit, force push, destructive cleanup, credential/permission changes, production,
Ready, merge or direct Vault/Notion updates. Scope expansion needs Human Gate.

Waves: 0 fresh gate/run artifacts; 1 contract/dependencies/architecture; 2 GeoJSON;
3 DXF; 4 validation/export/CLI; 5 fixtures/integration/CI/docs; 6 convergence,
Independent Verifier and Draft PR. Checkpoint every wave. Temporary external/tool
issues may be explicit debt, never geometry corruption, ignored ambiguity, invalid
adoption, privacy/security violations or main writes.

Required convergence: python -m pytest, npm run lint/test/build, boundary scan,
git diff --check, geometry/CLI integration, all 113 existing Python and 28 Web tests,
CI PASS and independent verification. Track all 25 acceptance criteria from the exact
packet. Create Draft PR titled "Phase 1: add geometry foundation" with run/digest,
base/head, contract, formats/units/limits, tests/CI, debt/unverified items, privacy and
Documentation Sync Trigger. STOP immediately after Draft creation. Final report must
include equivalence areas/difference, changed files, verifier and Human Gate:
STOP — Independent Review required. Documentation Sync Trigger: yes.
