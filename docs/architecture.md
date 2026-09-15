# アーキテクチャ

Current Phase = Phase 5 Web Results Viewer Foundation。WebとPythonは同じcanonical schemasを参照する
独立したclientです。PythonのGeometry/Constraints/Massing/SearchとWebはAPIで接続しません。

```text
生成用プロンプト → ユーザーがコピー
合成サンプル / ローカル JSON → Web のメモリ → 構文検証 → Schema 検証 → 出典状態表示
ローカル JSON               → Python CLI  → 構文検証 → Schema 検証
                                           ↑
                     schemas/sdg-project-v0.1.schema.json
```

## 責務と依存

| 要素 | 責務 |
| --- | --- |
| `apps/web` | Next.js / TypeScript の画面とブラウザ内検証。入力を送信・保存しない |
| `schemas/sdg-project-v0.1.schema.json` | 型・必須項目・列挙値の唯一の正本 |
| Python `bve` モジュール | import 可能な検証コアと CLI。Web へ依存しない |
| `cases/example-urban-office/project.json` | 匿名の合成 fixture。Core に例外分岐を持ち込まない |
| root npm workspace | Web の依存関係・起動・lint・test・build をまとめる |

Web 用に Schema の別定義を作りません。Python も同じ正本を読み込みます。画面用の型や状態は契約へのアクセスを補助するもので、独立した仕様にはしません。

## 構造と出典を別に判定する

JSON 構文または Schema が不正なら UI は `INVALID` です。Schema に適合していても `assumed`、`unknown`、`review_required` があれば `REVIEW_REQUIRED`、それ以外は `VALID` です。

Schema 適合は値の真偽・法規適合・物理的妥当性を意味しません。出典状態は入力の申告であり、検証処理が公式確認を行うことも、LLM の結果を公式情報へ昇格させることもありません。単位は Schema の契約に従い、暗黙の単位変換や座標変換は行いません。

## Phase 1 Geometry

```text
local XY GeoJSON / DXF → bve.geometry reader → 単位・形式確認
  → Shapely Polygon検証 → SiteGeometry (2D XY / m) → 明示出力先のGeoJSON / summary
```

`bve.geometry` は既存 `bve.validation` と独立した読込・正規化・検証・export・CLIです。
別の `sdg-site-geometry-v0.1.schema.json` はGeometry出力構造だけを定義し、Project Schemaは変更しません。
Shapely 2.1.2を唯一の幾何計算Core、ezdxf 1.4.4をDXF parserとして直接依存に追加します。
NumPyは両packageの必須推移依存として入りますが、BVEは直接依存・計算実装に使いません。
pyproj等の投影機構は追加しません。単位スケール以外の座標変換・移動はありません。
詳細は [Geometry契約](geometry-contract.md) と [ADR 0002](adr/0002-local-xy-geometry-foundation.md) を参照してください。

## 将来拡張と過去の判断

Phase 2は次の独立データフローを追加します。

```text
Project exact bytes → shared Project schema → immutable numeric conditions + SHA-256
Normalized Geometry exact bytes → Geometry schema/Core再検証 → SiteGeometry + SHA-256
  + 明示area basis → 固定Decimal計算 → traced ConstraintResult → 明示新規JSON出力
```

`bve.geometry.load_normalized_geometry`がPolygon・再計算面積/boundsの検証を担い、
Constraint側へ同じ検証を複製しません。`bve.constraints`はarea比較、3上限、個別state、
provenance/reviewRequiredを保持します。Project/Geometry schemaは維持し、出力にだけ
`sdg-constraint-result-v0.1.schema.json`を追加。Project条件/statusの参照はoffline registryに限定します。
JSON数値のDecimal読込・厳密境界とschema参照だけを小さな共通helperで共有します。
詳細は[Constraint契約](constraint-contract.md)と[ADR 0003](adr/0003-constraint-engine-foundation.md)。

将来のPython computeは独立サービスへ移せる境界とします。Run Packageは、その計算結果と
CAD/BIM Bridgeの間で入力版・入力参照・成果物・検証記録を受け渡す契約候補です。
Phase 0ではサービスもBridgeも接続しません。

将来の Run Package は、入力契約の版、入力への参照、成果物、検証記録を結ぶ文書上の契約検討に留めます。Phase 0 では Run Package 用の Schema、実行機構、ストレージ、API を実装しません。現在の SDG Project Schema を複製・拡張する先行実装も行いません。

Phase 0では幾何計算・DXF読込も対象外でした。過去のADRとRun記録は当時の判断として保持します。
現在も法規計算、自治体固有処理、実案件固有処理、DXF / PDF出力、CAD/BIM連携、Web compute接続は対象外です。
WebのDXF / PDF画面要素は無効のままです。Draft PR作成後STOPし、Ready、merge、Vercel操作、Production、Phase 6、
Vault/Notion直接更新は行いません。

## Phase 3 Massing

```text
Normalized Geometry → Geometry再検証 + exact bytes hash
Constraint Result → schema + Phase 2計算経路で再計算 → immutable validated result + canonical hash
  → Geometry hash/area/status binding + explicit floor height
  → convex homothetic footprint → integer floor stack → all caps/containment検証
  → 1 conceptual candidate → 明示新規JSON出力
```

既存3schemaは維持しCandidate schemaを追加。Phase 1のnormalize/orientとPhase 2の計算・Decimal encoderを共有する。
floorはGeneratorの整数階離散化。Phase 3は法規丸め・後退・3D・探索・ランキング・Web接続を持たない。
詳細は[Massing契約](massing-contract.md)と[ADR 0004](adr/0004-baseline-massing-candidate.md)。

旧Preview必須GateはSDG-VP-001 BLOCKED_EXTERNAL、D02 OPEN / PLATFORM_BLOCKED。
Previewを意図した2経路がProduction分類され両deployment削除済み。直前closureでGit切断とdeployment/domain0を確認。
HumanのPhase 3 transition exception = AUTHORIZED。Phase 3ではVercel操作・再試行をしない。

[公開・非公開データの境界](public-private-data-boundary.md) と [採用判断の ADR](adr/0001-monorepo-and-contract-boundary.md) を併せて参照してください。

## Phase 4 Search

Validated Geometry + Constraints + explicit floor heights → serial Phase 3 calls → accepted/rejected partition
→ GFA order → semantic checks → explicit Search JSON。

Phase 4 SearchはfloorHeightだけを探索し、Human明示値1..64件を使う。default gridなし、duplicate拒否。
Phase 3 Generatorを逐次再利用し、GFA降順だけでrankingする。rankingはdesign qualityではない。
tie-breakは階高昇順/hash昇順でserialization用。footprint探索・optimizer・実法規・weighted scoreはない。
Search schema、exact candidate hash、partition/rank/summary/reviewのsemantic再検証を追加する。
Vercel D02はOPEN / PLATFORM_BLOCKEDを維持する。詳細: docs/search-contract.md。

## Phase 5 Web Results Viewer

```text
Python BVE Core → explicit local Search Result JSON → browser-only viewer
```

Web is not compute runtime. Project検証UIを維持し、Search Resultではsyntax / UTF-8 / viewer resource /
5つのcanonical schemaだけをbrowser内で確認する。8 MiB超はVIEWER_LIMITでありSchema INVALIDではない。
Pythonのarithmetic、geometry/cap、candidateReference、input binding、ranking semantic validationを再実装しない。

表示はsummary、既存rank/rejection、review state、zero accepted、rank/reference選択とexterior ringの2D Local XY SVG。
入力はReact stateだけに保持しClearで破棄する。API、upload、persistence、telemetry、編集、download、3Dはない。
public sampleはcanonical Python bytesを追跡しexact-byte testでbindingする。詳細: docs/web-results-contract.md。
