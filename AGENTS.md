# Repository rules

- このRepositoryはPublic。source、schema、匿名synthetic fixture、テスト、文書だけを保存する。
- 実案件データ、実案件名・住所、施主情報、個人を識別するローカルパス、秘密情報、
  .envの値、署名付きURL、CAD/BIM/PDF原本、runtime input/log/dumpをGitへ入れない。
- fixtureは `cases/example-urban-office/` のsynthetic dataのみ。
- `schemas/sdg-project-v0.1.schema.json` が案件条件の正本。Web/Pythonで別schemaを作らない。
- BVE Coreに案件・自治体固有処理を埋め込まない。LLM調査値をofficial_verifiedへ昇格しない。
- Current Phase = Phase 4 Search & Ranking Foundation。検証済みGeometry/Constraint ResultとHuman明示階高集合から、
  Phase 3 Generatorを逐次実行し、GFA降順でconceptual candidatesを並べる。
- Project/Geometry/Constraint/Massing schemaは維持。floorHeight以外の探索・最適化・法規後退・3D・認証・DB・Bridge・Web compute接続は対象外。
- mainへ直接commitしない。作業branchでcheckpoint commitを残す。force push、破壊的cleanupは禁止。
- このCampaignではReady、merge、Vercel操作、Production、Phase 5開始は禁止。Draft PR作成直後にSTOP。
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

Phase 4 SearchはfloorHeightだけを探索し、Human明示値1..64件を使う。default gridなし、duplicate拒否。
Phase 3 Generatorを逐次再利用し、GFA降順だけでrankingする。rankingはdesign qualityではない。
tie-breakは階高昇順/hash昇順でserialization用。footprint探索・optimizer・実法規・weighted scoreはない。
Search schema、exact candidate hash、partition/rank/summary/reviewのsemantic再検証を追加する。
Vercel D02はOPEN / PLATFORM_BLOCKEDを維持する。詳細: docs/search-contract.md。
