import { formatMeasure, formatPercent } from "./search-display.ts";
import type { FloorAreaRatioContext } from "./search-validation.ts";

export const FAR_MINIMUM_NOTICE = "Effective FAR cap is the minimum of the explicit numeric caps supplied to BVE.";
export const FAR_LEGAL_NOTICE = "It does not identify the governing legal rule or prove regulatory compliance.";

/** Display supplied authoritative values in their original order. No cap calculation. */
export function farStackDisplay(far: FloorAreaRatioContext) {
  return {
    state: far.state,
    effective: formatPercent(far.effectiveCapPercent),
    effectiveIds: [...far.effectiveCapIds],
    maxGfa: formatMeasure(far.maxTotalFloorAreaM2),
    reviewRequired: far.reviewRequired,
    entries: far.capStack.map((entry) => ({
      id: entry.id, kind: entry.kind, value: formatPercent(entry.condition.value),
      status: entry.condition.status, reviewRequired: entry.reviewRequired,
    })),
  };
}
