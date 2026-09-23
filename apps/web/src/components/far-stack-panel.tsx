import { FAR_LEGAL_NOTICE, FAR_MINIMUM_NOTICE, farStackDisplay } from "../lib/far-display.ts";
import { capKindLabel, capStateLabel, displayValue, statusLabel } from "../lib/human-labels.ts";
import type { SearchViewModel } from "../lib/search-view.ts";

export function FarStackPanel({ model }: { model: SearchViewModel }) {
  if (model.schemaVersion !== "0.3" && model.schemaVersion !== "0.4" && model.schemaVersion !== "0.5") {
    return <section className="far-stack" aria-labelledby="far-stack-title"><h3 id="far-stack-title">容積率の計算条件</h3><p>この結果データには容積率の条件一覧が含まれていません。</p></section>;
  }
  const display = farStackDisplay(model.constraintContext.floorAreaRatio);
  return <section className="far-stack" aria-labelledby="far-stack-title">
    <h3 id="far-stack-title">容積率の計算条件</h3>
    <dl className="far-effective">
      <div><dt>計算に用いた容積率の上限</dt><dd>{displayValue(display.effective)}</dd></div>
      <div><dt>延床面積の上限</dt><dd>{displayValue(display.maxGfa)}{display.maxGfa !== "Unavailable" ? " m²" : ""}</dd></div>
    </dl>
    <p className="far-state">{capStateLabel(display.state)}{display.reviewRequired ? " · 要確認" : ""}</p>
    <div className="table-scroll far-table"><table><caption>入力された容積率の条件（入力順）</caption>
      <thead><tr><th scope="col">条件</th><th scope="col">上限</th><th scope="col">確認状態</th></tr></thead>
      <tbody>{display.entries.map((entry,index) => <tr key={`${entry.id}-${index}`}><th scope="row">{index === 0 ? "基準の容積率" : capKindLabel(entry.kind)}</th><td>{displayValue(entry.value)}</td><td>{statusLabel(entry.status)}{entry.reviewRequired ? " · 要確認" : ""}</td></tr>)}</tbody>
    </table></div>
    <p className="small">入力された数値上限を用いた計算結果です。道路幅員からの計算や、どの法規が支配するかの判定は行いません。</p>
    <details className="technical-details"><summary>詳細データ：容積率</summary>
      <p>Effective cap source ID(s): {display.effectiveIds.length ? display.effectiveIds.join(" / ") : "Unavailable"}</p>
      <p>{display.state}{display.reviewRequired ? " · REVIEW REQUIRED" : ""}</p>
      <ul>{display.entries.map((entry,index) => <li key={`${entry.id}-${index}`}>{index === 0 ? "Base FAR · " : ""}<code>{entry.id}</code> · {entry.value} · <code>{entry.kind}</code> · <code>{entry.status}</code> · reviewRequired={String(entry.reviewRequired)}</li>)}</ul>
      <ul>{model.constraintContext.floorAreaRatio.capStack.map((entry,index) => <li key={`${entry.id}-${index}`}><code>{entry.input}</code> · <code>{entry.reference}</code></li>)}</ul>
      <p className="far-disclaimer small">{FAR_MINIMUM_NOTICE}<br />{FAR_LEGAL_NOTICE}<br />Pythonの出力値を表示しています。</p>
    </details>
  </section>;
}
