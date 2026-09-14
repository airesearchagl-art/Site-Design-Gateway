# Run manifest

```yaml
run_id: LR-20260914-SDG-P0-001
execution_mode: LONG_RUN_ENDURANCE
horizon: DAY
task_packet_id: LRP-20260914-SDG-P0-001
task_packet_revision: 2
task_packet_snapshot_path: .agent-run/LR-20260914-SDG-P0-001/TASK_PACKET_SNAPSHOT.md
task_packet_digest_sha256: b791a519d0959ae697e87cd6ff8b93a5b51d4762da87ad25a24b61549842c21c
repository: airesearchagl-art/Site-Design-Gateway
working_branch: feat/phase0-bootstrap
base_sha: 62f8925b804cb26bddf73d91096d8490f444817f
checkpoint_policy: EACH_WAVE
resume_policy: ENABLED
quality_debt: ENABLED
final_output: DRAFT_PR
ready_for_review: PROHIBITED
merge: PROHIBITED
production: PROHIBITED
```

Revision 1 stopped before any write or digest binding. Revision 2 supersedes its
failure classification; Phase 0 objective, scope and acceptance criteria remain.
The exact revision 2 bytes are preserved locally at the snapshot path above.
The packet contains a personal workstation path and MUST NOT be committed.
`PUBLIC_CONTRACT.md` is a public-safe summary, not the exact snapshot.
On another checkout, obtain the exact revision 2 packet from the human through a
private surface and restore it locally before continuing; verify this digest.

Explicit authorization covers local feature-branch commits and, after convergence,
push and a Draft PR using existing authentication. Never create or change credentials.
