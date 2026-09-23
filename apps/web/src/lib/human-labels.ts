/** Presentation only. Never infer verification, legal meaning, rank, or a cap. */
export const TERMS = {
  siteArea: "敷地面積", buildingCoverageRatio: "建ぺい率", floorAreaRatio: "容積率",
  heightLimit: "高さ制限", floorHeight: "想定階高", floorCount: "階数", height: "建物高さ",
  footprint: "建築面積", grossFloorArea: "延床面積", areaBasis: "面積算定の基準",
  usage: "条件に対する利用状況", buildableArea: "指定された配置検討範囲",
} as const;
const statuses: Record<string, string> = {
  official_verified: "公式資料で確認済み", user_provided: "ユーザー入力", drawing_derived: "図面から取得",
  llm_researched: "AI調査・公式未確認", assumed: "仮定・要確認", unknown: "未確認", review_required: "要確認",
};
export function statusLabel(status: string): string { return statuses[status] ?? "確認状態の情報なし"; }
export function conditionLabel(path: string): string {
  const labels: Record<string, string> = {
    "site.area": TERMS.siteArea, "geometry.areaM2": "敷地形状から求めた面積",
    "/site/area": TERMS.siteArea, "/zoning/buildingCoverageRatio": TERMS.buildingCoverageRatio,
    "/zoning/floorAreaRatio": TERMS.floorAreaRatio, "/zoning/heightLimit": TERMS.heightLimit,
  };
  if (labels[path]) return labels[path];
  const additional = /^\/zoning\/(additionalFloorAreaRatioCaps|additionalHeightCaps)\/(\d+)$/.exec(path);
  if (additional) return `${additional[1] === "additionalHeightCaps" ? "追加の高さ制限" : "追加の容積率条件"} ${Number(additional[2]) + 1}`;
  return "その他の入力条件";
}
export function unitLabel(unit: string): string { return ({ m2: "m²", m: "m", percent: "%" } as Record<string, string>)[unit] ?? ""; }
export function displayValue(text: string): string { return text === "Unavailable" ? "情報なし" : text; }
export function capStateLabel(state: string): string { return ({ COMPUTED: "計算済み", UNAVAILABLE: "未確認の条件があり算定できません", ABSENT: "高さ制限の入力なし" } as Record<string, string>)[state] ?? "情報なし"; }
export function capKindLabel(kind: string): string {
  return ({ base_zoning: "基準の容積率", road_width_derived: "道路幅員に由来する外部入力", other_explicit: "その他の明示条件", base_height: "基準の高さ制限", absolute_height_explicit: "明示された高さ制限", district_plan_explicit: "地区計画による外部入力", external_rule_result: "外部の規則による計算結果" } as Record<string, string>)[kind] ?? "明示された追加条件";
}
/** A display name for an authoritative rank, including ranks beyond Z. No sorting. */
export function candidateName(rank: number): string {
  let letters = "";
  for (let n = rank; n > 0; n = Math.floor((n - 1) / 26)) letters = String.fromCharCode(65 + (n - 1) % 26) + letters;
  return `案 ${letters}`;
}
export const SAFETY_NOTICE = "この結果は入力された条件による初期ボリューム検討です。法規適合や建築可能最大値を証明するものではありません。";
