# Run state

- Run ID: LR-20260914-SDG-P0-001
- Mode: LONG_RUN_ENDURANCE
- Horizon: DAY
- Current state: RUNNING
- Repository: airesearchagl-art/Site-Design-Gateway
- Working branch: feat/phase0-bootstrap
- Base SHA: 62f8925b804cb26bddf73d91096d8490f444817f
- Current head: d1e9e339dd9eed8f8c8326bc0b54d4309f301ced (observed before checkpoint commit)
- Current wave: 2
- Last successful checkpoint: Wave 2; identify carrying commit with git log.
- Task Packet ID: LRP-20260914-SDG-P0-001
- Task Packet revision: 2
- Task Packet snapshot: .agent-run/LR-20260914-SDG-P0-001/TASK_PACKET_SNAPSHOT.md (local only)
- Task Packet SHA-256: b791a519d0959ae697e87cd6ff8b93a5b51d4762da87ad25a24b61549842c21c

## Objective

Complete the minimal safe Phase 0 foundation and reach a Draft PR. Scope and
acceptance criteria are fixed by PUBLIC_CONTRACT.md and the exact local packet.

## Acceptance Criteria

| ID | Status | Evidence |
| --- | --- | --- |
| 1 | NOT RUN | Final public content scan pending |
| 2 | PASS | Fresh gate; feature branch created |
| 3 | PASS | Main remains at expected base; no main commit |
| 4–18 | NOT RUN | Implementation and validation pending |
| 19 | PASS (local) | Exact snapshot bound; state/queue/evidence available |
| 20 | NOT RUN | Remote write deferred until convergence |

## Completed

Waves 0–2: foundation, SDG Project Schema v0.1, synthetic example-urban-office, importable BVE Core validation/CLI, Python tests.

## Current implementation state

Python source/editable package ready. Shared schema is the sole contract. Web source is being prepared independently and is not part of this checkpoint commit.

## Checks

Python worker: 103 pytest tests PASS, package import PASS, sample CLI PASS errors=0, invalid schema-as-input CLI FAIL exit 1. Covers enum, malformed JSON, units, null provenance, size/depth, nonfinite numbers, no mutation and no CLI input logging. Snapshot digest MATCH.

## Quality Debt

See QUALITY_DEBT.md. Existing PR read, remote authentication and preview unverified.

## Explicit unverified items

Web build/lint/browser; full CI; existing PRs; remote authentication/push/Draft PR; Vercel Preview; final public scan; independent verification. Python wheel distribution is outside Phase 0 support.

## Known failures

Broken PATH Python shim and default npm cache permissions are resolved for this task via explicit existing Python and local caches. No global settings changed. Remote metadata/auth and Preview remain deferred.

## Decisions

See DECISIONS.md. The exact human packet is local-only to protect personal paths.

## Files changed

schemas/, cases/example-urban-office/, pyproject.toml, src/bve/, tests/test_validation.py, README support clarification and run checkpoints. Web files remain local work in progress until Wave 3.

## Remaining tasks / Next action

Finish Web checks and browser smoke verification, integrate CI, then review all changes and remote delivery.

## Stop conditions status

No actual boundary violation observed; no main writes, secrets, private inputs,
destructive operations or remote writes. Non-hard local tool failures are repairable.

## Resume instructions

Read manifest, this state, task queue and debt. Verify repository/branch/base/tree.
Compare SHA-256 of the exact local snapshot to the manifest before any new write.
On another clone restore the exact packet privately; do not substitute the summary.
Current head records the commit observed before preparing this checkpoint. Resolve
the carrying checkpoint commit using git log; never rewrite checkpoint history.
