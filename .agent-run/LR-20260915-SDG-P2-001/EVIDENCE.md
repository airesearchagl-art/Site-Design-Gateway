# Execution evidence

## Wave 0

Fetch completed; correct repository; origin/main exactly
eb4d3ea4711955bf137bc27137a71c3e55787787; working tree clean before edits.
PR #2 observed MERGED with that squash commit. Created
feat/phase2-constraint-engine directly from exact origin/main.
Read required project documents, both schemas, validation/geometry core and synthetic
project/site inputs. Original Phase 2 packet copied byte-for-byte to ignored snapshot;
SHA-256 ba34e9db0f06a8fc7302985fb3215e21da79abdf0d9bb00be3631cd616f7908e.
Public artifacts contain only the run contract and synthetic verification summaries.
No implementation checks claimed at bootstrap. Old Phase 1 evidence remains history.

## Wave 1

Defined explicit basis, signed area difference, independent null/absent states,
per-input provenance, decimal resource limits/no rounding, exact input references,
normalized metadata integrity, safe CLI/export and the separate Vercel transition gate.
Added output-only schema referencing Project condition/status definitions offline.
Schema meta-validation PASS after correcting an empty prefixItems declaration.
No changes to Project/Geometry schemas or dependencies. Source APIs and behavioral
checks follow in later waves; schema meta-validation is not engine validation.

## Wave 2

Added a normalized Geometry consumer using the existing Polygon validation, exact
metadata comparison and current-input SHA-256. Preserves encoded ring order so
float metric roundtrips do not change through reorientation. Shared bounded decimal
JSON/offline schema helpers avoid duplicating Polygon or Project schema rules.
ValidatedProject retains immutable conditions/hash only; explicit area selection
rejects absent/invalid basis and unavailable selected declared area.
New boundary tests: 59 PASS. Full Python suite: 405 PASS (346 inherited + 59 new).
Initial oversized parameter labels exceeded the Windows environment limit; fixed
to short synthetic IDs before rerunning. No input values included in case names.
Original schemas/dependencies/fixtures remain unchanged; packet digest MATCH.

## Wave 3

Implemented the three explicit decimal functions and immutable traced ConstraintResult.
Independent Context traps Inexact; caller precision/rounding/flags are preserved.
72 focused tests PASS: both bases yield 160/1200/31; 200-vs-198 yields 160/1200
or 158.4/1188 with difference 2; reverse difference -2 adds no threshold/review flag.
Null conditions are individually UNAVAILABLE, absent height ABSENT, zero ratios
COMPUTED. Long fractional expected value verified exactly, without float rounding.
Per-input provenance/state fields added with the engine; Wave 4 verifies all seven
statuses and adds deterministic export/CLI. Schema validation of computed/null/absent
results PASS. No legal rules or shape generation. Packet digest MATCH.
