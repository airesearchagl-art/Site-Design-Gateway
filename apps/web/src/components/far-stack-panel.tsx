import { FAR_LEGAL_NOTICE, FAR_MINIMUM_NOTICE, farStackDisplay } from "../lib/far-display.ts";
import type { SearchViewModel } from "../lib/search-view.ts";

export function FarStackPanel({ model }: { model: SearchViewModel }) {
  if (model.schemaVersion !== "0.3" && model.schemaVersion !== "0.4" && model.schemaVersion !== "0.5") {
    return <section className="far-stack" aria-labelledby="far-stack-title">
      <h3 id="far-stack-title">FAR cap stack</h3><p>Unavailable in this Search Result version</p>
    </section>;
  }
  const display = farStackDisplay(model.constraintContext.floorAreaRatio);
  return (
    <section className="far-stack" aria-labelledby="far-stack-title">
      <h3 id="far-stack-title">FAR cap stack</h3>
      <p className="small">入力された数値上限の比較です。道路幅員からの計算や法的な支配規定の判定は行いません。</p>
      <dl className="far-effective">
        <div><dt>Effective FAR cap</dt><dd>{display.effective}</dd></div>
        <div><dt>Effective cap source ID(s)</dt><dd>{display.effectiveIds.length ? display.effectiveIds.join(" / ") : "Unavailable"}</dd></div>
        <div><dt>Effective max GFA cap</dt><dd>{display.maxGfa}{display.maxGfa !== "Unavailable" ? " m²" : ""}</dd></div>
      </dl>
      <p className="far-state">{display.state}{display.reviewRequired ? " · REVIEW REQUIRED" : ""}</p>
      <div className="table-scroll far-table"><table>
        <caption>Base FAR / Additional FAR caps · 入力順</caption>
        <thead><tr><th scope="col">Source ID</th><th scope="col">Cap</th><th scope="col">Kind</th><th scope="col">Status</th><th scope="col">Review</th></tr></thead>
        <tbody>{display.entries.map((entry, index) => <tr key={`${entry.id}-${index}`}>
          <th scope="row">{index === 0 ? "Base FAR · " : ""}{entry.id}</th><td>{entry.value}</td>
          <td>{entry.kind}</td><td>{entry.status}</td><td>{entry.reviewRequired ? "REVIEW REQUIRED" : "—"}</td>
        </tr>)}</tbody>
      </table></div>
      <p className="far-disclaimer small">{FAR_MINIMUM_NOTICE}<br />{FAR_LEGAL_NOTICE}<br />Pythonの出力値を表示しています。</p>
    </section>
  );
}
