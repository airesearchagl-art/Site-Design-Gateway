import type { PackageValidationResult } from "../lib/run-package-validation.ts";

export function PackageCheckSummary({ result }: { result: PackageValidationResult | null }) {
  if (!result) return null;
  if (result.state === "DISPLAYABLE") {
    return (
      <div className="package-check package-pass" role="status">
        <strong>Package integrity PASS</strong>
        <dl className="package-facts">
          <div><dt>Package version</dt><dd>{result.packageVersion}</dd></div>
          <div><dt>Artifacts</dt><dd>{result.artifactCount} + manifest（5ファイル）</dd></div>
          <div><dt>Browser check</dt><dd>DISPLAYABLE</dd></div>
        </dl>
        <p>Package integrity and shared-schema checks passed in this browser.</p>
        <p className="package-authority">Python <code>bve.run verify</code> remains the authoritative semantic verifier.</p>
        <p className="small">このブラウザでは共有Schema・exact bytesのSHA-256・入力参照・設定の整合性を確認しました。
          計算内容の意味検証はPythonが正本です。署名や作成者認証、法規適合の確認ではありません。
          設定比較はJSON.parse後のNumberによるもので、Decimalの同値証明ではありません（D04 OPEN）。</p>
      </div>
    );
  }
  return (
    <div className={`package-check ${result.state === "VIEWER_LIMIT" ? "limit-message" : "invalid-message"}`} role="status">
      <strong>Package · {result.state}</strong>
      <p><code>{result.issues[0].file}</code> · {result.issues[0].code} · {result.issues[0].message}</p>
      {result.state === "VIEWER_LIMIT" ? (
        <p>package自体が不正とは限りません。local Python verifyでは有効でも、Webでは表示できない場合があります。
          Search ResultのWeb上限は8 MiBです。</p>
      ) : null}
    </div>
  );
}
