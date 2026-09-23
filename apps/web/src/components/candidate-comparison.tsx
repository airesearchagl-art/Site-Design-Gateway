import { candidateName, TERMS } from "../lib/human-labels.ts";
import { formatMeasure } from "../lib/search-display.ts";
import type { CandidateView, SearchViewModel } from "../lib/search-view.ts";

const floorHeight = new Intl.NumberFormat("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 3 });

export function ComparisonExplanation({ model }: { model: SearchViewModel }) {
  return <section className="comparison-explanation" aria-labelledby="comparison-title">
    <h3 id="comparison-title">今回、何を比較しているか</h3>
    <dl className="comparison-facts">
      <div><dt>比較条件</dt><dd>{model.strategy === "floor_height_sweep_v0.1" ? TERMS.floorHeight : "詳細データを確認してください"}</dd></div>
      <div><dt>比較値</dt><dd>{model.floorHeightsM.map(value => floorHeight.format(value)).join(" / ")} m</dd></div>
      <div><dt>並び順</dt><dd>{model.ranking === "maximize_gross_floor_area_v0.1" ? "延床面積が大きい順" : "計算結果の順序"}</dd></div>
    </dl>
    <p className="small">同じ延床面積の場合は想定階高が低い順です。計算済みの順序を表示し、画面上で並べ替えません。</p>
    <p className="small">順位は設計品質・推奨・最適性・法規適合を意味しません。</p>
  </section>;
}

export function CandidateKpis({ selected }: { selected: CandidateView }) {
  return <section className="candidate-kpis" aria-labelledby="selected-title">
    <div className="selected-heading"><h3 id="selected-title">選択中：{candidateName(selected.rank)}</h3><span>想定階高 {formatMeasure(selected.floorHeightM)} m · 順位 {selected.rank}</span></div>
    <dl className="kpi-grid">
      <div className="kpi-main"><dt>{TERMS.grossFloorArea}</dt><dd>{formatMeasure(selected.grossFloorAreaM2)}<span> m²</span></dd></div>
      <div><dt>{TERMS.footprint}</dt><dd>{formatMeasure(selected.footprintAreaM2)}<span> m²</span></dd></div>
      <div><dt>{TERMS.floorCount}</dt><dd>{selected.floorCount}<span> 階</span></dd></div>
      <div><dt>{TERMS.height}</dt><dd>{formatMeasure(selected.heightM)}<span> m</span></dd></div>
      <div><dt>{TERMS.floorHeight}</dt><dd>{formatMeasure(selected.floorHeightM)}<span> m</span></dd></div>
    </dl>
  </section>;
}
