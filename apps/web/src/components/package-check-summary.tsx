import type { PackageValidationResult } from "../lib/run-package-validation.ts";

export function PackageCheckSummary({ result }: { result: PackageValidationResult | null }) {
  if (!result) return null;
  if (result.state === "DISPLAYABLE") return <div className="package-check package-pass" role="status">
    <strong>検討結果フォルダを読み込みました</strong>
    <p>計算済みの結果を表示しています。計算内容の検証はローカルのPythonが正本です。</p>
    <details className="technical-details"><summary>詳細データ：フォルダの検証</summary>
      <strong>Package integrity PASS</strong>
      <dl className="package-facts"><div><dt>Package version</dt><dd>{result.packageVersion}</dd></div><div><dt>Artifacts</dt><dd>{result.artifactCount} + manifest（{result.artifactCount + 1}ファイル）</dd></div><div><dt>Browser check</dt><dd>DISPLAYABLE</dd></div></dl>
      <p>Package integrity and shared-schema checks passed in this browser.</p>
      <p className="package-authority">Python <code>bve.run verify</code> remains the authoritative semantic verifier.</p>
      <p className="small">共有Schema・exact bytesのSHA-256・入力参照・設定の整合性を確認しました。署名や作成者認証、法規適合の確認ではありません。設定比較はJSON.parse後のNumberによるもので、Decimalの同値証明ではありません（D04 OPEN）。</p>
    </details>
  </div>;
  return <div className={"package-check " + (result.state === "VIEWER_LIMIT" ? "limit-message" : "invalid-message")} role="status">
    <strong>{result.state === "VIEWER_LIMIT" ? "この画面の表示上限を超えています" : "検討結果フォルダを確認してください"}</strong>
    <p>{result.state === "VIEWER_LIMIT" ? "データ自体が不正とは限りません。ローカルで確認してください。" : "同じ計算で作成されたフォルダ内の全ファイルを選んでください。問題の箇所は詳細データで確認できます。"}</p>
    <details className="technical-details"><summary>詳細データ：読込エラー</summary>
      <p>Package · {result.state}</p><p><code>{result.issues[0].file}</code> · {result.issues[0].code} · {result.issues[0].message}</p>
      {result.state === "VIEWER_LIMIT" ? <p>local Python verifyでは有効でも、Webでは表示できない場合があります。Search ResultのWeb上限は8 MiBです。</p> : null}
    </details>
  </div>;
}
