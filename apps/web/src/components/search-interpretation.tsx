import { areaBasisDisplay, candidateUsage, USAGE_DISCLAIMER } from "../lib/search-display.ts";
import { candidateName, conditionLabel, displayValue, statusLabel, TERMS } from "../lib/human-labels.ts";
import type { CandidateView, SearchViewModel } from "../lib/search-view.ts";

export function AreaBasisPanel({ model }: { model: SearchViewModel }) {
  const area = model.constraintContext ? areaBasisDisplay(model.constraintContext.areaBasis) : null;
  const provenance = model.constraintContext?.areaBasis.provenance ?? [];
  return <section className="area-basis" aria-labelledby="area-basis-title">
    <h3 id="area-basis-title">{TERMS.areaBasis}</h3>
    {area ? <>
      <p className="basis-selected">使用した基準：<strong>{area.selected === "Declared project area" ? "入力された敷地面積" : "敷地形状から求めた面積"}</strong></p>
      <dl className="basis-values">{[["算定に用いた面積",area.basis],["入力された敷地面積",area.declared],["敷地形状の面積",area.geometry],["面積の差",area.difference]].map(([label,value]) =>
        <div key={label}><dt>{label}</dt><dd>{displayValue(value)}{value !== "Unavailable" ? " m²" : ""}</dd></div>)}</dl>
      <ul className="provenance-list">{provenance.map((source,index) => <li key={index}>{conditionLabel(source.input)}：{statusLabel(source.condition.status)}</li>)}</ul>
      <details className="technical-details"><summary>詳細データ：面積の出典</summary>
        <p>{area.selected} / {model.constraintContext?.areaBasis.selectedBasis}</p>
        {provenance.map((source,index) => <p key={index}><code>{source.input}</code> · <code>{source.condition.status}</code><br /><code>{source.reference}</code></p>)}
      </details>
    </> : <p>この結果データには、面積算定の基準が含まれていません。基準は推測しません。</p>}
  </section>;
}

export function ConstraintUsagePanel({ model, selected }: { model: SearchViewModel; selected?: CandidateView }) {
  const rows = candidateUsage(selected, selected?.constraintCaps ?? model.constraintContext?.constraintCaps);
  const labels: Record<string,string> = { Footprint: TERMS.footprint, GFA: TERMS.grossFloorArea, Height: TERMS.height };
  return <section className="constraint-usage" aria-labelledby="constraint-usage-title">
    <h3 id="constraint-usage-title">{TERMS.usage}</h3>
    <p className="small">{selected ? "選択中：" + candidateName(selected.rank) : "表示できる案がないため、利用状況は情報なしです"}</p>
    <div className="usage-grid">{rows.map(row => <section className="usage-metric" key={row.label} aria-label={labels[row.label]}>
      <h4>{labels[row.label]} <span className="small">{row.unit}</span></h4>
      <dl><div><dt>選択案</dt><dd>{displayValue(row.actual)}</dd></div><div><dt>条件の上限</dt><dd>{displayValue(row.cap)}</dd></div>
        <div><dt>上限との差</dt><dd>{displayValue(row.remaining)}</dd></div><div><dt>利用率</dt><dd>{displayValue(row.percentage)}</dd></div></dl>
    </section>)}</div>
    <p className="usage-disclaimer small">{USAGE_DISCLAIMER}</p>
  </section>;
}
