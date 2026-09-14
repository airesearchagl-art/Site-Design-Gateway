# Quality debt

## D01
- id: D01
- source_wave: 0
- type: TOOL_AUTH_UNAVAILABLE
- description: Previous run's GitHub CLI returned HTTP 401; current existing PR read unavailable.
- why_deferred: Revision 2 moves remote write checks after local convergence.
- risk: Remote push and Draft PR may require human action.
- blocks_final_verify: true for remote delivery only
- required_resolution: Check existing authentication at convergence without changing credentials.
- evidence: Prior run gh HTTP 401; current anonymous PR metadata request unavailable.
- status: OPEN

## D02
- id: D02
- source_wave: 0
- type: PREVIEW_UNAVAILABLE
- description: Vercel CLI absent; no existing safe Preview connection established.
- why_deferred: Phase 0 requires a buildable structure, not deployment.
- risk: Hosted Preview behavior remains unverified.
- blocks_final_verify: false
- required_resolution: Optional later Preview verification using existing authorized configuration.
- evidence: Vercel CLI inventory: NOT INSTALLED.
- status: OPEN
