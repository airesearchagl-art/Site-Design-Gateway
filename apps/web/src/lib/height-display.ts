import { formatMeasure } from "./search-display.ts";
import type { HeightContext } from "./search-validation.ts";

export const HEIGHT_MINIMUM_NOTICE = "Effective height cap is the minimum of the explicit scalar height caps supplied to BVE.";
export const HEIGHT_LEGAL_NOTICE = "It does not evaluate spatial slope planes, identify the governing legal rule, or prove regulatory compliance.";

function meters(value: number | null): string {
  return value === null ? "Unavailable" : `${formatMeasure(value)} m`;
}

/** Read authoritative fields in supplied order; no scalar calculation or tie inference. */
export function heightStackDisplay(height: HeightContext) {
  return {
    state: height.state,
    effective: meters(height.effectiveHeightM),
    effectiveIds: [...height.effectiveCapIds],
    reviewRequired: height.reviewRequired,
    entries: height.capStack.map((entry) => ({
      id: entry.id, kind: entry.kind, value: meters(entry.condition.value),
      status: entry.condition.status, reviewRequired: entry.reviewRequired,
    })),
  };
}
