# Repository rules

- このRepositoryはPublic。source、schema、匿名synthetic fixture、テスト、文書だけを保存する。
- 実案件データ、実案件名・住所、施主情報、個人を識別するローカルパス、秘密情報、
  .envの値、署名付きURL、CAD/BIM/PDF原本、runtime input/log/dumpをGitへ入れない。
- fixtureは `cases/example-urban-office/` のsynthetic dataのみ。
- `schemas/sdg-project-v0.1.schema.json` が案件条件の正本。Web/Pythonで別schemaを作らない。
- BVE Coreに案件・自治体固有処理を埋め込まない。LLM調査値をofficial_verifiedへ昇格しない。
- Phase 0はvalidationまで。geometry、massing、rule engine、認証、DB、外部storage、Bridgeは対象外。
- mainへ直接commitしない。作業branchでcheckpoint commitを残す。force push、破壊的cleanupは禁止。
- Human承認なしReady/merge禁止。このCampaignではProductionとPhase 1開始も禁止。
- Credentialの生成・取得・store変更、OS/GitHub権限変更は禁止。
- Notion/Obsidianを開発IDEから直接更新しない。最終報告にDocumentation Sync Triggerを返す。
- Scope拡張はHuman Gate。Phase 0で未使用のdependencyを将来用途で入れない。
- 入力はbrowser memoryだけで検証する。upload API、telemetry、storage、入力全文のconsole/logを追加しない。
- Required checks: `python -m pytest`, `npm run lint`, `npm run test`, `npm run build`。
  CIにはsyntheticのみを使う。変更に対応する境界テストを実施し、未実行をPASSとしない。
- Project instructions: `docs/project-instructions.md`。Public境界: `docs/public-private-data-boundary.md`。
- Long Run再開はmanifest/state/queue/debtを読み、branch/base/treeとexact local packetのSHA-256を確認する。
  exact packetは個人パスを含むためGit除外。公開要約をexact snapshotの代用にしない。
