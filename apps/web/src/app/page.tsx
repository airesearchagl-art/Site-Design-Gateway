"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import sample from "../../../../cases/example-urban-office/project.json" with { type: "json" };
import { PROJECT_PROMPT } from "../lib/prompt";
import { validateFile, validateJson, type ValidationResult } from "../lib/validation";

const statusLabels: Record<string, string> = {
  official_verified: "公式資料で確認済み（申告）",
  user_provided: "ユーザー提供",
  drawing_derived: "図面から取得",
  llm_researched: "LLM調査・公式未確認",
  assumed: "仮定・要確認",
  unknown: "不明・要確認",
  review_required: "レビュー待ち",
};

export default function Home() {
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [copyMessage, setCopyMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const request = useRef(0);

  async function copyPrompt() {
    try {
      await navigator.clipboard.writeText(PROJECT_PROMPT);
      setCopyMessage("プロンプトをコピーしました。");
    } catch {
      setCopyMessage("コピーできませんでした。プロンプト欄を選択してコピーしてください。");
    }
  }

  function loadSample() {
    request.current += 1;
    setLoading(false);
    setResult(validateJson(JSON.stringify(sample)));
  }

  async function selectFile(file?: File) {
    if (!file) return;
    const current = ++request.current;
    setLoading(true);
    setResult(null);
    const next = await validateFile(file);
    if (current === request.current) {
      setResult(next);
      setLoading(false);
    }
  }

  return (
    <main>
      <header className="topbar">
        <Link className="brand" href="/" aria-label="Site Design Gateway ホーム"><span className="mark" aria-hidden="true">SDG</span> Site Design Gateway</Link>
        <span className="phase">PHASE 0 / INPUT VALIDATION</span>
      </header>

      <section className="intro" aria-labelledby="intro-title">
        <p className="eyebrow">条件から、次の検討へ。</p>
        <h1 id="intro-title">Site Design Gateway</h1>
        <p className="lead">建築初期検討の入力条件を、確かめられる形に。<br />Project JSONの形式と、数値の出典状態を確認します。</p>
        <p className="note">Phase 0では入力の検証まで。法規適合の判定やボリューム生成は行いません。</p>
      </section>

      <div className="workflow">
        <section className="panel" aria-labelledby="create-title">
          <span className="step">STEP 01</span>
          <h2 id="create-title">1. Create Project JSON</h2>
          <p>プロンプトをChatGPT・Claude・Geminiなどへ渡して、共通形式のJSONを作成します。</p>
          <div className="prompt-actions">
            <span className="small">Schema v0.1 + synthetic sample</span>
            <button type="button" onClick={copyPrompt}>Copy prompt</button>
          </div>
          <label className="field-label" htmlFor="project-prompt">Project JSON生成プロンプト</label>
          <textarea id="project-prompt" className="prompt" value={PROJECT_PROMPT} readOnly spellCheck={false} />
          <p className="feedback" role="status">{copyMessage}</p>
          <p className="note">出典の状態を残したまま生成します。LLM調査値は「公式確認済み」と区別します。</p>
        </section>

        <section className="panel" aria-labelledby="upload-title">
          <span className="step">STEP 02</span>
          <h2 id="upload-title">2. Upload Project JSON</h2>
          <p>まずは架空のサンプルで確認できます。選択したJSONはブラウザ内で検証し、送信・保存しません。</p>
          <button type="button" className="primary sample" onClick={loadSample}>サンプルを読み込む</button>
          <p className="small">example-urban-office · 架空の都市型オフィス</p>
          <div className="file-zone">
            <label className="field-label" htmlFor="project-file">JSONファイルを選択</label>
            <input id="project-file" type="file" accept=".json,application/json" aria-describedby="file-help" onChange={(event) => { void selectFile(event.target.files?.[0]); event.target.value = ""; }} />
            <p id="file-help" className="small">.json / 256 KiBまで</p>
          </div>
          <div className="placeholders" aria-label="将来のファイル対応">
            <button type="button" disabled>DXF upload · 今後対応</button>
            <button type="button" disabled>PDF upload · 今後対応</button>
          </div>
        </section>
      </div>

      <section className="panel results" aria-labelledby="result-title" aria-busy={loading}>
        <div className="result-heading"><h2 id="result-title">Validation result</h2><span className="small">形式と出典を、別々に確認</span></div>
        <div aria-live="polite" aria-atomic="true">
          {loading ? <p>読み込み中…</p> : !result ? <p className="empty">サンプルまたはJSONファイルを読み込むと、ここに結果を表示します。</p> : (
            <>
              <div className="verdict"><strong className={`badge ${result.outcome.toLowerCase()}`}>{result.outcome}</strong><span>Schema <b>{result.schema}</b></span></div>
              <p>{result.outcome === "INVALID" ? "JSONの形式に問題があります。以下の項目を確認してください。" : result.outcome === "REVIEW_REQUIRED" ? "形式は適合しています。仮定・不明・レビュー待ちの条件を確認してください。" : "形式は適合しています。各出典と値の妥当性は引き続き確認してください。"}</p>
              {result.issues.length > 0 ? <ul className="issues">{result.issues.map((issue, index) => <li key={`${issue.path}-${index}`}><code>{issue.path}</code><span>{issue.message}</span></li>)}</ul> : null}
              {result.sources.length > 0 ? (
                <div className="table-scroll"><table><caption>入力値の出典status（入力の申告を表示）</caption><thead><tr><th scope="col">項目</th><th scope="col">値 / 単位</th><th scope="col">出典status</th></tr></thead><tbody>{result.sources.map((source) => <tr key={source.path}><th scope="row"><code>{source.path}</code></th><td>{source.value ?? "未確定"} <span className="small">{source.unit}</span></td><td><span className={`source-tag ${source.status}`}>{source.status}</span><br /><span className="small">{statusLabels[source.status]}</span></td></tr>)}</tbody></table></div>
              ) : null}
            </>
          )}
        </div>
      </section>
      <footer><span>Site Design Gateway · BVE Core</span><span>入力条件 / 出典 / 再現可能な検討</span></footer>
    </main>
  );
}
