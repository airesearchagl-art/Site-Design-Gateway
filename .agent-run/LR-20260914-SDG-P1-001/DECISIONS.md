# Decisions

- Wave 6: fail closed on lossy numeric conversion or unsupported raw DXF structure.
  Decimal is only lexical validation; all geometry calculations remain Shapely.
- Wave 6: inspect all polyline/vertex structures conservatively before selection.
  Unsupported data on an unselected layer/block may reject the entire file; this
  explicit limitation is preferable to silently discarded source information.
- Wave 6: UTF-8 DXF supports LF/CRLF/CR; original bytes still define sourceReference.
- Wave 6: fix hash-dependent DXF class ordering in the synthetic generator, not by
  weakening fixture equivalence/provenance tests or adding flaky-test debt.
- Wave 6: all discovered integrity findings must close before remote delivery.

- Wave 0: latest explicit Human Phase 1 authorization supersedes current-phase
  prohibitions from Phase 0. Historical ADR/run artifacts stay unchanged.
- Wave 0: exact packet is local-only; public digest and summary enable private restore.
- Wave 0: checkpoints record their observed parent; resolve carrying commit with git log.

## Wave 0 checkpoint

Scope unchanged; next wave per queue.
Snapshot rehash MATCH; branch/base MATCH.

## Wave 1 checkpoint

Scope unchanged; next wave per queue.
Snapshot rehash MATCH; branch/base MATCH.

## Wave 2 checkpoint

Scope unchanged; next wave per queue.
Snapshot rehash MATCH; branch/base MATCH.

## Wave 3 checkpoint

Scope unchanged; next wave per queue.
Snapshot rehash MATCH; branch/base MATCH.

## Wave 4 checkpoint

Scope unchanged; next wave per queue.
Snapshot rehash MATCH; branch/base MATCH.

## Wave 5 checkpoint

Scope unchanged; next wave per queue.
Snapshot rehash MATCH; branch/base MATCH.

## Wave 6 checkpoint

Scope unchanged; next wave per queue.
Snapshot rehash MATCH; branch/base MATCH.
