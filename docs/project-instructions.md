# Project instructions

目的は建築初期検討の入力条件と出典状態を明示するWeb Gatewayの最小基盤。
計算主体はBVE Core（Buildable Volume Engine）。Current Phase = Phase 9 Run Package Viewer Intake Foundation。
Phase 0〜8を維持し、固定5ファイルのRun Packageをbrowser-onlyで確認して既存Viewerへ渡す。

- Next.js / TypeScriptはProject検証とSearch Resultの形式確認・read-only表示、PythonはProject検証・Geometry・Constraints・Massing・Search計算とsemantic exportを担当する。
- 単位を暗黙変換しない。面積はm2、比率はpercent、高さはmをschemaで明示する。
  検証成功は法規適合や建築可能性の証明ではない。
- 既存7schemaを維持する。WebはRun Manifestを含む7schemaをoffline参照し、直接Searchはv0.1/v0.2を受け入れる。
  追加のschemaVersion変更は互換性判断を伴うためHuman Gateとする。
- 日本語で簡潔に結果と未確認事項を報告する。UI内へ運用上の実装手順を混ぜない。
- Runtime dataをpublic fixtureに転用しない。開発・CI・ブラウザ検証もsyntheticのみ。
- `AGENTS.md`、README、対象ファイルと直接依存を先に読む。
- 実行環境の不調は原因と未実施checkを記録して独立作業を続ける。
  実際のprivacy/security/data-integrity違反は即停止する。
- 最終出口はDraft PR。remote authが利用不能ならlocal commitsを保全して停止する。

Geometryはlocal XY・m/mmの明示入力だけをmへ正規化する。Shapelyを唯一の計算Coreとし、
DXF読込はezdxfを使う。未知単位・未知CRS・曲線・不正Polygonを推測や修復で採用しない。
正規化Geometry schemaはProject schemaと別契約。既存Project schemaを複製・改版しない。
Constraintsは検証済みProjectとSiteGeometryから固定の3計算だけを行う。normalized読込の
Polygon検証はGeometryへ集約する。面積の自動選択・任意threshold・丸め・status昇格・formula DSLは禁止。
出力のexact input hash、個別null/absent状態、provenance、reviewRequiredを保持する。
Massingは凸・穴なし敷地、固定homothetic footprintと同形整数階stackだけ。
Constraint Resultはschemaと再計算で検証し、Geometry referenceを一致させる。階高の既定値は禁止。
actual areaを丸めずcapと包含を再確認する。法規適合・後退・最適性を主張しない。
WebからPythonを呼ばない。floorHeight以外の探索、3D、本番rulepacks、Bridge、API、保存基盤は対象外。
Draft PR作成後STOP。Ready、merge、Vercel操作、Production、Phase 10、Vault/Notion直接更新は禁止。
旧Preview必須GateはSDG-VP-001 BLOCKED_EXTERNAL、D02 OPEN / PLATFORM_BLOCKEDとして切り離された。
意図しないProduction分類2件は削除済み。Git切断確認後、HumanのPhase 3 transition exception = AUTHORIZED。
このPhaseではVercelを再検証せず、別Runで原因と安全経路をfresh auditする。

Phase 4 SearchはfloorHeightだけを探索し、Human明示値1..64件を使う。default gridなし、duplicate拒否。
Phase 3 Generatorを逐次再利用し、GFA降順だけでrankingする。rankingはdesign qualityではない。
tie-breakは階高昇順/hash昇順でserialization用。footprint探索・optimizer・実法規・weighted scoreはない。
Search schema、exact candidate hash、partition/rank/summary/reviewのsemantic再検証を追加する。
Vercel D02はOPEN / PLATFORM_BLOCKEDを維持する。詳細: docs/search-contract.md。

Phase 5 WebはSearch Resultをbrowser memoryだけで読み、8 MiB viewer limitとSchema INVALIDを分離する。
summary/ranking/rejection/zero accepted、review warning、rank/reference選択、exterior ringの2D SVGだけを表示する。
BVE arithmetic、canonical hash、ranking semantic validatorをTypeScriptへ移植しない。Schema PASSはPython semantic PASSを意味しない。
upload、fetch、storage、telemetry、編集・保存・download、3D、Project/Search hash bindingは対象外。詳細: docs/web-results-contract.md。

Phase 7ではauthoritative Constraint Result由来のcontextをSearch v0.2へcopyし、Pythonでexact referenceと照合する。
UIにはbasis、cap、actual、remaining、usage、ranking ruleを表示する。単純な表示用差分/比率のみ許可し、
法規計算、governing constraint、clamp、再sort、同順位badgeを追加しない。en-US丸め表示と原本保持を明記する。
D04 OPEN。Phase 6 private workspaceや詳細reportを参照・転記しない。Vercel状態は継承のみ。

Phase 8 Run PackageはProject/Geometry/Constraints/Searchの既存public APIとcanonical exporterを再利用する。
manifest v0.1は独立schemaであり既存6schemaは変更しない。area basisと階高はHuman明示、defaultなし。
strict fixed file set、hash/相互参照/意味検証、既存target拒否、完全staging検証後のatomic公開を必須とする。
Phase 8でWeb production sourceとdependencyは変更しなかった。詳細: docs/run-package-contract.md。

Phase 9のpackage入口はdocs/web-results-contract.mdに従う。fixed file set/path、全file先行size確認、
exact-byte SHA-256、root入力参照、basis/階高のparsed値と順序を検証する。共有7schemaはcopyしない。
Python semantic authorityをUIに明示し、計算・candidate hash・順位を再実行しない。D04 OPEN。
直接Search、Phase 7表示、resource preflight、privacyを維持し、Clearの非同期競合も検証する。
packageのtest helperはpublic syntheticを既存Pythonで一時生成するだけ。runtime packageを追跡しない。
