# Evidence

Only synthetic, public-safe summaries belong here. Never paste raw runtime inputs,
credentials, identifying workstation paths or complete environment output.

## Wave 0 — fresh gate and initialization

- Anonymous HTTPS clone: PASS, no credential changes.
- Origin: https://github.com/airesearchagl-art/Site-Design-Gateway.git
- Initial HEAD and origin/main: 62f8925b804cb26bddf73d91096d8490f444817f.
- Initial branch: main; worktree clean; tracked files: README.md only.
- Existing branches: main and origin/main only. Feature branch created afterward.
- Current branch: feat/phase0-bootstrap; base preserved.
- Project instructions: human-provided instructions and existing global AGENTS read.
  No repository AGENTS, test config or project instructions existed at the base.
- Vault: Implementation_Task_Prompt and Codex_Capability_Tier_Orchestration read-only.
  Long_Run_Development_Route and Long_Run_Task_Packet not present at requested paths.
  Vault was not cloned, modified or pushed; Notion untouched.
- Node 24.15.0 / npm 11.12.1 / GitHub CLI 2.96.0 available. Vercel CLI absent.
- PATH Python shim fails (local execution); no py launcher. Existing bundled
  Python 3.12.14 / pip 26.2.1 works without system configuration changes.
- npm metadata fetch failed because the default cache is not writable; next
  strategy is a workspace-local cache, not a permission change.
- Git ignore-file warning under sandbox; normal approved Git gate confirmed clean.
  A NUL exclude-file experiment failed, was abandoned, and is not used.
- Git feature-branch creation succeeded through the approved execution boundary.
- Existing PR metadata unavailable through anonymous local request; deferred.
- Network boundary: public GitHub/npm/package documentation; no project inputs sent.
- Filesystem boundary: repository writes only; Git metadata uses approved commands.
- Exact revision 2 snapshot SHA-256: b791a519d0959ae697e87cd6ff8b93a5b51d4762da87ad25a24b61549842c21c.
- Snapshot is ignored; no exact task-packet contents will be staged or published.

## Wave 1 checkpoint

Foundation docs/AGENTS reviewed against public/private and Phase 0 boundaries. git diff --check PASS. .env/example policy and exact snapshot exclusion checked. Existing Python 3.12.14 created .venv successfully. npm metadata requests with workspace-local cache succeeded: Next 16.3.5, React 19.3.0, Ajv 8.20.0.

Snapshot SHA-256 recheck: MATCH (b791a519d0959ae697e87cd6ff8b93a5b51d4762da87ad25a24b61549842c21c).

## Wave 2 checkpoint

Python worker reports 103 passed in 2.38s; sample CLI PASS errors=0; invalid input CLI FAIL errors=5 exit 1; import PASS. Lead reviewed package source, schema loading and safe CLI output. Installed jsonschema 4.26.0 / pytest 8.4.2 in local venv. Web unit tests already 26 PASS; complete Web checkpoint follows.

Snapshot SHA-256 recheck: MATCH (b791a519d0959ae697e87cd6ff8b93a5b51d4762da87ad25a24b61549842c21c).

## Wave 3 checkpoint

Lead reran Python with workspace-local temp/cache: 103 passed in 1.91s; sample PASS errors=0. Web node:test: 26 passed. npm audit after install: 0 vulnerabilities. Lint/TypeScript PASS. Turbopack build compiled/static prerender PASS. agent-browser desktop and 390px mobile smoke PASS with synthetic-only inputs. Clipboard button reports copied. VALID/INVALID/REVIEW_REQUIRED observed. Invalid enum path /site/area/status displayed. Malformed JSON error does not echo input. JSON operations: No requests captured, zero browser storage keys, no page exceptions/overlay. Local screenshots are excluded from public Git. React checklist: client events for browser APIs, stable keys, no effects/network, accessible labels/live results and native disabled controls.

Snapshot SHA-256 recheck: MATCH (b791a519d0959ae697e87cd6ff8b93a5b51d4762da87ad25a24b61549842c21c).
