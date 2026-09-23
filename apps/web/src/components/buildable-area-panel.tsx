import type { SearchViewModel } from "../lib/search-view.ts";
import { formatMeasure } from "../lib/search-display.ts";
import { statusLabel, TERMS } from "../lib/human-labels.ts";
import { BUILDABLE_DOMAIN_NOTICE, BUILDABLE_DERIVATION_NOTICE, BUILDABLE_LEGAL_NOTICE } from "../lib/spatial-display.ts";

export function BuildableAreaPanel({ model }: { model: SearchViewModel }) {
  if (model.schemaVersion !== "0.5") return null;
  const domain = model.spatialContext.buildableArea;
  return <section className="buildable-area" aria-labelledby="buildable-area-title">
    <h3 id="buildable-area-title">{TERMS.buildableArea}</h3>
    <dl className="buildable-facts">
      <div><dt>範囲の面積</dt><dd>{formatMeasure(domain.areaM2)} m²</dd></div>
      <div><dt>確認状態</dt><dd>{statusLabel(domain.sourceStatus)}</dd></div>
      <div><dt>計算での扱い</dt><dd>外部で指定された配置検討範囲</dd></div>
      <div><dt>確認の必要性</dt><dd>{domain.reviewRequired ? "要確認" : "この範囲に要確認の指定なし"}</dd></div>
    </dl>
    <p>この範囲内で案を作成した計算結果を表示しています。建ぺい率・容積率の面積基準は敷地面積です。</p>
    <p className="small">この形状を後退・斜線などの法規から自動作成したものではなく、法規適合を証明するものでもありません。</p>
    <details className="technical-details"><summary>詳細データ：配置検討範囲</summary>
      <p><code>{domain.sourceStatus}</code> / <code>{domain.role}</code> / {domain.reviewRequired ? "REVIEW REQUIRED" : "No spatial review flag"}</p>
      <dl>{[["artifactReference",domain.artifactReference],["siteReference",domain.siteReference],["sourceReference",domain.sourceReference]].map(([label,value]) => <div key={label}><dt>{label}</dt><dd><code>{value}</code></dd></div>)}</dl>
      <p className="buildable-disclaimer small">{BUILDABLE_DOMAIN_NOTICE}<br />{BUILDABLE_DERIVATION_NOTICE}<br />{BUILDABLE_LEGAL_NOTICE}</p>
    </details>
  </section>;
}
