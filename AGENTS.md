# Repository rules

- このRepositoryはPublic。source、schema、匿名synthetic fixture、テスト、文書だけを保存する。
- 実案件データ、実案件名・住所、施主情報、個人を識別するローカルパス、秘密情報、
  .envの値、署名付きURL、CAD/BIM/PDF原本、runtime input/log/dumpをGitへ入れない。
- fixtureは `cases/example-urban-office/` のsynthetic dataのみ。
- `schemas/sdg-project-v0.1.schema.json` が案件条件の正本。Web/Pythonで別schemaを作らない。
- BVE Coreに案件・自治体固有処理を埋め込まない。LLM調査値をofficial_verifiedへ昇格しない。
- Current Phase = Phase 9 Run Package Viewer Intake Foundation。固定5ファイルをbrowser-onlyで検証し、
  既存Search Viewerへ渡す。Python production sourceと既存7schemaは変更しない。
- Project/Geometry/Constraint/MassingおよびSearch v0.1 schemaは維持。Search v0.2は既存schemaへの参照でcontextを追加する。
  Web compute、semantic再計算、編集・保存、3D、認証、DB、Bridgeは対象外。
- mainへ直接commitしない。作業branchでcheckpoint commitを残す。force push、破壊的cleanupは禁止。
- このCampaignではReady、merge、Vercel操作、Production、Phase 10開始は禁止。Draft PR作成直後にSTOP。
- SDG-VP-001はBLOCKED_EXTERNAL。D02 OPEN / PLATFORM_BLOCKEDを継承し、Preview PASSとは扱わない。
  Preview意図の2経路がProduction分類され両方削除済み。Git Integration DISCONNECTED確認後、
  HumanのPhase 3 transition exception = AUTHORIZED。旧Preview必須条件はこの例外で解除された。
- Credentialの生成・取得・store変更、OS/GitHub権限変更は禁止。
- Notion/Obsidianを開発IDEから直接更新しない。最終報告にDocumentation Sync Triggerを返す。
- Scope拡張はHuman Gate。現Phaseで未使用のdependencyを将来用途で入れない。
- Web入力はbrowser memoryだけで検証する。Python Geometry/Constraints/Massing/Searchは独立CLIとして明示runtime出力のみ許可。
- upload API、telemetry、storage、入力全文や座標列のconsole/logを追加しない。
- Required checks: `python -m pytest`, `npm run lint`, `npm run test`, `npm run build`。
  CIにはsyntheticのみを使う。変更に対応する境界テストを実施し、未実行をPASSとしない。
- Project instructions: `docs/project-instructions.md`。Public境界: `docs/public-private-data-boundary.md`。
- Long Run再開はmanifest/state/queue/debtを読み、branch/base/treeとexact local packetのSHA-256を確認する。
  exact packetは個人パスを含むためGit除外。公開要約をexact snapshotの代用にしない。

Phase 4 Searchの計算契約・ranking semanticsは変更しない。WebはRun ManifestとSearch v0.1/v0.2を含む7schemaのoffline Ajv registryで
JSON syntax / UTF-8 / viewer resource / Schemaを確認し、Python semantic validationを再実行しない。
viewer上限8 MiBはVIEWER_LIMITとしてSchema INVALIDと分離する。入力はbrowser memoryのみ、Clearで破棄する。
summary、ranking/rejection、review warning、zero accepted、rank/reference選択、exterior ringの2D Local XY SVGをread-only表示する。
順位はGFA比較だけで設計品質・推奨・最適性・法規適合を意味しない。詳細: docs/web-results-contract.md。
Vercel D02はOPEN / PLATFORM_BLOCKEDを維持する。

Phase 7のconstraintContextはPython exportがcanonical Constraint Resultへ照合する。
Webはarea basis・cap・actualと、cap-actual / actual/capの表示値だけを扱う。clamp、再sort、
authoritative tie判定、governing/legal判定は禁止。明示localeで丸め表示し、入力を変更しない。
D04 OPEN、VMVP-001 PASS WITH TARGET ANOMALYを継承。Phase 6 private workspaceや詳細reportは読まない。

Phase 8はdocs/run-package-contract.mdを参照。入力はpublic syntheticだけで検証し、新dependencyは追加しない。
manifestは固定相対pathとexact artifact hashのみ。原本名・絶対path・wall-clockを含めない。
existing outputは上書きせず、stagingの完全verify後に排他的atomic publishする。runtime packageはGit/CI artifactに入れない。

Phase 9ではexact file setと同一root直下、全File.size先行確認、actual-buffer recheckを必須とする。
manifest/project 256 KiB、geometry/constraints 4 MiB、Search 8 MiB。raw parse前preflightは維持する。
Web Crypto SHA-256はartifact integrityのみ。root参照とbasis/階高のparsed値/順序を照合する。
Python bve.run verifyがauthoritative semantic verifier。package内Searchはv0.2、直接v0.1/v0.2は維持。
Clearで全state/inputを解除し遅延handoffを防ぐ。ZIP、network/storage、FS write、新dependencyは追加しない。
