import { HEIGHT_LEGAL_NOTICE, HEIGHT_MINIMUM_NOTICE, heightStackDisplay } from "../lib/height-display.ts";
import type { SearchViewModel } from "../lib/search-view.ts";

export function HeightStackPanel({ model }: { model: SearchViewModel }) {
  if (model.schemaVersion !== "0.4") {
    return <section className="height-stack" aria-labelledby="height-stack-title">
      <h3 id="height-stack-title">Height cap stack</h3><p>Unavailable in this Search Result version</p>
    </section>;
  }
  const display = heightStackDisplay(model.constraintContext.height);
  return <section className="height-stack" aria-labelledby="height-stack-title">
    <h3 id="height-stack-title">Height cap stack</h3>
    <p className="small">明示された高さ上限の比較です。斜線などの空間的制限や法的な支配規定の判定は行いません。</p>
    <dl className="height-effective">
      <div><dt>Effective height cap</dt><dd>{display.effective}</dd></div>
      <div><dt>Effective cap source ID(s)</dt><dd>{display.effectiveIds.length ? display.effectiveIds.join(" / ") : "Unavailable"}</dd></div>
    </dl>
    <p className="height-state">{display.state}{display.reviewRequired ? " · REVIEW REQUIRED" : ""}</p>
    <div className="table-scroll height-table"><table>
      <caption>Base height cap / Additional scalar height caps · 入力順</caption>
      <thead><tr><th scope="col">Source ID</th><th scope="col">Cap</th><th scope="col">Kind</th><th scope="col">Status</th><th scope="col">Review</th></tr></thead>
      <tbody>{display.entries.map((entry, index) => <tr key={`${entry.id}-${index}`}>
        <th scope="row">{entry.id === "base-height" ? "Base height cap · " : ""}{entry.id}</th><td>{entry.value}</td>
        <td>{entry.kind}</td><td>{entry.status}</td><td>{entry.reviewRequired ? "REVIEW REQUIRED" : "—"}</td>
      </tr>)}</tbody>
    </table></div>
    <p className="height-disclaimer small">{HEIGHT_MINIMUM_NOTICE}<br />{HEIGHT_LEGAL_NOTICE}<br />Pythonの出力値を表示しています。</p>
  </section>;
}
