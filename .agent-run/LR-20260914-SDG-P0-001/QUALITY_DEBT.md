# Quality debt

## D03
- id: D03
- source_wave: 3
- type: UPSTREAM_TOOL_COMPATIBILITY
- description: ESLint 10.10.0 fails with the React plugin shipped by eslint-config-next 16.3.5; use pinned ESLint 9.39.5.
- why_deferred: Compatible version passes lint; npm audit reports no known vulnerabilities.
- risk: ESLint 9 emits an end-of-support notice; later lint-plugin compatibility update is needed.
- blocks_final_verify: false
- required_resolution: Upgrade ESLint when the Next/React lint dependency chain supports v10 and rerun lint.
- evidence: v10 react/display-name getFilename failure; v9 lint/TypeScript PASS.
- status: OPEN

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

## Wave 1 checkpoint

D01/D02 unchanged. Python/cache local environment issues repaired without credential, OS or global configuration changes.

## Wave 2 checkpoint

D01 and D02 remain OPEN. Python tests are executable and passed, so LOCAL_PYTHON_UNAVAILABLE debt is unnecessary.

## Wave 3 checkpoint

D01/D02 unchanged. D03 below records the upstream ESLint compatibility limit.
