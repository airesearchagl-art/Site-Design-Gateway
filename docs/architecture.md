# Phase 0 アーキテクチャ

Web と Python は、同じ SDG Project JSON Schema を使う独立した検証クライアントです。Phase 0 では両者を API で接続しません。

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

## 将来拡張の境界

将来の Run Package は、入力契約の版、入力への参照、成果物、検証記録を結ぶ文書上の契約検討に留めます。Phase 0 では Run Package 用の Schema、実行機構、ストレージ、API を実装しません。現在の SDG Project Schema を複製・拡張する先行実装も行いません。

幾何計算、法規計算、自治体固有処理、実案件固有処理、DXF / PDF 出力、CAD/BIM 連携は Phase 0 の Core に入りません。DXF / PDF の画面要素は無効です。拡張は独立レビューと人の承認後、次の Phase で扱います。

[公開・非公開データの境界](public-private-data-boundary.md) と [採用判断の ADR](adr/0001-monorepo-and-contract-boundary.md) を併せて参照してください。
