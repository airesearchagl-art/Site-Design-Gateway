import assert from "node:assert/strict";
import test from "node:test";
import sample from "../../../cases/example-urban-office/search-result.json" with { type: "json" };
import type { SearchResultDocument } from "../src/lib/search-validation.ts";
import {
  findCandidate,
  footprintPreview,
  initialCandidate,
  shortenReference,
  toSearchViewModel,
} from "../src/lib/search-view.ts";

function model() {
  return toSearchViewModel(structuredClone(sample) as SearchResultDocument);
}

test("five accepted candidates preserve rank order and display metrics", () => {
  const result = model();
  assert.deepEqual(result.candidates.map((candidate) => candidate.rank), [1, 2, 3, 4, 5]);
  assert.deepEqual(result.candidates.map((candidate) => candidate.floorHeightM), [4, 5, 6, 7, 8]);
  assert.deepEqual(result.candidates.map((candidate) => candidate.grossFloorAreaM2), [1120, 960, 800, 640, 480]);
  assert.equal(result.summary.reviewRequired, true);
});

test("zero accepted and mixed rejection remain successful view models", () => {
  const zero = structuredClone(sample) as SearchResultDocument;
  zero.summary = { evaluated: 2, accepted: 0, rejected: 2, hasFeasibleCandidate: false, reviewRequired: true };
  zero.rankedCandidates = [];
  zero.rejections = [
    { floorHeightM: 32, code: "NO_FEASIBLE_MASSING" },
    { floorHeightM: 40, code: "RESOURCE_LIMIT" },
  ];
  const result = toSearchViewModel(zero);
  assert.deepEqual(result.candidates, []);
  assert.deepEqual(result.rejections.map((item) => item.floorHeightM), [32, 40]);

  const mixed = structuredClone(sample) as SearchResultDocument;
  mixed.rankedCandidates = mixed.rankedCandidates.slice(0, 1);
  mixed.rejections = [{ floorHeightM: 32, code: "NO_FEASIBLE_MASSING" }];
  assert.deepEqual(toSearchViewModel(mixed).rejections, mixed.rejections);
});

test("selection uses the exact rank and reference pair rather than array position", () => {
  const result = model();
  const first = initialCandidate(result)!;
  assert.equal(first.rank, 1);
  assert.equal(findCandidate(result, first)?.floorHeightM, 4);
  assert.equal(findCandidate(result, { rank: 2, candidateReference: first.candidateReference }), undefined);
  assert.equal(findCandidate({ ...result, candidates: result.candidates.toReversed() }, first)?.floorHeightM, 4);
  assert.ok(shortenReference(first.candidateReference).includes("…"));
});

test("footprint bounds invert Y for rendering without changing source coordinates", () => {
  const candidate = initialCandidate(model())!;
  const before = structuredClone(candidate.footprint);
  const preview = footprintPreview(candidate);
  assert.equal(preview.available, true);
  if (preview.available) {
    assert.match(preview.viewBox, /^-?\d/);
    assert.ok(preview.points.includes(",-") || preview.points.includes(",0"));
  }
  assert.deepEqual(candidate.footprint, before);
});

test("degenerate or unsafe preview bounds return a candidate-only fallback", () => {
  const candidate = initialCandidate(model())!;
  assert.deepEqual(footprintPreview({ ...candidate, footprint: [[[1, 1], [1, 1], [1, 1], [1, 1]]] }), { available: false });
  assert.deepEqual(footprintPreview({ ...candidate, footprint: [[[0, 0], [Infinity, 0], [1, 1], [0, 0]]] }), { available: false });
});

