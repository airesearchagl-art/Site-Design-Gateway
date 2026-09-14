# Phase 0 public contract summary

This public-safe summary references the exact local revision 2 packet bound by
`RUN_MANIFEST.md`. It does not replace or alter that packet.

## Objective

Reach the smallest safe, reproducible Next.js Web + JSON Schema + Python BVE Core
foundation and a Draft PR. Stop at Phase 0, even if the DAY horizon remains.

## Scope

- Next.js / TypeScript shell: generation prompt, copy, JSON file selection,
  sample loading, parse/schema issues, source statuses and disabled DXF/PDF placeholders.
- One SDG Project JSON Schema v0.1, authoritative for Web and Python.
- BVE Core importable skeleton and validation only. No compute integration.
- Anonymous synthetic `example-urban-office` fixture and minimum validation tests.
- README, AGENTS, project instructions, ignore rules, empty env example,
  public/private boundary, architecture, ADR, synthetic-only CI and run checkpoints.
- Source statuses fixed to official_verified, user_provided, drawing_derived,
  llm_researched, assumed, unknown, review_required. No automatic trust promotion.
- Schema PASS/FAIL is separate from UI VALID/INVALID/REVIEW_REQUIRED.
  Malformed or schema-invalid input is INVALID; a schema-valid input containing
  assumed/unknown/review_required is REVIEW_REQUIRED, otherwise VALID.

## Acceptance criteria

1. No confidential fixture published.
2. Work on the feature branch.
3. No direct main changes/commits.
4. Web build passes.
5. Python tests pass (record NOT RUN if the local runtime remains unavailable).
6. Schema PASS/FAIL tests exist.
7. Valid synthetic sample passes the schema.
8. Malformed JSON is rejected.
9. Invalid status is rejected.
10. Status enum is fixed.
11. All three UI outcomes work.
12. No validation-case-specific processing in Core.
13. No municipality-specific processing in Core.
14. CI does not log complete project inputs.
15. No tracked .env.
16. CI uses synthetic fixtures only.
17. Web structure supports Vercel builds.
18. README supports local setup and startup.
19. Run artifacts support resume.
20. Draft PR created.

## Boundaries and stop conditions

No real project data, identifying paths, secrets, runtime dumps, signed URLs or
private data in public Git. No Notion or Vault writes. No main commits, force push,
destructive cleanup, credential/permission changes, Ready, merge or production.
No geometry, DXF parsing, massing, search, rule engine, authentication, storage,
database, CAD/BIM bridge, optimization, design system or speculative dependencies.

Actual security/privacy/data-integrity violations or digest mismatch stop the run.
Unavailable CLI auth, Python, network, previews or remote persistence alone are
deferred checks/debt; independent safe local work continues. Remote write is checked
only after local convergence. If existing authorization is unavailable then stop
as AUTHORITY_REQUIRED_FOR_REMOTE_WRITE and preserve local commits.

## Waves

0. Anonymous clone, fresh repository/base/tree gate, branch and run initialization.
1. Safety and repository foundation.
2. Schema, synthetic fixture, Python skeleton and tests.
3. Web shell, validation, tests, lint and build.
4. CI/integration and documentation completion.
5. Convergence: no new features; diff, tests, privacy, debt and independent review.
6. Existing-authentication push, Draft PR, STOP.

Rehash the exact packet at each checkpoint. Preserve evidence and local commits.
Retry a hypothesis at most twice; use at most five repair strategies and stop
after four waves without progress. Do not hide incomplete checks.
