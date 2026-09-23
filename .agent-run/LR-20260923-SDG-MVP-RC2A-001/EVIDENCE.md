# MVP-RC2A validation evidence

All test inputs are existing public synthetic fixtures. Exact packet, runtime packages, browser harness,
screenshots and raw logs are excluded from Git. No private workspace was read.

## Local verification

- Fresh gate: main = origin/main = required base; working tree clean before edits; base tree and packet digest verified.
- Baseline: Python1165 PASS; Web205 PASS.
- Implementation: Web229 PASS (205 retained +24 UX tests). Existing UI wording assertions updated, no tests deleted.
- Final Python rerun:1165 PASS; Web229 PASS, zero failures/skips. Final-build browser scenarios repeated PASS.
- lint / production build / public boundary / pip check / diff check PASS at implementation checkpoint.
- 128MiB wide4/wide6/wide8/deep6:4/4 PASS, actual constrained Node child processes reject before parse.
- No changes to Python/tests, schemas, cases, existing validators, prompt, package manifests or lockfile.
- Public boundary scan:278 tracked/public-candidate files PASS. Final protected-path diff empty; exact packet and local evidence remain ignored.

## Canonical and browser checks

Existing Python create/verify generated all4 package versions. Every file hash matched the pre-UX evidence:
legacy0.1/0.2/0.3 matched the Phase12 legacy snapshot;0.4 matched the RC1 snapshot. No fixture bytes were rewritten.
Version0.4 GFA by authoritative rank:588/392/392/294/294 m²; footprint98m²; FAR400%; height24m.

External temporary Playwright harness used an existing runtime; no dependency install or environment setting change.
Local production HTTP200. Desktop1440x1000 initial purpose +3 actions visible; long prompt and raw technical facts hidden.
One click showed both Project conditions and Search5/5/0. Keyboard candidate selection and details toggle worked.
Package0.4 folder and6-file fallback displayed all5 ranks/KPI/SVG/domain. Legacy0.1/0.2/0.3 opened in the same viewer.
Preparation showed4 categories, three external-AI preparation steps and standalone Project validation.
390x844 actions, selected KPI, candidate switches, Advanced details worked; document/body width390, root overflow0.
Screenshots visually inspected. Deferred buildable read released after Clear could not restore stale results.

Network audit did not block requests.11 initial same-origin GETs were document, Next static assets and framework prefetch.
After user actions/file selection: new requests0, input-bearing0, POST0, external0.
Initial, sample-clear, package0.4, mobile and final-clear checks: localStorage0, sessionStorage0,
IndexedDB0, CacheStorage0, service-worker registrations0. App console/runtime errors0.
Browser closed; local production server stopped and port no longer listening.

## Publication boundary

No Vercel access or hosted mutation. D02 OPEN / PLATFORM_BLOCKED; D04 OPEN.
Remote exact-head CI and Draft PR identity belong in the completion report; this is pre-publication evidence.
Documentation Sync Trigger: yes — MVP-RC2A human-first UX milestone. No Notion/Obsidian writes.
