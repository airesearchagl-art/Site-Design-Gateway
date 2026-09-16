# Evidence

Only public synthetic sources are used. Exact packet, runtime packages, logs, screenshots and
mutation copies remain ignored. Phase 6 private workspace and Vercel are not accessed.

## Executed local gates

- Fresh baseline: exact main/base and clean tree; only fast-forward sync and prescribed feature branch.
- Exact packet SHA-256 rechecked: a13fd940edae009e870aefc438f8f57e29bef6edb414904a7434dba925f88380.
- Python: 891 PASS (`python -m pytest -p no:cacheprovider`, isolated ignored basetemp).
- Web: 142 PASS, 0 failed/skipped (69 existing + 73 new); npm run test.
- npm run lint (ESLint + TypeScript), npm run build, npm run check:boundary,
  python -m pip check, git diff --check: PASS.
- Explicit 128 MiB heap: wide4 / wide6 / wide8 / deep6 all PASS (4/4).
- Python production, all seven schemas, Phase 8 Run Package contract, dependency manifests/lockfile: unchanged.
- Test helper invokes existing Python CLI with public fixture only; canonical normal/zero packages
  are created and removed in temporary directories. No tracked runtime fixture or new dependency.

## Production browser smoke

Existing external Playwright installation, fresh headless Chromium, localhost production build only.
Public synthetic source was newly created/verified using Python under the browser's execution context.
An earlier harness attempt saw empty folder selection because the package was protected for a different
execution user. No ACL was changed. The successful audit used newly generated temporary packages, not
previous Phase 8 outputs. Initial helper syntax error was repaired before any PASS record.

- HTTP 200; initial EMPTY. Real folder filechooser and ordinary five-file fallback both PASS.
- Package integrity + shared schemas; authoritative Python disclaimer visible.
- Normal Search 5/5/0; rank 1-5 selection, GFA usage 1120/960/800/640/480, SVG and REVIEW REQUIRED PASS.
- Clear removes package/Search/selection/SVG/all input values. Delayed File-read fault injection
  confirms Clear remains EMPTY after completion; no late handoff.
- Direct sample, direct v0.1 legacy and direct v0.2 all PASS.
- Zero accepted 2/0/2: basis/caps/rejections visible, candidate usage Unavailable, no SVG.
- 390x844: document/body scrollWidth <=390; rank switching works. Screenshot visually inspected.
- Initial traffic: 11 same-origin GETs (document, CSS, seven scripts, two Next.js framework fetches),
  all without bodies. No extension traffic in the fresh browser context.
- After package selection/interactions: new requests 0; POST 0; input-bearing 0; external attempts 0.
- localStorage/sessionStorage/IndexedDB/CacheStorage all 0 at initial, selected, cleared and final stages.
  Service-worker registrations 0. App console/runtime errors 0.
- Raw reports/harness/screenshots remain ignored; no CI artifact upload.
