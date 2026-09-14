# Decisions

- Wave 0: Revision 2 supersedes the overly broad environment failure classification.
  Local work proceeds before remote authentication is checked at convergence.
- Wave 0: Anonymous clone succeeded. No credential store or global config changes.
- Wave 0: Use an already-installed Python 3.12 runtime explicitly; the PATH shim
  is broken. Use a local virtual environment and workspace-local package caches.
- Wave 0: Exact task-packet bytes include an identifying local path. Preserve
  them in the required local snapshot, ignore the snapshot in Git, and publish its
  digest plus PUBLIC_CONTRACT.md. Public privacy takes precedence over publishing
  the raw packet. Resume on another machine requires the privately supplied packet.
- Wave 0: Git metadata updates use approved tool execution when sandboxed writes
  are unavailable; do not alter filesystem ACLs or GitHub permissions.
- Wave 0: Keep Web and Python independent; one root schemas/ contract is authoritative.

## Wave 1 checkpoint

Use standard npm workspaces; Next.js app root apps/web, root schemas/cases imported by the app. Document Vercel Root Directory apps/web and inclusion of sources outside that root; no deployment or project setting change. Documentation was delegated with disjoint file ownership.

## Wave 2 checkpoint

Draft 2020-12 schema is shared verbatim by Ajv and Python jsonschema. Explicit units m2/m/percent, fixed seven provenance statuses, null allowed only with unknown/review_required. No regulatory limit or geometry computation. Python source/editable only; wheel delivery is not required. Input boundary limits are 256 KiB and depth 32; no trust promotion.

## Wave 3 checkpoint

Use native node:test rather than another test framework. Keep compatible ESLint 9.39.5 while Next's React lint plugin is incompatible with v10. Set supported Next agentRules=false so dev startup does not generate/modify instruction files. Generated files were confirmed to contain only Next's own boilerplate and removed before staging.
