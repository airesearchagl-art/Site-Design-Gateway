# Web Results Viewer / Phase 10 FAR stack contract

Current Phase = Phase 10 Constraint Stack / Effective FAR Foundation。Phase 5 privacy/resource・Phase 7表示境界を維持する。

Web は、ローカル BVE Core が canonical export した Search Result JSON をユーザーが選択し、
ブラウザ内だけで形式確認・比較表示する read-only consumer である。

```text
Python BVE Core → explicit local Search Result JSON → browser-only viewer
```

Web は compute runtime ではない。Next.js API route、Server Action、Python subprocess / HTTP service、
serverless BVE、WebSocket、worker Python execution、TypeScript への BVE 計算移植を持たない。
Project、Geometry、Constraints、Massing、Search の計算や、candidate hash・順位・cap・包含の意味検証を再実行しない。

## 入力と状態

直接入力は `.json` ファイル1件または tracked synthetic sample。追加の5-file package入口は後述。内容は React state と処理中の一時値だけに保持し、
送信、保存、upload、form submission、telemetry、console 出力をしない。`Clear result` は表示中の Search Result と選択を破棄する。

viewer state は `EMPTY`、`LOADING`、`DISPLAYABLE`、`INVALID`、`VIEWER_LIMIT` を区別する。
上限は 8 MiB。超過時は bytes を読まず `VIEWER_LIMIT` とし、Search Result 自体を `INVALID` と呼ばない。
拡張子、UTF-8、JSON 構文、nesting depth と Schema をブラウザ内で検証する。silent truncation はしない。

JSON.parseの前にraw textを1回走査し、値の出現数250,000・root depth 0からの深さ64を確認する。
文字列内の記号やobject keyは数えず、重複keyで後から上書きされる値も割当予算として数える。
stackは深さ上限に比例する大きさだけを保持し、token列・object graphを作らない。
予算超過は直ちにVIEWER_LIMIT / NOT_CHECKEDとし、parseしない。構文判定はJSON.parseに委ねる。
parse後にも同じnode/depth上限を防御として確認する。byte上限8 MiBと表示・semantic境界は変更しない。

## Schema 境界

正本はSearch Result v0.1/v0.2/v0.3のschema。Ajv の offline registry へ Project、Geometry、
Constraint Result、Massing Candidate、Search Result、Run Manifestのlegacy 7schemaと新4schemaを登録し、Web用copyを作らない。
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

数値はJavaScript Numberによる表示値であり、m/m²は最大小数3桁、割合は小数1桁、en-USの桁区切りを使う。
丸め表示とcanonical JSON不変をUIで明示する。法規丸めではない。JavaScript NumberはPython Decimalおよび
元JSONの数値字句の正本ではない（D04 OPEN）。lossless parserは追加しない。

## Phase 7 interpretation

Pythonの新規exportはv0.2。root必須constraintContext.areaBasisは既存Constraint schemaへの$ref、
constraintCapsは既存Massing schemaへの$ref。Pythonがcanonical Constraint bytesのhashとcontext exact copyを照合する。
candidate capsはroot capsと一致する。v0.1を改版せず、legacyではArea basisに
`Context unavailable in legacy Search Result v0.1`と表示する。2ファイル選択やbasis推測は行わない。

Area basisはselectedBasis / basis / declared / geometry / signed differenceを表示する。
nullはUnavailable。zero acceptedでもbasisとcapは表示し、candidate usageはUnavailableとする。
選択候補のfootprint/GFA/heightにActual、Cap、Remaining、Usage %を表示する。
許される表示用演算はcap-actualとactual/capのみ。clampしない。ゼロ除算・非有限の表示値はUnavailable。
これは支配的な法規制約の判定でも法規適合の証明でもない旨をpanel直下に明示する。

Ranking ruleはGFA降順、正本GFAが等しければ階高昇順、最後にcandidateReference辞書順と説明する。
authoritative rankと配列順を保ち、ブラウザで再sort・Decimal equality推定・TIED badge付与をしない。

## 公開fixture

`cases/example-urban-office/search-result.json` は完全合成の deterministic canonical contract fixture。
Python CLI pipeline（Project / Geometry / Constraints / Search [4,5,6,7,8]）のactual bytesを追跡し、
Python exact-byte testでCoreへ固定する。一般のruntime/private Search Resultは公開Gitへ含めない。

SDG-VP-001はBLOCKED_EXTERNAL、D02はOPEN / PLATFORM_BLOCKED。VMVP-001はPASS WITH TARGET ANOMALYを継承。
Phase 10でVercelは操作しない。

## Run Package v0.1 browser入口

`File[]`相当の選択から確認する独立validatorを、folder picker（webkitdirectory）と通常のmultiple inputで共用する。
exact setはmanifest.json / project.json / site.geojson / constraints.json / search-result.json。
missing、extra、duplicate、hidden metadataはINVALID。relative pathがある場合、全fileは同じrootのdirect childのみ。
空relative pathのfallbackではexact filename setを確認する。rootや絶対pathは表示・保存・errorへ含めない。
manifestの固定pathはcanonical Schemaで制限し、実読込は固定name mapのみから行う。

| File | Web byte limit |
| --- | --- |
| manifest.json | 256 KiB |
| project.json | 256 KiB |
| site.geojson | 4 MiB |
| constraints.json | 4 MiB |
| search-result.json | 8 MiB |

全File.sizeを確認する前にarrayBufferを呼ばない。読込後もactual bufferを再確認し、UTF-8をstrict decodeする。
manifestを先に読みshared Schemaを検証し、その後artifactを逐次処理する。raw preflightは全artifactへ適用し、
Searchは既存validateSearchJsonの8 MiB / depth64 / 250,000 nodes境界を通る。package内Searchはv0.2のみ。
PythonのSearch package上限256 MiBはWebへ持ち込まない。VIEWER_LIMITはpackage不正を意味せず、Python verifyで有効な場合もある。

crypto.subtle.digest("SHA-256", exact selected bytes)で4artifactをhash化しmanifest referenceと照合する。
鍵生成・署名・暗号化はしない。constraintsのproject/geometryとSearchのproject/geometry/constraintsのroot参照を照合する。
manifestのareaBasisはconstraints selectedBasisと、floorHeightsMはSearchの長さ/順序/parsed valuesと一致を要求する。
sort・補完・Decimal同値推定はしない。exact-byte hashでもJSON.parseの数値字句問題は解決せずD04 OPEN。

PASS時は同じSearch validation resultを既存Viewerへhandoffし、表示経路を複製しない。
UIはPackage integrity / version / artifact count / Browser checkを表示し、次を明示する。

- Package integrity and shared-schema checks passed in this browser.
- Python `bve.run verify` remains the authoritative semantic verifier.

integrityは署名・作成者認証・法規適合ではない。candidate hash、geometry、constraints、massing、rankingの意味検証はPythonが正本。
zero acceptedでもArea Basis/caps/rejectionsを表示し、candidate usageはUnavailable。直接Search v0.1/v0.2とsampleを維持する。
errorは固定filename/code/一般説明だけ。raw JSON、hash値、任意key、例外、stackをechoしない。

Clearはpackage issues、Search、candidate、SVG、input値を解除してEMPTYへ戻す。
abortと世代番号で進行中読込・hashの後のhandoffを防ぎ、buffer等をstorageへ退避しない。
recursive privacy scanはnetwork、storage、Cache API、File System Access write、service worker、consoleを禁止する。
ZIP、保存、編集、API、Python実行、新dependencyは対象外。Phase 8 Run Package契約自体は変更しない。

## Phase 10 FAR display and version routes

直接Project0.1/0.2、Search0.1/0.2/0.3、Package0.1/0.2を受け入れる。package matrixは
[Run Package契約](run-package-contract.md)と同一で、artifactのversion混在を拒否する。
Project0.2のduplicate cap IDsは構造的identityとして拒否する。WebでFAR semantic再計算はしない。
Search0.3のFAR panelはbase/additional、status/review、effective cap、source IDs、max GFAを出力順に表示する。
legacyにはcontext unavailableと表示し、Area Basis / Constraint Usageを維持する。
Python出力のeffectiveCapPercent / effectiveCapIdsを使い、min / tie / sort / governing判定は行わない。
表示用のen-US丸めだけを適用し、JSON値を変更しない。D04 OPEN。

- Effective FAR cap is the minimum of the explicit numeric caps supplied to BVE.
- It does not identify the governing legal rule or prove regulatory compliance.

ClearはFAR panelも含めて破棄する。既存8 MiB・depth64・node250000・all-file preflight・actual-buffer再確認、
128 MiB probes、network/storage禁止、遅延handoff防止を維持する。
