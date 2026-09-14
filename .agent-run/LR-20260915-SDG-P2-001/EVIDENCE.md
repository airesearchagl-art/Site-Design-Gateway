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

## Wave 4

65 focused tests PASS (core/provenance/export/CLI). All seven status values retained
for each of five source fields; BCR/FAR trace area plus ratio, height traces only height.
Overall review includes both compared areas; no llm_researched promotion.
Decimal result numbers are serialized without conversion to float. Output schema
validation, fixed ordering, exact input hashes and PYTHONHASHSEED 1/23 byte/summary
equality PASS. CLI permits explicit output only, rejects overwrite/duplicate arguments,
and emits counts or fixed codes with empty stderr on tested successes and failures.
No-output mode creates no files. Missing/invalid input/path and tampered metadata
fail without output artifacts. Packet digest MATCH.

## Wave 5

Full local regression: Python 492 PASS (346 existing + 146 added), Web 28 PASS,
ESLint/TypeScript/build PASS, pip check PASS, public scan 94 candidates PASS,
git diff --check PASS. No Project/Geometry schema, existing fixture, Web source,
dependency or prior test-file changes relative to exact base.
Additional checks cover output state/provenance contradictions, all-null conditions,
extreme decimal lexemes without rounding, offline schema resolution, both existing
geometry producers through the new consumer, partial write errors, CLI unexpected
exceptions and boolean schema strictness. Runtime/private markers remain temporary.
CI now includes the Phase 2 push branch, pip check, and both basis CLI paths through
temporary normalized Geometry. Remote CI is not yet observed; it is required before Draft.
README/instructions/architecture/privacy docs identify Phase 2 and the separate
Vercel Preview Smoke gate required before Phase 3. No deployment performed.

Isolated-copy mutation probes: baseline 53 PASS; llm status promotion killed by 5
failures; default area selection by 1; ignored metadata mismatch by 5; fake Project
and Geometry digests by 8. These are assertion failures, not collection errors.
Each probe verifies copy-local module import and uses isolated pytest root/cache/temp.
All source/test SHA-256 values match before/after. Scripts/logs/copies are ignored in
local/; only this synthetic summary is public. No mutant applied to the repository.
Exact packet rehash MATCH. Independent verification remains Wave 6 work.

## Wave 6

Separate-context independent verification PASS, no blocking findings. Independently
executed Python 492 (346 inherited + 146 added), Web 28, lint/type/build, pip check,
public boundary scan and diff check all PASS. Additional independent probes passed
184 assertions, including Fraction oracle arithmetic, ambient Decimal isolation,
null combinations, normalized ring integrity, offline schemas, exact hashes and CLI.
Those are supplemental assertions, not additional permanent pytest test cases.
All four isolated mutations independently re-executed and killed with 5/1/5/8
assertion failures; unmodified baseline 53 PASS. Source/test bytes were preserved.
INDEPENDENT_VERIFICATION.md binds 48 tested files by local exact-byte SHA-256;
these are explicitly distinct from Git blob hashes. Parent rechecked the bindings
before this checkpoint. Public scan after the two final reports: 96 files PASS.
Exact packet digest, branch and expected origin/main rechecked; no implementation
changes after Wave 5. ACCEPTANCE.md records contract coverage and remaining debt.

This is the final local pre-delivery checkpoint. Exact pushed head CI must succeed
before Draft creation. The PR body and Completion Report record the final head,
push CI and Draft receipt; they cannot be written back after the mandatory STOP.
PR-triggered CI, Vercel, Production and Phase 3 remain unobserved/unexecuted here.
Documentation Sync Trigger: yes. STOP — Independent Review required after Draft.
