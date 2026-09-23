"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { SearchResultViewer, type SearchViewerHandle } from "../components/search-result-viewer";
import { ProjectConditions } from "../components/project-conditions";
import { SAFETY_NOTICE } from "../lib/human-labels";
import { PROJECT_PROMPT } from "../lib/prompt";
import { validateFile, type ValidationResult } from "../lib/validation";

export default function Home() {
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [copyMessage, setCopyMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const request = useRef(0);
  const viewer = useRef<SearchViewerHandle>(null);
  const preparation = useRef<HTMLDetailsElement>(null);
  const projectInput = useRef<HTMLInputElement>(null);

  async function copyPrompt() {
    try { await navigator.clipboard.writeText(PROJECT_PROMPT); setCopyMessage("プロンプトをコピーしました。"); }
    catch { setCopyMessage("コピーできませんでした。プロンプト欄を選択してコピーしてください。"); }
  }
  function clearProject() { request.current += 1; setResult(null); setLoading(false); if (projectInput.current) projectInput.current.value = ""; }
  function loadSample() { clearProject(); viewer.current?.loadSample(); }
  function openPreparation() {
    if (preparation.current) { preparation.current.open = true; preparation.current.scrollIntoView({ block: "start" }); preparation.current.querySelector("summary")?.focus(); }
  }
  async function selectFile(file?: File) {
    if (!file) return;
    const current = ++request.current; setLoading(true); setResult(null);
    const next = await validateFile(file);
    if (current === request.current) { setResult(next); setLoading(false); }
  }

  return <main>
    <header className="topbar">
      <Link className="brand" href="/" aria-label="Site Design Gateway ホーム"><span className="mark" aria-hidden="true">SDG</span> Site Design Gateway</Link>
      <span className="product-caption">建築初期検討</span>
    </header>
    <section className="intro" aria-labelledby="intro-title">
      <p className="eyebrow">敷地を知る。条件を確かめる。案を比べる。</p>
      <h1 id="intro-title">敷地条件から、<br />初期ボリュームを比較</h1>
      <p className="lead">敷地・計画条件を整理し、計算済みの案を<br className="desktop-break" />建築面積・延床面積・階数・高さで比較します。</p>
      <div className="entry-actions" aria-label="検討の始め方">
        <button type="button" className="primary" onClick={loadSample}>サンプルで試す<span>架空のオフィスで比較を体験</span></button>
        <button type="button" onClick={() => viewer.current?.openIntake()}>自分の検討結果を開く<span>計算済みのフォルダを選択</span></button>
        <button type="button" onClick={openPreparation}>自分の案件を準備する<span>手持ちの資料・条件を整理</span></button>
      </div>
      <p className="safety-notice">{SAFETY_NOTICE}</p>
      <p className="privacy-note">選んだデータはブラウザ内だけで扱います。送信・保存はしません。</p>
    </section>
    <SearchResultViewer ref={viewer} onSample={loadSample} onClear={clearProject} />
    <details className="panel preparation" ref={preparation} id="preparation">
      <summary>自分の案件を準備する</summary>
      <div className="preparation-content">
        <h2>手持ちの資料から始めましょう</h2>
        <p>全部揃ってから始める必要はありません。未確認の値、仮定した値、図面から取得した値を分けて整理し、後から根拠を確認できます。</p>
        <div className="preparation-grid">
          <section><span className="step">01</span><h3>敷地形状</h3><p>DXF・GeoJSONや、その他の図面資料。敷地境界と単位が分かる資料を用意します。</p></section>
          <section><span className="step">02</span><h3>敷地・法規条件</h3><p>敷地面積、建ぺい率、容積率、高さ制限。分かる範囲で、値と出典・確認状態を揃えます。</p></section>
          <section><span className="step">03</span><h3>計画条件</h3><p>想定用途、比較したい想定階高、その他の初期条件。今回の比較では想定階高を変えます。</p></section>
          <section><span className="step">任意</span><h3>配置検討範囲</h3><p>外部で作成済みの配置可能範囲があれば用意します。法的に建築可能な範囲であることを示すものではありません。</p></section>
        </div>
        <div className="hybrid-route"><h3>準備から比較まで</h3><ol><li>手持ち資料と条件を整理する。</li><li>ローカルのSDG / BVE Coreで入力を確認し、ボリューム案を計算する。</li><li>この画面の「自分の検討結果を開く」から計算済みフォルダを選ぶ。</li></ol>
          <p>現在、このWeb画面では計算・PDF / DXFの自動解析・住所からの法規取得は行いません。</p>
        </div>
        <details className="technical-details prompt-preparation"><summary>AIを使って入力データを準備する</summary>
          <ol><li>利用権限と公開可否を確認した手持ちの敷地資料・計画条件を、ChatGPT / Claude / Gemini等へ渡します。</li><li>下の補助プロンプトを一緒に渡します。</li><li>生成されたProject JSONの値と出典を人が確認し、local BVE Coreで使用します。</li></ol>
          <p className="small">この画面からAIへの送信は行いません。AI調査値を公式確認済みとして扱わないでください。</p>
          <div className="prompt-actions"><span className="small">Project JSON / Schema v0.1 + synthetic sample</span><button type="button" onClick={copyPrompt}>補助プロンプトをコピー</button></div>
          <label className="field-label" htmlFor="project-prompt">Project JSON生成プロンプト</label>
          <textarea id="project-prompt" className="prompt" value={PROJECT_PROMPT} readOnly spellCheck={false} />
          <p className="feedback" role="status">{copyMessage}</p>
        </details>
        <details className="technical-details"><summary>準備した入力データを確認する（Project JSON）</summary>
          <p>計算前に、入力形式と確認状態をブラウザ内で確認できます。ここではボリューム計算は行いません。</p>
          <label className="field-label" htmlFor="project-file">入力条件のJSONファイル</label>
          <input ref={projectInput} id="project-file" type="file" accept=".json,application/json" aria-describedby="file-help" onChange={event => { void selectFile(event.target.files?.[0]); event.target.value = ""; }} />
          <p id="file-help" className="small">256 KiBまで / 送信・保存なし</p>
          <div aria-live="polite" aria-busy={loading}>{loading ? <p>入力条件を確認中…</p> : result ? <ProjectConditions result={result} /> : <p className="empty">準備済みの入力データを選ぶと、敷地面積などの値と確認状態を表示します。</p>}</div>
          <button type="button" onClick={clearProject} disabled={!loading && !result}>入力条件の表示をクリア</button>
        </details>
      </div>
    </details>
    <footer><span>Site Design Gateway</span><span>入力条件と出典を確かめながら、初期検討を進める。</span></footer>
  </main>;
}
