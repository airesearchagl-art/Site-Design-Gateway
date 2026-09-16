"use client";

import { useMemo, useRef, useState } from "react";
import { AreaBasisPanel, ConstraintUsagePanel } from "./search-interpretation";
import { PackageCheckSummary } from "./package-check-summary";
import { FarStackPanel } from "./far-stack-panel";
import { validateRunPackage, type PackageValidationResult } from "../lib/run-package-validation.ts";
import { formatMeasure, RANKING_RULES, ROUNDING_NOTICE } from "../lib/search-display.ts";
import searchSample from "../../../../cases/example-urban-office/search-result.json" with { type: "json" };
import {
  validateSearchFile,
  validateSearchJson,
  type SearchValidationResult,
} from "../lib/search-validation";
import {
  findCandidate,
  footprintPreview,
  initialCandidate,
  shortenReference,
  toSearchViewModel,
  type CandidateSelection,
} from "../lib/search-view";

const strategyLabels: Record<string, string> = {
  "floor_height_sweep_v0.1": "明示階高の逐次比較",
  "maximize_gross_floor_area_v0.1": "GFA降順",
};

function selectionOf(candidate: CandidateSelection | undefined): CandidateSelection | null {
  return candidate ? { rank: candidate.rank, candidateReference: candidate.candidateReference } : null;
}

export function SearchResultViewer() {
  const [result, setResult] = useState<SearchValidationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [selection, setSelection] = useState<CandidateSelection | null>(null);
  const request = useRef(0);
  const fileInput = useRef<HTMLInputElement>(null);
  const directoryInput = useRef<HTMLInputElement>(null);
  const packageInput = useRef<HTMLInputElement>(null);
  const packageRequest = useRef<AbortController | null>(null);
  const [packageResult, setPackageResult] = useState<PackageValidationResult | null>(null);
  const [packageLoading, setPackageLoading] = useState(false);
  const model = useMemo(
    () => result?.state === "DISPLAYABLE" ? toSearchViewModel(result.value) : null,
    [result],
  );
  const selected = model && selection ? findCandidate(model, selection) : undefined;
  const preview = selected ? footprintPreview(selected) : { available: false as const };
  const state = loading ? "LOADING" : result?.state ?? packageResult?.state ?? "EMPTY";

  function resetPackage() {
    packageRequest.current?.abort();
    packageRequest.current = null;
    setPackageResult(null);
    setPackageLoading(false);
    if (directoryInput.current) directoryInput.current.value = "";
    if (packageInput.current) packageInput.current.value = "";
  }

  function show(next: SearchValidationResult) {
    setResult(next);
    if (next.state === "DISPLAYABLE") {
      setSelection(selectionOf(initialCandidate(toSearchViewModel(next.value))));
    } else {
      setSelection(null);
    }
  }

  function loadSample() {
    request.current += 1;
    resetPackage();
    setLoading(false);
    show(validateSearchJson(JSON.stringify(searchSample)));
  }

  async function selectFile(file?: File) {
    if (!file) return;
    const current = ++request.current;
    resetPackage();
    setLoading(true);
    setResult(null);
    setSelection(null);
    const next = await validateSearchFile(file);
    if (request.current === current) {
      show(next);
      setLoading(false);
    }
  }

  function clearResult() {
    request.current += 1;
    resetPackage();
    setLoading(false);
    setResult(null);
    setSelection(null);
    if (fileInput.current) fileInput.current.value = "";
  }

  async function selectPackage(files: File[]) {
    if (!files.length) return;
    const current = ++request.current;
    resetPackage();
    if (fileInput.current) fileInput.current.value = "";
    const controller = new AbortController();
    packageRequest.current = controller;
    setLoading(true);
    setPackageLoading(true);
    setResult(null);
    setSelection(null);
    const next = await validateRunPackage(files, controller.signal);
    if (request.current === current && !controller.signal.aborted) {
      setPackageResult(next);
      if (next.state === "DISPLAYABLE") show(next.search);
      setLoading(false);
      setPackageLoading(false);
      packageRequest.current = null;
    }
  }

  return (
    <section className="panel search-panel" aria-labelledby="search-title" aria-busy={loading} data-viewer-state={state}>
      <div className="search-intro">
        <div>
          <span className="step">STEP 03</span>
          <h2 id="search-title">3. Review Search Result</h2>
          <p>ローカルBVE CoreのRun PackageまたはSearch Result JSONを、ブラウザ内だけで確認・比較表示します。</p>
        </div>
        <strong className={`viewer-state state-${state.toLowerCase()}`}>{state}</strong>
      </div>

      <div className="package-intake" data-package-state={packageLoading ? "LOADING" : packageResult?.state ?? "EMPTY"}>
        <h3>SDG Run Package</h3>
        <p className="small" id="package-help">folder直下のmanifest.json / project.json / site.geojson / constraints.json / search-result.jsonを選択します。
          folder選択に対応しないブラウザでは5ファイル同時選択を使えます。送信・保存なし。ZIPは対象外です。</p>
        <div className="package-controls">
          <button type="button" className="primary" onClick={() => directoryInput.current?.click()}>SDG Run Packageを選択</button>
          <input ref={directoryInput} id="run-package-folder" type="file" multiple {...{ webkitdirectory: "" }} hidden
            aria-label="SDG Run Package folder" aria-describedby="package-help"
            onChange={(event) => { const files = Array.from(event.target.files ?? []); event.target.value = ""; void selectPackage(files); }} />
          <button type="button" onClick={() => packageInput.current?.click()}>5ファイル同時選択</button>
          <input ref={packageInput} id="run-package-files" type="file" multiple hidden
            aria-label="Run Packageの5ファイル" aria-describedby="package-help"
            onChange={(event) => { const files = Array.from(event.target.files ?? []); event.target.value = ""; void selectPackage(files); }} />
        </div>
        {packageLoading ? <p role="status">Packageをブラウザ内で確認中…</p> : null}
        <PackageCheckSummary result={packageResult} />
      </div>

      <div className="search-controls">
        <button type="button" className="primary" onClick={loadSample}>Search Result sample</button>
        <div className="search-file">
          <label className="field-label" htmlFor="search-result-file">Search Result JSONファイルを選択</label>
          <input
            ref={fileInput}
            id="search-result-file"
            type="file"
            accept=".json,application/json"
            aria-describedby="search-file-help"
            onChange={(event) => { void selectFile(event.target.files?.[0]); event.target.value = ""; }}
          />
          <span id="search-file-help" className="small">.json / viewer上限 8 MiB / 送信・保存なし</span>
        </div>
        <button type="button" onClick={clearResult} disabled={!loading && !result && !packageResult}>Clear result</button>
      </div>

      <div className="viewer-content" aria-live="polite" aria-atomic="false">
        {loading ? <p className="empty">Search Resultを読み込み中…</p> : null}
        {!loading && !result && !packageResult ? <p className="empty">package、sampleまたはローカルJSONを読み込むと、ここに結果を表示します。</p> : null}
        {!loading && result?.state === "VIEWER_LIMIT" ? (
          <div className="viewer-message limit-message">
            <strong>VIEWER LIMIT</strong>
            <p>{result.issues[0]?.message}</p>
            <p className="small">これはブラウザviewerのresource上限であり、Search Result自体の不正を示しません。Schemaは未確認です。</p>
          </div>
        ) : null}
        {!loading && result?.state === "INVALID" ? (
          <div className="viewer-message invalid-message">
            <strong>INVALID · Schema {result.schema}</strong>
            <p>JSONの構文、UTF-8、拡張子またはSearch Result Schemaを確認してください。</p>
            <ul className="issues">
              {result.issues.map((issue, index) => (
                <li key={`${issue.path}-${issue.keyword}-${index}`}>
                  <code>{issue.path}</code><span>{issue.keyword} · {issue.message}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {!loading && result?.state === "DISPLAYABLE" && model ? (
          <div className="search-results">
            <div className="schema-line">
              <strong className="badge valid">Schema PASS</strong>
              <span className="small">構文・UTF-8・viewer resource・共有Schemaを確認</span>
            </div>
            <p className="semantic-note">Schema PASSは、BVE Coreのsemantic validationをブラウザで再実行したことを意味しません。Python export時の検証が正本です。</p>

            {model.summary.reviewRequired ? (
              <div className="review-banner" role="status"><strong>REVIEW REQUIRED</strong><span>入力条件と出典状態の確認が必要です。</span></div>
            ) : null}

            <div className="summary-grid" aria-label="Search Result summary">
              <div><span>Evaluated</span><strong>{model.summary.evaluated}</strong></div>
              <div><span>Accepted</span><strong>{model.summary.accepted}</strong></div>
              <div><span>Rejected</span><strong>{model.summary.rejected}</strong></div>
              <div><span>Candidate</span><strong>{model.summary.hasFeasibleCandidate ? "あり" : "なし"}</strong></div>
            </div>
            <dl className="strategy-list">
              <div><dt>Search strategy</dt><dd><code>{model.strategy}</code><span>{strategyLabels[model.strategy]}</span></dd></div>
              <div><dt>Ranking strategy</dt><dd><code>{model.ranking}</code><span>{strategyLabels[model.ranking]}</span></dd></div>
            </dl>

            <AreaBasisPanel model={model} />
            <FarStackPanel model={model} />

            <div className="ranking-warning" role="note">
              <strong>順位の読み方</strong>
              <span>順位はGFA降順による比較であり、設計品質・推奨・最適性・法規適合を意味しません。</span>
            </div>

            <ol className="ranking-rules">{RANKING_RULES.map((rule) => <li key={rule}>{rule}</li>)}</ol>
            <p className="small">Search Resultの正本の順位を表示しています。表示上の丸めや同値に見える数値で並べ替えません。</p>

            {model.candidates.length === 0 ? (
              <div className="zero-result"><strong>Search completed.</strong><p>この探索条件では表示可能なaccepted candidateはありません。</p></div>
            ) : (
              <div className="table-scroll candidate-table">
                <table>
                  <caption>Accepted candidates · Search Result内の順序</caption>
                  <thead><tr><th scope="col">Rank</th><th scope="col">Floor height</th><th scope="col">Floors</th><th scope="col">Building height</th><th scope="col">Footprint area</th><th scope="col">GFA</th><th scope="col">candidateReference</th><th scope="col"><span className="visually-hidden">選択</span></th></tr></thead>
                  <tbody>
                    {model.candidates.map((candidate) => {
                      const active = selected?.rank === candidate.rank && selected.candidateReference === candidate.candidateReference;
                      return (
                        <tr key={`${candidate.rank}-${candidate.candidateReference}`} className={active ? "selected-row" : undefined}>
                          <th scope="row">{candidate.rank}</th>
                          <td>{formatMeasure(candidate.floorHeightM)} m</td>
                          <td>{candidate.floorCount}</td>
                          <td>{formatMeasure(candidate.heightM)} m</td>
                          <td>{formatMeasure(candidate.footprintAreaM2)} m²</td>
                          <td>{formatMeasure(candidate.grossFloorAreaM2)} m²</td>
                          <td><code title={candidate.candidateReference}>{shortenReference(candidate.candidateReference)}</code></td>
                          <td><button type="button" className="select-candidate" aria-pressed={active} aria-label={`Rank ${candidate.rank} を選択`} onClick={() => setSelection(selectionOf(candidate))}>{active ? "選択中" : "表示"}</button></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            <ConstraintUsagePanel model={model} selected={selected} />

            {selected ? (
              <section className="candidate-detail" aria-labelledby="footprint-title">
                <div>
                  <span className="small">Selected candidate</span>
                  <h3 id="footprint-title">Conceptual footprint · Local XY</h3>
                  <p>Rank {selected.rank} · floor height {formatMeasure(selected.floorHeightM)} m · GFA {formatMeasure(selected.grossFloorAreaM2)} m²</p>
                  <p className="small">exterior ringのみを表示。形状の修復・補間・後退・3D化は行いません。</p>
                </div>
                <div className="footprint-frame">
                  {preview.available ? (
                    <svg viewBox={preview.viewBox} role="img" aria-label={`Rank ${selected.rank} conceptual footprint, Local XY`} preserveAspectRatio="xMidYMid meet">
                      <polygon points={preview.points} />
                    </svg>
                  ) : <p className="preview-unavailable">Footprint preview unavailable</p>}
                </div>
              </section>
            ) : null}

            {model.rejections.length > 0 ? (
              <div className="table-scroll rejection-table">
                <table>
                  <caption>Rejected search points · fixed code</caption>
                  <thead><tr><th scope="col">Floor height</th><th scope="col">Code</th></tr></thead>
                  <tbody>{model.rejections.map((rejection) => <tr key={`${rejection.floorHeightM}-${rejection.code}`}><th scope="row">{formatMeasure(rejection.floorHeightM)} m</th><td><code>{rejection.code}</code></td></tr>)}</tbody>
                </table>
              </div>
            ) : null}

            <p className="numeric-note">{ROUNDING_NOTICE}<br />JavaScript NumberはPython Decimalや元JSON数値字句の正本ではありません（D04 OPEN）。</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
