import type { AreaBasis, ContextCaps } from "./search-validation.ts";
import type { CandidateView } from "./search-view.ts";

export const DISPLAY_LOCALE = "en-US";
const measure = new Intl.NumberFormat(DISPLAY_LOCALE, { maximumFractionDigits: 3 });
const signed = new Intl.NumberFormat(DISPLAY_LOCALE, { maximumFractionDigits: 3, signDisplay: "exceptZero" });
const percentage = new Intl.NumberFormat(DISPLAY_LOCALE, { minimumFractionDigits: 1, maximumFractionDigits: 1 });

export function formatMeasure(value: number | null | undefined, showSign = false): string {
  if (value == null || !Number.isFinite(value)) return "Unavailable";
  return (showSign ? signed : measure).format(value);
}

export function formatPercent(value: number | null): string {
  return value === null || !Number.isFinite(value) ? "Unavailable" : `${percentage.format(value)}%`;
}

export function areaBasisDisplay(area: AreaBasis) {
  return {
    selected: area.selectedBasis === "declared_project_area" ? "Declared project area" : "Geometry area",
    basis: formatMeasure(area.basisAreaM2),
    declared: formatMeasure(area.declaredAreaM2),
    geometry: formatMeasure(area.geometryAreaM2),
    difference: formatMeasure(area.differenceM2, true),
  };
}

export function constraintUsage(actual: number | null, cap: number | null) {
  const available = actual !== null && cap !== null && Number.isFinite(actual) && Number.isFinite(cap);
  const remaining = available ? cap - actual : null;
  const usage = available && cap > 0 ? actual / cap * 100 : null;
  return {
    actual: formatMeasure(actual), cap: formatMeasure(cap), remaining: formatMeasure(remaining),
    percentage: usage !== null && Number.isFinite(usage) ? `${percentage.format(usage)}%` : "Unavailable",
  };
}

export function candidateUsage(candidate: CandidateView | undefined, caps: ContextCaps | undefined) {
  return [
    { label: "Footprint", unit: "m²", ...constraintUsage(candidate?.footprintAreaM2 ?? null, caps?.maxFootprintAreaM2 ?? null) },
    { label: "GFA", unit: "m²", ...constraintUsage(candidate?.grossFloorAreaM2 ?? null, caps?.maxTotalFloorAreaM2 ?? null) },
    { label: "Height", unit: "m", ...constraintUsage(candidate?.heightM ?? null, caps?.maxHeightM ?? null) },
  ];
}

export const USAGE_DISCLAIMER = "使用率は値の比較表示です。支配的な法規制約の特定や、法規適合の証明ではありません。";
export const ROUNDING_NOTICE = "表示値は丸められる場合があります（m・m²は小数3桁まで、割合は小数1桁、en-US表記）。Canonical JSONは変更しません。";
export const RANKING_RULES = [
  "GFAが大きい候補から順位が付いています。",
  "正本のGFAが等しい場合は、階高が低い候補が先になります。",
  "最後はcandidateReferenceの辞書順で順序を確定します。",
];
