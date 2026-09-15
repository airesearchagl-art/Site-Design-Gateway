# Phase 5 Web Results Viewer contract

Current Phase = Phase 5 Web Results Viewer Foundation。

Web は、ローカル BVE Core が canonical export した Search Result JSON をユーザーが選択し、
ブラウザ内だけで形式確認・比較表示する read-only consumer である。

```text
Python BVE Core → explicit local Search Result JSON → browser-only viewer
```

Web は compute runtime ではない。Next.js API route、Server Action、Python subprocess / HTTP service、
serverless BVE、WebSocket、worker Python execution、TypeScript への BVE 計算移植を持たない。
Project、Geometry、Constraints、Massing、Search の計算や、candidate hash・順位・cap・包含の意味検証を再実行しない。

## 入力と状態

入力は `.json` ファイル1件または tracked synthetic sample。内容は React state と処理中の一時値だけに保持し、
送信、保存、upload、form submission、telemetry、console 出力をしない。`Clear result` は表示中の Search Result と選択を破棄する。

viewer state は `EMPTY`、`LOADING`、`DISPLAYABLE`、`INVALID`、`VIEWER_LIMIT` を区別する。
上限は 8 MiB。超過時は bytes を読まず `VIEWER_LIMIT` とし、Search Result 自体を `INVALID` と呼ばない。
拡張子、UTF-8、JSON 構文、nesting depth と Schema をブラウザ内で検証する。silent truncation はしない。

## Schema 境界

正本は `schemas/sdg-search-result-v0.1.schema.json`。Ajv の offline registry へ Project、Geometry、
Constraint Result、Massing Candidate、Search Result の既存5schemaを登録し、Web用copyを作らない。
Ajv の問題表示は instance path、keyword、固定の一般説明だけとし、入力断片や raw exception message を含めない。

Schema PASS はブラウザで BVE Core の semantic validation を再実行したことを意味しない。
canonical hash、input binding、rank partition、constraint arithmetic、geometry/cap containmentの正本は
Python export時のsemantic validationである。Project JSON と Search Result のbrowser-side hash bindingもPhase 5対象外。

## 表示契約

summary は evaluated / accepted / rejected / hasFeasibleCandidate / reviewRequired、Search strategy、Ranking strategyを表示する。
`reviewRequired=true` は `REVIEW REQUIRED` と明示し、falseでも法規確認や承認を示さない。

accepted は既存順序のまま rank、floor height、floor count、building height、footprint area、GFA、
candidateReference を表示する。初期選択は rank 1。選択は rank と candidateReference で照合し、browser stateだけに保持する。
順位はGFA降順の比較であり、設計品質・推奨・最適性・法規適合を意味しない。

accepted=0 / hasFeasibleCandidate=false は正常な完了結果として扱い、表示可能なcandidateがない旨と
floor height / fixed code のrejection一覧を表示する。fixed codeへ法規解釈を加えない。

選択candidateの `candidate.footprint.coordinates[0]` だけを Local XY のconceptual SVGとして表示する。
source coordinatesは変更せず、Y反転は描画座標だけに適用する。repair、補間、setback、convex hull、3D化はしない。
有限で正の描画boundsを安全に得られない場合は、そのpreviewだけを unavailable とする。

数値はSearch ResultからJavaScript Numberとして表示するだけで、計算や意味のある丸めをしない。
JavaScript NumberはPython Decimalおよび元JSONの数値字句の正本ではない（D04）。

## 公開fixture

`cases/example-urban-office/search-result.json` は完全合成の deterministic canonical contract fixture。
Python CLI pipeline（Project / Geometry / Constraints / Search [4,5,6,7,8]）のactual bytesを追跡し、
Python exact-byte testでCoreへ固定する。一般のruntime/private Search Resultは公開Gitへ含めない。

SDG-VP-001はBLOCKED_EXTERNAL、D02はOPEN / PLATFORM_BLOCKED。Phase 5でVercelは操作しない。
