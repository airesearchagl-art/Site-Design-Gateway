import type { ConstraintCaps, ConstraintContext, FarConstraintContext, RankedCandidateDocument, SearchResultDocument } from "./search-validation.ts";

export type CandidateSelection = { rank: number; candidateReference: string };

export type CandidateView = CandidateSelection & {
  floorHeightM: number;
  floorCount: number;
  heightM: number;
  footprintAreaM2: number;
  grossFloorAreaM2: number;
  footprint: number[][][];
  constraintCaps: ConstraintCaps;
};

export type SearchViewModel = ({ schemaVersion: "0.1"; constraintContext?: never }
  | { schemaVersion: "0.2"; constraintContext: ConstraintContext }
  | { schemaVersion: "0.3"; constraintContext: FarConstraintContext }) & {
  summary: SearchResultDocument["summary"];
  strategy: string;
  ranking: string;
  candidates: CandidateView[];
  rejections: SearchResultDocument["rejections"];
};

export type FootprintPreview =
  | { available: true; viewBox: string; points: string }
  | { available: false };

function candidateView(entry: RankedCandidateDocument): CandidateView {
  return {
    rank: entry.rank,
    candidateReference: entry.candidateReference,
    floorHeightM: entry.candidate.generator.floorHeightM,
    floorCount: entry.candidate.candidate.floorCount,
    heightM: entry.candidate.candidate.heightM,
    footprintAreaM2: entry.candidate.candidate.footprintAreaM2,
    grossFloorAreaM2: entry.grossFloorAreaM2,
    footprint: entry.candidate.candidate.footprint.coordinates,
    constraintCaps: entry.candidate.constraintCaps,
  };
}

export function toSearchViewModel(document: SearchResultDocument): SearchViewModel {
  const version = document.schemaVersion === "0.1" ? { schemaVersion: document.schemaVersion }
    : document.schemaVersion === "0.2" ? { schemaVersion: document.schemaVersion, constraintContext: document.constraintContext }
    : { schemaVersion: document.schemaVersion, constraintContext: document.constraintContext };
  return {
    ...version,
    summary: document.summary,
    strategy: document.search.strategy,
    ranking: document.search.ranking,
    candidates: document.rankedCandidates.map(candidateView),
    rejections: document.rejections.map((rejection) => ({ ...rejection })),
  };
}

export function initialCandidate(model: SearchViewModel): CandidateView | undefined {
  return model.candidates.find((candidate) => candidate.rank === 1);
}

export function findCandidate(model: SearchViewModel, selection: CandidateSelection): CandidateView | undefined {
  return model.candidates.find((candidate) =>
    candidate.rank === selection.rank && candidate.candidateReference === selection.candidateReference,
  );
}

export function shortenReference(reference: string): string {
  if (reference.length <= 24) return reference;
  return `${reference.slice(0, 15)}…${reference.slice(-8)}`;
}

export function footprintPreview(candidate: CandidateView): FootprintPreview {
  const ring = candidate.footprint[0];
  if (!ring || ring.length < 4) return { available: false };
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const point of ring) {
    if (point.length !== 2 || !Number.isFinite(point[0]) || !Number.isFinite(point[1])) {
      return { available: false };
    }
    minX = Math.min(minX, point[0]);
    minY = Math.min(minY, point[1]);
    maxX = Math.max(maxX, point[0]);
    maxY = Math.max(maxY, point[1]);
  }
  const width = maxX - minX;
  const height = maxY - minY;
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return { available: false };
  }
  const padding = Math.max(width, height) * 0.08;
  const viewWidth = width + padding * 2;
  const viewHeight = height + padding * 2;
  const viewX = minX - padding;
  const viewY = -maxY - padding;
  if (![padding, viewWidth, viewHeight, viewX, viewY].every(Number.isFinite)) return { available: false };
  return {
    available: true,
    viewBox: `${viewX} ${viewY} ${viewWidth} ${viewHeight}`,
    points: ring.map(([x, y]) => `${x},${-y}`).join(" "),
  };
}
