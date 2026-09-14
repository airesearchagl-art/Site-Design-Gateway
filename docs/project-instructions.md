# Project instructions

目的は建築初期検討の入力条件と出典状態を明示するWeb Gatewayの最小基盤。
計算主体は将来のBVE Core（Buildable Volume Engine）。Phase 0はJSON検証だけを実装する。

- Next.js / TypeScriptは入力と検証結果の表示、Pythonは同じschemaの検証境界を担当する。
- 単位を暗黙変換しない。面積はm2、比率はpercent、高さはmをschemaで明示する。
  検証成功は法規適合や建築可能性の証明ではない。
- 共通schemaを先に変更し、fixtureと両側のテストで契約を確認する。
  schemaVersionの変更は互換性判断を伴うためHumanへ相談する。
- 日本語で簡潔に結果と未確認事項を報告する。UI内へ運用上の実装手順を混ぜない。
- Runtime dataをpublic fixtureに転用しない。開発・CI・ブラウザ検証もsyntheticのみ。
- `AGENTS.md`、README、対象ファイルと直接依存を先に読む。
- 実行環境の不調は原因と未実施checkを記録して独立作業を続ける。
  実際のprivacy/security/data-integrity違反は即停止する。
- 最終出口はDraft PR。remote authが利用不能ならlocal commitsを保全して停止する。

Phase 1以降の候補はgeometry、massing、rulepacks、Run PackageとBridgeの接続。
今回これらの空frameworkや未使用packageは追加しない。
