"use client";

import { useImperativeHandle, useMemo, useRef, useState, type Ref } from "react";
import { AreaBasisPanel, ConstraintUsagePanel } from "./search-interpretation";
import { PackageCheckSummary } from "./package-check-summary";
import { BuildableAreaPanel } from "./buildable-area-panel.tsx";
import { HeightStackPanel } from "./height-stack-panel.tsx";
import { FarStackPanel } from "./far-stack-panel";
import { ProjectConditions } from "./project-conditions";
import { ComparisonExplanation, CandidateKpis } from "./candidate-comparison";
import { candidateName, SAFETY_NOTICE } from "../lib/human-labels";
import { validateJson } from "../lib/validation";
import { validateRunPackage, type PackageValidationResult } from "../lib/run-package-validation.ts";
import { formatMeasure, RANKING_RULES, ROUNDING_NOTICE } from "../lib/search-display.ts";
import searchSample from "../../../../cases/example-urban-office/search-result.json" with { type: "json" };
import projectSample from "../../../../cases/example-urban-office/project.json" with { type: "json" };
import { validateSearchFile, validateSearchJson, type SearchValidationResult } from "../lib/search-validation";
import { findCandidate, footprintPreview, initialCandidate, toSearchViewModel, type CandidateSelection } from "../lib/search-view";

const sampleConditions = validateJson(JSON.stringify(projectSample));
const stateLabels: Record<string, string> = { EMPTY: "結果を選択してください", LOADING: "確認中", DISPLAYABLE: "比較できます", INVALID: "データを確認してください", VIEWER_LIMIT: "表示上限を超えています" };
export type SearchViewerHandle = { loadSample: () => void; openIntake: () => void };
function selectionOf(candidate: CandidateSelection | undefined): CandidateSelection | null {
  return candidate ? { rank: candidate.rank, candidateReference: candidate.candidateReference } : null;
}

export function SearchResultViewer({ ref, onSample, onClear }: { ref?: Ref<SearchViewerHandle>; onSample: () => void; onClear: () => void }) {
  const [result, setResult] = useState<SearchValidationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [isSample, setIsSample] = useState(false);
  const [selection, setSelection] = useState<CandidateSelection | null>(null);
  const request = useRef(0);
  const fileInput = useRef<HTMLInputElement>(null);
  const directoryInput = useRef<HTMLInputElement>(null);
  const packageInput = useRef<HTMLInputElement>(null);
  const intake = useRef<HTMLDetailsElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const packageRequest = useRef<AbortController | null>(null);
  const [packageResult, setPackageResult] = useState<PackageValidationResult | null>(null);
  const [packageLoading, setPackageLoading] = useState(false);
  const model = useMemo(() => result?.state === "DISPLAYABLE" ? toSearchViewModel(result.value) : null, [result]);
  const selected = model && selection ? findCandidate(model, selection) : undefined;
  const preview = selected ? footprintPreview(selected, model?.schemaVersion === "0.5" ? model.spatialContext.buildableArea.geometry.coordinates : undefined) : { available: false as const };
  const state = loading ? "LOADING" : result?.state ?? packageResult?.state ?? "EMPTY";

  function focusResults() { heading.current?.scrollIntoView({ block: "start" }); heading.current?.focus({ preventScroll: true }); }
  function openIntake() { if (intake.current) { intake.current.open = true; intake.current.scrollIntoView({ block: "start" }); intake.current.querySelector("summary")?.focus(); } }

  function resetPackage() {
    packageRequest.current?.abort(); packageRequest.current = null;
    setPackageResult(null); setPackageLoading(false);
    if (directoryInput.current) directoryInput.current.value = "";
    if (packageInput.current) packageInput.current.value = "";
  }
  function show(next: SearchValidationResult) {
    setResult(next);
    if (next.state === "DISPLAYABLE") setSelection(selectionOf(initialCandidate(toSearchViewModel(next.value))));
    else setSelection(null);
  }
  function loadSample() {
    request.current += 1; resetPackage(); setLoading(false); setIsSample(true);
    if (fileInput.current) fileInput.current.value = "";
    if (intake.current) intake.current.open = false;
    show(validateSearchJson(JSON.stringify(searchSample))); focusResults();
  }
  async function selectFile(file?: File) {
    if (!file) return;
    const current = ++request.current; resetPackage(); setIsSample(false); setLoading(true); setResult(null); setSelection(null);
    const next = await validateSearchFile(file);
    if (request.current === current) { show(next); setLoading(false); }
  }
  function clearResult() {
    request.current += 1; resetPackage(); setLoading(false); setResult(null); setSelection(null); setIsSample(false);
    if (fileInput.current) fileInput.current.value = "";
    onClear();
  }
  async function selectPackage(files: File[]) {
    if (!files.length) return;
    const current = ++request.current; resetPackage(); setIsSample(false);
    if (fileInput.current) fileInput.current.value = "";
    const controller = new AbortController(); packageRequest.current = controller;
    setLoading(true); setPackageLoading(true); setResult(null); setSelection(null);
    const next = await validateRunPackage(files, controller.signal);
    if (request.current === current && !controller.signal.aborted) {
      setPackageResult(next);
      if (next.state === "DISPLAYABLE") show(next.search);
      setLoading(false); setPackageLoading(false); packageRequest.current = null;
    }
  }

  useImperativeHandle(ref, () => ({ loadSample, openIntake }));

  return <section className="panel search-panel" aria-labelledby="search-title" aria-busy={loading} data-viewer-state={state}>
    <div className="search-intro">
      <div><p className="eyebrow">計算済みの案を読み解く</p><h2 ref={heading} tabIndex={-1} id="search-title">ボリューム案を比較</h2><p>想定階高を変えたケースを、延床面積の大きい順で確認します。</p></div>
      <strong className={"viewer-state state-" + state.toLowerCase()}>{stateLabels[state]}</strong>
    </div>
    <details ref={intake} className="package-intake" id="results-intake">
      <summary>計算済みの検討結果を開く</summary>
      <div className="intake-content" data-package-state={packageLoading ? "LOADING" : packageResult?.state ?? "EMPTY"}>
        <p id="package-help">ローカルSDG / BVE Coreで作成した検討結果フォルダを選択します。ブラウザ内で確認し、送信・保存しません。</p>
        <div className="package-controls">
          <button type="button" className="primary" onClick={() => directoryInput.current?.click()}>検討結果フォルダを選択</button>
          <input ref={directoryInput} id="run-package-folder" type="file" multiple {...{ webkitdirectory: "" }} hidden aria-label="検討結果フォルダ" aria-describedby="package-help"
            onChange={event => { const files = Array.from(event.target.files ?? []); event.target.value = ""; void selectPackage(files); }} />
        </div>
        <details className="technical-details fallback-intake"><summary>うまくフォルダを選べない場合</summary>
          <p>同じ検討結果フォルダ内の全ファイルをまとめて選択してください。</p>
          <button type="button" onClick={() => packageInput.current?.click()}>ファイルをまとめて選択</button>
          <input ref={packageInput} id="run-package-files" type="file" multiple hidden aria-label="検討結果の全ファイル"
            onChange={event => { const files = Array.from(event.target.files ?? []); event.target.value = ""; void selectPackage(files); }} />
          <p className="small">SDG Run Package：manifest.json / project.json / site.geojson / constraints.json / search-result.json。v0.4のみbuildable-area.geojsonも必要です。5 / 6ファイル同時選択、ZIPは対象外です。</p>
        </details>
        <details className="technical-details direct-intake"><summary>結果データを1ファイルで開く（Search JSON）</summary>
          <label className="field-label" htmlFor="search-result-file">Search Result JSONファイルを選択</label>
          <input ref={fileInput} id="search-result-file" type="file" accept=".json,application/json" aria-describedby="search-file-help"
            onChange={event => { void selectFile(event.target.files?.[0]); event.target.value = ""; }} />
          <span id="search-file-help" className="small">.json / viewer上限 8 MiB / 送信・保存なし</span>
        </details>
      </div>
    </details>
    <div className="search-controls">
      <button type="button" onClick={onSample}>サンプルで試す</button>
      <span className="small">{isSample ? "公開サンプル：架空の都市型オフィス（実案件ではありません）" : "計算はローカルで行い、この画面では結果を比較します。"}</span>
      <button type="button" onClick={clearResult} disabled={!loading && !result && !packageResult}>表示をクリア</button>
    </div>
    <div className="viewer-content" aria-live="polite" aria-atomic="false">
      {loading ? <p className="empty">検討結果を確認中…</p> : null}
      {!loading && !result && !packageResult ? <p className="empty">まず「サンプルで試す」を押すか、「自分の検討結果を開く」から計算済みの検討結果フォルダを開いてください。</p> : null}
      <PackageCheckSummary result={packageResult} />
      {!loading && result?.state === "VIEWER_LIMIT" ? <div className="viewer-message limit-message">
        <strong>この画面の表示上限を超えています</strong><p>データ自体が不正とは限りません。ローカルで計算結果を確認してください。</p>
        <details className="technical-details"><summary>詳細データ：表示上限</summary><p>VIEWER_LIMIT / Schema NOT_CHECKED</p><p>{result.issues[0]?.message}</p></details>
      </div> : null}
      {!loading && result?.state === "INVALID" ? <div className="viewer-message invalid-message">
        <strong>結果データを確認してください</strong><p>対応する計算済みファイルを選んでください。形式の問題は詳細データに表示します。</p>
        <details className="technical-details"><summary>詳細データ：入力形式</summary><p>INVALID · Schema {result.schema}</p>
          <ul className="issues">{result.issues.map((issue,index) => <li key={index}><code>{issue.path}</code><span>{issue.keyword} · {issue.message}</span></li>)}</ul>
        </details>
      </div> : null}
      {!loading && result?.state === "DISPLAYABLE" && model ? <div className="search-results">
        {isSample ? <p className="sample-banner">サンプルを表示中 · 架空の都市型オフィス / 想定用途：オフィス・店舗</p> : null}
        <ComparisonExplanation model={model} />
        {selected ? <CandidateKpis selected={selected} /> : null}
        <div className="summary-grid" aria-label="検討結果の件数">
          <div><span>比較したケース</span><strong>{model.summary.evaluated}</strong></div>
          <div><span>表示できる案</span><strong>{model.summary.accepted}</strong></div>
          <div><span>案のないケース</span><strong>{model.summary.rejected}</strong></div>
          <div><span>ボリューム案</span><strong>{model.summary.hasFeasibleCandidate ? "あり" : "なし"}</strong></div>
        </div>
        {model.summary.reviewRequired ? <div className="review-banner" role="status"><strong>要確認</strong><span>入力条件と出典状態の確認が必要です。</span></div> : null}
        <p className="safety-notice">{SAFETY_NOTICE}</p>
        {model.candidates.length === 0 ? <div className="zero-result"><strong>比較は完了しました</strong><p>今回の条件では表示できるボリューム案がありません。比較した想定階高と、下の「案が作成されなかったケース」を確認してください。</p></div> : (
          <div className="table-scroll candidate-table" tabIndex={0} role="region" aria-label="ボリューム案の比較表（横スクロールできます）">
            <table><caption>想定階高ごとのボリューム案 · 計算結果の順序</caption>
              <thead><tr><th scope="col">案</th><th scope="col">想定階高</th><th scope="col">階数</th><th scope="col">建物高さ</th><th scope="col">建築面積</th><th scope="col">延床面積</th><th scope="col">選択</th></tr></thead>
              <tbody>{model.candidates.map(candidate => {
                const active = selected?.rank === candidate.rank && selected.candidateReference === candidate.candidateReference;
                return <tr key={candidate.rank + "-" + candidate.candidateReference} className={active ? "selected-row" : undefined}>
                  <th scope="row"><strong>{candidateName(candidate.rank)}</strong><span className="small candidate-rank">順位 {candidate.rank}</span></th>
                  <td>{formatMeasure(candidate.floorHeightM)} m</td><td>{candidate.floorCount} 階</td><td>{formatMeasure(candidate.heightM)} m</td><td>{formatMeasure(candidate.footprintAreaM2)} m²</td><td>{formatMeasure(candidate.grossFloorAreaM2)} m²</td>
                  <td><button type="button" className="select-candidate" aria-pressed={active} aria-label={candidateName(candidate.rank) + "（想定階高 " + formatMeasure(candidate.floorHeightM) + " m）を選択"} onClick={() => setSelection(selectionOf(candidate))}>{active ? "選択中" : "この案を見る"}</button></td>
                </tr>;
              })}</tbody>
            </table>
          </div>
        )}
        {selected ? <section className="candidate-detail" aria-labelledby="footprint-title">
          <div><span className="small">選択中：{candidateName(selected.rank)}</span><h3 id="footprint-title">建築面積のかたち</h3>
            <p>想定階高 {formatMeasure(selected.floorHeightM)} m · 延床面積 {formatMeasure(selected.grossFloorAreaM2)} m²</p>
            <p className="small">計算済みの平面形状です。実際の建物配置・後退距離や法規適合を確認する図ではありません。</p>
            {model.schemaVersion === "0.5" ? <p className="footprint-legend small"><span>破線：指定された配置検討範囲</span><span>塗り：選択案の建築面積</span></p> : null}
          </div>
          <div className="footprint-frame">{preview.available ? <svg viewBox={preview.viewBox} role="img" aria-label={candidateName(selected.rank) + "の建築面積（平面図）"} preserveAspectRatio="xMidYMid meet">
            {preview.buildablePoints ? <polygon className="buildable-outline" points={preview.buildablePoints} /> : null}<polygon className="candidate-footprint" points={preview.points} />
          </svg> : <p className="preview-unavailable">この案の平面図は表示できません</p>}</div>
        </section> : null}
        <ConstraintUsagePanel model={model} selected={selected} />
        {isSample ? <section className="sample-conditions"><h3>サンプルの敷地・計画条件</h3><ProjectConditions result={sampleConditions} /></section> : null}
        <AreaBasisPanel model={model} />
        <div className="constraint-panels"><FarStackPanel model={model} /><HeightStackPanel model={model} /></div>
        <BuildableAreaPanel model={model} />
        {model.rejections.length > 0 ? <div className="table-scroll rejection-table"><table><caption>案が作成されなかったケース</caption>
          <thead><tr><th scope="col">想定階高</th><th scope="col">計算結果</th></tr></thead>
          <tbody>{model.rejections.map(rejection => <tr key={rejection.floorHeightM + "-" + rejection.code}><th scope="row">{formatMeasure(rejection.floorHeightM)} m</th><td>{rejection.code === "RESOURCE_LIMIT" ? "計算の処理上限に達しました" : "入力条件から案を作成できませんでした"}</td></tr>)}</tbody>
        </table></div> : null}
        <details className="technical-details result-technical"><summary>詳細データ：計算結果・検証情報</summary>
          <p>Schema PASS / DISPLAYABLE / schemaVersion {model.schemaVersion}</p>
          <p>Schema PASSは、BVE Coreのsemantic validationをブラウザで再実行したことを意味しません。Python export時の検証が正本です。</p>
          <dl className="strategy-list"><div><dt>Search strategy ID</dt><dd><code>{model.strategy}</code></dd></div><div><dt>Ranking strategy ID</dt><dd><code>{model.ranking}</code></dd></div></dl>
          <p>reviewRequired: {String(model.summary.reviewRequired)}</p>
          <ol className="ranking-rules">{RANKING_RULES.map(rule => <li key={rule}>{rule}</li>)}</ol>
          <ul>{model.candidates.map(candidate => <li key={candidate.rank}><span>{candidateName(candidate.rank)} · candidateReference </span><code>{candidate.candidateReference}</code></li>)}</ul>
          <dl>{Object.entries(result.value.inputReferences).map(([key,value]) => <div key={key}><dt>inputReferences.{key}</dt><dd><code>{value}</code></dd></div>)}</dl>
          {model.rejections.map(rejection => <p key={rejection.floorHeightM}>{formatMeasure(rejection.floorHeightM)} m / <code>{rejection.code}</code></p>)}
          <p>SVG: exterior ring / Local XY。座標は変更せず描画時のみY反転。形状の修復・補間・後退・3D化なし。</p>
          <p className="numeric-note">{ROUNDING_NOTICE}<br />JavaScript NumberはPython Decimalや元JSON数値字句の正本ではありません（D04 OPEN）。</p>
        </details>
      </div> : null}
    </div>
  </section>;
}
