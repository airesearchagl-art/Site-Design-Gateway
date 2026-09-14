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
