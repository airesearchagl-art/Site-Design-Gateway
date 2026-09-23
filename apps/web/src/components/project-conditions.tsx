import type { ValidationResult } from "../lib/validation.ts";
import { conditionLabel, statusLabel, unitLabel } from "../lib/human-labels.ts";
import { formatMeasure } from "../lib/search-display.ts";

export function ProjectConditions({ result }: { result: ValidationResult }) {
  return <div className="project-conditions" data-project-state={result.outcome}>
    <p className="verdict"><strong className={`badge ${result.outcome.toLowerCase()}`}>
      {result.outcome === "INVALID" ? "入力形式を確認してください" : result.outcome === "REVIEW_REQUIRED" ? "要確認の条件があります" : "入力形式を確認しました"}
    </strong></p>
    <p className="small">確認状態は入力された申告です。値と根拠の妥当性は人が確認してください。</p>
    {result.outcome === "INVALID" ? <p>準備したデータの形式を確認してください。問題の位置は「詳細データ」で確認できます。</p> : null}
    {result.sources.length > 0 ? <div className="table-scroll project-table"><table>
      <caption>敷地・計画条件と確認状態</caption>
      <thead><tr><th scope="col">項目</th><th scope="col">値</th><th scope="col">確認状態</th></tr></thead>
      <tbody>{result.sources.map(source => <tr key={source.path}>
        <th scope="row">{conditionLabel(source.path)}</th>
        <td>{source.value === null ? "未確認" : `${formatMeasure(source.value)} ${unitLabel(source.unit)}`}</td>
        <td><span className={`source-tag ${source.status}`}>{statusLabel(source.status)}</span></td>
      </tr>)}</tbody>
    </table></div> : null}
    <details className="technical-details"><summary>詳細データ：入力条件</summary>
      <p>Schema {result.schema} / {result.outcome}</p>
      {result.issues.length ? <ul className="issues">{result.issues.map((issue,index) => <li key={index}><code>{issue.path}</code><span>{issue.message}</span></li>)}</ul> : null}
      <ul>{result.sources.map(source => <li key={source.path}><code>{source.path}</code> · <code>{source.status}</code></li>)}</ul>
    </details>
  </div>;
}
