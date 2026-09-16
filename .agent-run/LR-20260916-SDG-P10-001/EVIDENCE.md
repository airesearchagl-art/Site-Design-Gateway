# Evidence

Only public synthetic example-urban-office data used. Ignored exact snapshot digest is in RUN_MANIFEST.md.
Baseline: Python891 / Web142 PASS. Added76 Python /17 Web cases: current967 /159 PASS.
Full Python command: python -m pytest -p no:cacheprovider --basetemp=<ignored-local> --tb=short.
The pre-existing inaccessible pytest cache was bypassed, without ACL changes or deletion.
Web test/lint/build PASS. Build static / and not-found only. New dependencies NONE.
wide4/wide6/wide8/deep6 each PASS at128 MiB. pip check / boundary scan / git diff --check PASS.
Legacy base archive generated fresh Project0.1 package; all5 frozen hashes match current pipeline.
New Project0.2 CLI create+verify: Package0.2,5/5/0, FAR400%, GFA cap800mﾂｲ; candidate GFA800/800/800/640/480.
Legacy CLI create+verify Package0.1 also PASS; no upconversion.

Local production Playwright: HTTP200, directSearch0.1/0.2/0.3, Package0.2 folder and0.1 files,
base/additional/status/effective/IDs/legal notices, Rank1..5 usage/SVG, review, tie IDs,
0% FAR2/0/2, Clear,390x844 no root overflow PASS. Desktop/mobile screenshots visually reviewed.
Initial framework static GET assets are separate from input interactions.
After first local selection: new requests0, POST0, body/input-bearing0, external0.
localStorage/sessionStorage/IndexedDB/CacheStorage/ServiceWorkers0 at all checkpoints; runtime/console errors0.
Playwright uses existing external runtime only; no dependency/environment/Vercel change.
Ignored harness/report/screenshots and mutation copies stay local; no runtime artifacts committed.
First root npm start argument forwarding failed before serving; workspace start succeeded without source changes.

No private workspace access, legal coefficient lookup, Vercel or external documentation writes.
Remote CI results are recorded in PR/final report after execution.

## Mutation evidence

Source checkpoint: ba479837dd9b6971a70a1deab11a54e177fdb2e8. Each mutation used an isolated git-archive copy.
Working source unchanged. Every control PASS; AST/transpile and imports PASS; targeted assertion failure required.
Syntax/import/fixture-preparation failures are excluded.

| Mutation | Guard / behavior changed | Target | Assertion failures | Result |
| --- | --- | --- | --- | --- |
| M-P10-01 | duplicate cap ID | test_duplicate_cap_id_semantic_guard | 1 | KILLED |
| M-P10-02 | min replaced by max | test_effective_min_and_tie_order | 4 | KILLED |
| M-P10-03 | null ignored instead of fail closed | test_unknown_cap_fails_closed | 3 | KILLED |
| M-P10-04 | LLM review removed | test_v2_far_review_policy | 2 | KILLED |
| M-P10-05 | Search FAR exact-copy removed | test_search_far_context_exact_copy_guard | 7 | KILLED |
| M-P10-06 | legacy package routing removed | test_manual_cli_equivalence | 2 | KILLED |
| M-P10-07 | v0.2 matrix guard removed | test_package_v2_matrix_guard | 4 | KILLED |
| M-P10-08 | viewer local min calculation | P10-WEB-10 | 1 | KILLED |
| M-P10-09 | legal disclaimer removed | P10-WEB-11 | 1 | KILLED |
| M-P10-10 | CacheStorage/privacy guard removed | privacy guard explicitly | 1 | KILLED |

The first harness assertion-parser recognized AssertionError but not pytest short-form E assert output.
That harness-only limitation was corrected; all10 were rerun in fresh copies and passed the criteria.
No production repair was needed. React checklist: pure bounded display component, no effect/derived-state duplication,
no new network/cache/storage APIs, escaped text, table headings/caption and labelled sections.

Exit: documentation-only seal, feature push, exact-head CI, Draft PR then immediate STOP.
Documentation Sync Trigger: yes. Reason: Phase 10 major schema / constraint contract.
D02 OPEN / PLATFORM_BLOCKED, D04 OPEN, VMVP-001 PASS WITH TARGET ANOMALY.

Local production server stopped after the completed audit. No runtime service remains from this run.
