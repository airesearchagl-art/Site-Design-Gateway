"use client";

import { useMemo, useRef, useState } from "react";
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
  const model = useMemo(
    () => result?.state === "DISPLAYABLE" ? toSearchViewModel(result.value) : null,
    [result],
  );
  const selected = model && selection ? findCandidate(model, selection) : undefined;
  const preview = selected ? footprintPreview(selected) : { available: false as const };
  const state = loading ? "LOADING" : result?.state ?? "EMPTY";

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
    setLoading(false);
    show(validateSearchJson(JSON.stringify(searchSample)));
  }

  async function selectFile(file?: File) {
    if (!file) return;
    const current = ++request.current;
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
    setLoading(false);
    setResult(null);
    setSelection(null);
    if (fileInput.current) fileInput.current.value = "";
  }

  return (
    <section className="panel search-panel" aria-labelledby="search-title" aria-busy={loading} data-viewer-state={state}>
      <div className="search-intro">
        <div>
          <span className="step">STEP 03</span>
          <h2 id="search-title">3. Review Search Result</h2>
          <p>ローカルBVE Coreが生成したSearch Result JSONを、ブラウザ内だけで比較表示します。</p>
        </div>
        <strong className={`viewer-state state-${state.toLowerCase()}`}>{state}</strong>
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
        <button type="button" onClick={clearResult} disabled={!loading && !result}>Clear result</button>
      </div>

      <div className="viewer-content" aria-live="polite" aria-atomic="false">
        {loading ? <p className="empty">Search Resultを読み込み中…</p> : null}
        {!loading && !result ? <p className="empty">sampleまたはローカルJSONを読み込むと、ここに結果を表示します。</p> : null}
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

            <div className="ranking-warning" role="note">
              <strong>順位の読み方</strong>
              <span>順位はGFA降順による比較であり、設計品質・推奨・最適性・法規適合を意味しません。</span>
            </div>

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
                          <td>{candidate.floorHeightM} m</td>
                          <td>{candidate.floorCount}</td>
                          <td>{candidate.heightM} m</td>
                          <td>{candidate.footprintAreaM2} m²</td>
                          <td>{candidate.grossFloorAreaM2} m²</td>
                          <td><code title={candidate.candidateReference}>{shortenReference(candidate.candidateReference)}</code></td>
                          <td><button type="button" className="select-candidate" aria-pressed={active} aria-label={`Rank ${candidate.rank} を選択`} onClick={() => setSelection(selectionOf(candidate))}>{active ? "選択中" : "表示"}</button></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {selected ? (
              <section className="candidate-detail" aria-labelledby="footprint-title">
                <div>
                  <span className="small">Selected candidate</span>
                  <h3 id="footprint-title">Conceptual footprint · Local XY</h3>
                  <p>Rank {selected.rank} · floor height {selected.floorHeightM} m · GFA {selected.grossFloorAreaM2} m²</p>
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
                  <tbody>{model.rejections.map((rejection) => <tr key={`${rejection.floorHeightM}-${rejection.code}`}><th scope="row">{rejection.floorHeightM} m</th><td><code>{rejection.code}</code></td></tr>)}</tbody>
                </table>
              </div>
            ) : null}

            <p className="numeric-note">表示数値はSearch Result由来です。JavaScript Numberによる表示はPython Decimalの正本ではなく、WebでBVE計算を再実行していません。</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}

