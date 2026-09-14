# ADR 0001: モノレポと共通契約の境界

状態: Phase 0 で採用

## 背景

Web の入力確認と Python の検証コアが異なる契約を持つと、片方だけで通る入力が生まれます。最初の段階では共通契約と再現可能な開発手順を固定し、計算・保存・外部連携を追加しません。

## 決定

- Web、Python、Schema、合成 fixture を同一リポジトリで管理する。
- Web は `apps/web` の Next.js / TypeScript とし、root npm workspace のコマンドで起動・検証・ビルドする。
- `schemas/sdg-project-v0.1.schema.json` を唯一の Schema 正本とし、両実装が参照する。
- Python BVE Core は import と検証 CLI に留め、Web から呼び出さない。
- Web の入力処理はブラウザ内で完結させ、サーバー送信・保存・入力のログ出力を実装しない。
- Schema の `PASS` / `FAIL` と UI の `VALID` / `INVALID` / `REVIEW_REQUIRED` を分ける。情報の信頼状態を自動昇格させない。

## 帰結

契約変更と両実装のテストを同じ変更としてレビューできます。CI は合成 fixture のみを使います。将来、案件や自治体ごとの条件を追加しても Core に例外分岐を埋め込まず、次の Phase の独立した契約検討に回します。

Web と Python の配備・依存環境は独立しています。共有 Schema の読込位置を維持し、ローカルテスト、Web build、ホスト上の Preview を別々に検証する必要があります。Schema 適合だけでは法規・単位・幾何の実務検証を代替しません。

Run Package、幾何計算、法規エンジン、認証、DB、CAD/BIM 連携は今回実装しません。Run Package は将来の文書上の契約検討に留めます。Phase 0 は Draft PR で停止し、Ready / merge / production / 次 Phase の開始には独立レビューと人の承認を要します。
