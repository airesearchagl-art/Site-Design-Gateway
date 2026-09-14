# Run manifest

```yaml
run_id: LR-20260915-SDG-P2-001
task_packet_id: LRP-20260915-SDG-P2-001
task_packet_revision: 1
task_packet_snapshot_path: .agent-run/LR-20260915-SDG-P2-001/TASK_PACKET_SNAPSHOT.md
task_packet_digest_sha256: ba34e9db0f06a8fc7302985fb3215e21da79abdf0d9bb00be3631cd616f7908e
execution_mode: LONG_RUN_ENDURANCE
horizon: DAY
repository: airesearchagl-art/Site-Design-Gateway
working_branch: feat/phase2-constraint-engine
base_sha: eb4d3ea4711955bf137bc27137a71c3e55787787
checkpoint_policy: EACH_WAVE
resume_policy: ENABLED
quality_debt: ENABLED
final_output: DRAFT_PR
ready_for_review: PROHIBITED
merge: PROHIBITED
production: PROHIBITED
vercel_deploy: PROHIBITED
```

Original exact packet is retained locally and Git-ignored because it includes a
personal path. This manifest/evidence is a public summary, never its substitute.
Rehash original bytes before every checkpoint and resume. No prior run is modified.
Phase 2 is authorized after the independently reviewed, Human-approved Phase 1 merge.
Next Gate: Vercel Preview Smoke — REQUIRED BEFORE PHASE 3 (separate run).
