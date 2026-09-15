# PR 6 Focused Safety Repair

Previous independently reviewed head: `182501a589b8daef9cc4429c38e736ef083fdbe1`.
Base: `2abb5c8a8508eacdbf629466c4f9726c85a94f16`.
Run `LR-20260915-SDG-P5-001`; packet `LRP-20260915-SDG-P5-001`, revision 1,
SHA-256 `d685b90ea2cf98ac3014fa0f74c7c54caa915b822f945b62cbb473b5cea0ed72`.
The exact ignored packet was rehashed and unchanged. The focused repair stays in its scope.

## Fresh Gate

Local branch, local HEAD, remote feature branch and PR head matched the previous reviewed head.
Local/remote main and PR base matched the base above; tracked tree was clean.
PR 6 was OPEN, Draft, unmerged. No credentials, permissions or Vercel settings changed.

## Superseding review evidence

Independent FULL Review classified the previous head as **B: P1 Blocker + P2 Required Fix**.
Earlier verifier PASS records remain historical evidence, not the current repair verdict.
The earlier 4 MB memory result was reproduced, but did not cover the later 6 MB OOM case.
The previous privacy source guard did not cover Cache API; the earlier contrary claim is superseded here.

## RF-P5-01 — resource amplification

Root cause: JSON.parse materialized the full input before node/depth screening; array key
enumeration could allocate before traversal stopped. A 6,000,003-byte wide array and a
6,000,001-byte deeply nested array crashed under a 128 MiB Node heap during independent review.

Repair: a single-pass raw-text resource preflight now runs after byte/UTF-8 checks and before
JSON.parse. It stores only quote/escape/atom state and at most 65 container-context entries.
It counts values, including root and overwritten duplicate member values, but not object keys
or structure characters inside strings. It creates no parsed graph or token array, performs no
schema/semantic checks, and leaves below-budget syntax errors to JSON.parse.
Values above 250,000 or depth above 64 (root zero) return VIEWER_LIMIT / NOT_CHECKED before parsing.
Post-parse checks remain; array traversal uses numeric iteration without whole-array key enumeration.

Explicit fresh subprocess results with `--max-old-space-size=128`:

| Case | Bytes | Result | Exit | JSON.parse calls |
| --- | ---: | --- | ---: | ---: |
| old wide, 2,000,001 elements | 4,000,003 | VIEWER_LIMIT / NOT_CHECKED | 0 | 0 |
| prior wide OOM, 3,000,001 elements | 6,000,003 | VIEWER_LIMIT / NOT_CHECKED | 0 | 0 |
| wide, 4,000,001 elements | 8,000,003 | VIEWER_LIMIT / NOT_CHECKED | 0 | 0 |
| prior deep OOM, depth 3,000,000 | 6,000,001 | VIEWER_LIMIT / NOT_CHECKED | 0 | 0 |

The Web suite runs each case in its own 128 MiB child process. CI also has an explicit
summary-only step running all four commands with the same heap flag; no input/log artifact upload.
Boundary tests cover 249,999/250,000/250,001 values, arrays/objects, depth64/65 with primitive and
empty-container leaves, strings/escapes/Unicode, duplicate members, malformed syntax, and exact 8 MiB.

## RF-P5-02 — Cache API source guard

The real recursive Web source scan now prohibits `caches` and `CacheStorage` along with all
existing network/storage/realtime tokens. Console calls are also guarded. The guard-presence
test checks the expanded list, but does not replace the real source scan.

Isolated copies started with all 57 Web tests passing. Adding `caches.open` to Web source or,
separately, a `CacheStorage` reference caused the source-scan assertion to fail (not compilation).
Removing Cache regexes permits the injected source through that scanner, while the guard-presence
test then fails. This confirms both the concrete API detection and regression of the guard itself.
Current production Web source has no input transmission, persistence or console-output API added.

## Mutation verification

| Mutation | Result |
| --- | --- |
| M-P5-R1 raw preflight bypass | KILLED: parse-before-rejection/resource assertions |
| M-P5-R2 preflight node budget disabled | KILLED: node/pre-parse assertions |
| M-P5-R3 Cache source guard removed | KILLED: guard-presence assertion; injected Cache only passes the weakened scanner |
| M-P5-R4 actual-buffer byte recheck removed | KILLED: oversize malformed-UTF-8 classification assertion |
| Additional depth budget disabled | KILLED |
| Additional caches.open source injection | KILLED: source-scan assertion |
| Additional CacheStorage-only source injection | KILLED: source-scan assertion |

Each copy baseline: 57 PASS. Every mutant failed by targeted assertion, collection/setup errors 0.
Original source/tests/schema/fixture/dependency hashes remained unchanged across the mutations.
Raw local probes and mutation logs remain Git ignored.

## P3 advisories

Responsive: FIXED with one CSS containing-block rule on the candidate table scroller.
The previous independent 390px measurement was documentElement clientWidth375 / scrollWidth936;
body-only375/375 did not prove root overflow was absent. This corrects the prior PR/Run assertion.
Fresh production browser smoke now measured documentElement375/375 and body375/375, both initially
and after keyboard Rank3 selection; candidate table250/984 retains its internal scroller.
The screenshot retained the warning, controls and selected candidate. SVG was present;
Clear returned EMPTY and removed SVG. Desktop1280 requested width measured root1265/1265 with 5 rows.

Actual-buffer: HARDENED. A reported size1 / actual buffer >8 MiB containing invalid UTF-8 must
return VIEWER_LIMIT / NOT_CHECKED before decode. Exact8 MiB and one-byte-under manageable inputs PASS.
This advisory hardening is separate from RF-P5-01/RF-P5-02 closure.

Browser caveat: extension Sentry/CDN messages and two unattributed message-channel errors were
observed; console-wide zero is not claimed. Dynamic network/storage inspection remains unavailable
in this browser harness. No input-bearing network absence is inferred from static tests alone.

## Regression and focused verifier

- Web: 46 previous + 11 added = **57 PASS**, fail/skip/cancel/todo 0.
- Python: **763 PASS**, fail/skip/xfail/xpass/collection errors 0.
- ESLint, TypeScript, production build and pip check: PASS.
- Public boundary: PASS, 160 tracked/public-candidate files. Working diff check: PASS.
- Separate-context Independent Focused Verifier: PASS on the frozen repair source. It independently
  ran Web57/Python763, old wide4/prior wide6/deep6 under 128 MiB (exit0, parse calls0), 9,000 seeded
  node/depth/escape comparisons, and a manageable 6,499,975-byte/250,000-node object without OOM.
  Three independent real-source Cache injections each produced 56 PASS / 1 privacy assertion FAIL,
  collection errors0. All 89 source/test/schema/fixture/dependency files were unchanged before/after.
  Aggregate SHA-256: `8c95d681b0eddf59aaae3ecd895238712a95d972b2692d55d1025db08d888174`.
  Its ignored report SHA-256 is `ee1ec2236560cb44e3232e61cb8b0436b9323ab8b9449c0845d2945553cf238a`.
  Browser/lint/build/remote CI and final commit state were outside that verifier's execution scope.
- No schema, Python Core, canonical fixture, dependency, ranking/selection/SVG behavior or public byte limit changed.
- This record is the pre-push repair snapshot. The new commit SHA and executed exact-head CI result
  will be recorded in the appended PR repair section and completion report after push.

## Human boundary

Vercel NOT TOUCHED. SDG-VP-001 BLOCKED_EXTERNAL; D02 OPEN / PLATFORM_BLOCKED; Git Integration
DISCONNECTED is inherited without a Vercel live query. D04 remains OPEN.
Documentation Sync Trigger: yes. No Notion/Obsidian write.
STOP after focused repair delivery; Human Focused Independent Re-Review is required.
The repair verifier does not replace that review. Ready, merge and Phase 6 remain prohibited.
