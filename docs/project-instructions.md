# Project instructions

目的は建築初期検討の入力条件と出典状態を明示するWeb Gatewayの最小基盤。
計算主体はBVE Core（Buildable Volume Engine）。Current Phase = Phase 2 Constraint Engine Foundation。
Phase 0/1を維持し、明示area basisで既存BCR/FAR/heightを出典付きConstraint Resultへ変換する。

- Next.js / TypeScriptは入力と検証結果の表示、PythonはProject検証・Geometry・Constraintsを担当する。
- 単位を暗黙変換しない。面積はm2、比率はpercent、高さはmをschemaで明示する。
  検証成功は法規適合や建築可能性の証明ではない。
- Phase 2ではProject/Geometry schemaを維持し、Constraint出力schemaだけを追加する。
  schemaVersionの変更は互換性判断を伴うためHumanへ相談する。
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
WebからPythonを呼ばない。massing、本番rulepacks、Run Package、Bridge、API、保存基盤は対象外。
Draft PR作成後STOP。Ready、merge、Vercel deploy、Production、Phase 3、Vault/Notion直接更新は禁止。
Next Gate: Vercel Preview Smoke — REQUIRED BEFORE PHASE 3（Phase 2 merge後の別Run）。
