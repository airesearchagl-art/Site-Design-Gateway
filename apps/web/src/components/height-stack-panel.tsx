import { HEIGHT_LEGAL_NOTICE, HEIGHT_MINIMUM_NOTICE, heightStackDisplay } from "../lib/height-display.ts";
import { capKindLabel, capStateLabel, displayValue, statusLabel } from "../lib/human-labels.ts";
import type { SearchViewModel } from "../lib/search-view.ts";

export function HeightStackPanel({ model }: { model: SearchViewModel }) {
  if (model.schemaVersion !== "0.4" && model.schemaVersion !== "0.5") {
    return <section className="height-stack" aria-labelledby="height-stack-title"><h3 id="height-stack-title">高さ制限の計算条件</h3><p>この結果データには高さ制限の条件一覧が含まれていません。</p></section>;
  }
  const display = heightStackDisplay(model.constraintContext.height);
  return <section className="height-stack" aria-labelledby="height-stack-title">
    <h3 id="height-stack-title">高さ制限の計算条件</h3>
    <dl className="height-effective"><div><dt>計算に用いた高さの上限</dt><dd>{displayValue(display.effective)}</dd></div></dl>
    <p className="height-state">{capStateLabel(display.state)}{display.reviewRequired ? " · 要確認" : ""}</p>
    <div className="table-scroll height-table"><table><caption>入力された高さ制限（入力順）</caption>
      <thead><tr><th scope="col">条件</th><th scope="col">上限</th><th scope="col">確認状態</th></tr></thead>
      <tbody>{display.entries.map((entry,index) => <tr key={`${entry.id}-${index}`}><th scope="row">{entry.id === "base-height" ? "基準の高さ制限" : capKindLabel(entry.kind)}</th><td>{displayValue(entry.value)}</td><td>{statusLabel(entry.status)}{entry.reviewRequired ? " · 要確認" : ""}</td></tr>)}</tbody>
    </table></div>
    <p className="small">明示された高さ上限を用いた計算結果です。斜線などの空間的制限や、どの法規が支配するかの判定は行いません。</p>
    <details className="technical-details"><summary>詳細データ：高さ制限</summary>
      <p>Effective cap source ID(s): {display.effectiveIds.length ? display.effectiveIds.join(" / ") : "Unavailable"}</p>
      <p>{display.state}{display.reviewRequired ? " · REVIEW REQUIRED" : ""}</p>
      <ul>{display.entries.map((entry,index) => <li key={`${entry.id}-${index}`}>{entry.id === "base-height" ? "Base height cap · " : ""}<code>{entry.id}</code> · {entry.value} · <code>{entry.kind}</code> · <code>{entry.status}</code> · reviewRequired={String(entry.reviewRequired)}</li>)}</ul>
      <ul>{model.constraintContext.height.capStack.map((entry,index) => <li key={`${entry.id}-${index}`}><code>{entry.input}</code> · <code>{entry.reference}</code></li>)}</ul>
      <p className="height-disclaimer small">{HEIGHT_MINIMUM_NOTICE}<br />{HEIGHT_LEGAL_NOTICE}<br />Pythonの出力値を表示しています。</p>
    </details>
  </section>;
}
