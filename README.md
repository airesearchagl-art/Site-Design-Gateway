# Site Design Gateway

CAD上で一案ずつ試す初期検討から、入力条件・制約・計算根拠・候補比較を明示した
再現可能な探索へ進めるWeb Gatewayです。計算主体はBVE Core（Buildable Volume Engine）です。

建築計画の入力 JSON を、共通の JSON Schema で確認する Phase 0 の開発基盤です。Web は生成用プロンプトのコピー、合成サンプルの読込、JSON ファイルの読込、構文・Schema・出典状態の確認を提供します。Python BVE Core は検証用の最小 CLI です。

## ローカルで開始する

前提: Node.js 22.18 以上、npm、Python 3.12 以上。以下はすべてリポジトリのルートで実行します。

```sh
npm install
npm run dev
```

起動ログに表示されるローカル URL を開き、「サンプルを読み込む」から動作を確認します。開発用の環境変数や API キーは不要です。

Python は仮想環境へインストールします。Phase 0はsource/editable installを対象とし、
正本Schemaを読むためリポジトリを保持してください。wheel単体での配布は対象外です。

```sh
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m bve cases/example-urban-office/project.json
```

macOS / Linux:

```sh
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/python -m bve cases/example-urban-office/project.json
```

## 確認・ビルド

```sh
npm run lint
npm test
npm run build
npm run check:boundary
```

仮想環境を有効にした場合、Python の確認は `python -m pytest`、CLI は `python -m bve cases/example-urban-office/project.json` でも実行できます。再現用の依存インストールにはルートで `npm ci` を使います。

CI は公開可能な合成データだけを使い、Web の lint・test・build と Python のテストを実行します。コマンドの掲載は成功記録ではありません。実行ごとの結果は CI と対応する Run 記録で確認してください。

## 検証結果の意味

Schema の正本は [`schemas/sdg-project-v0.1.schema.json`](schemas/sdg-project-v0.1.schema.json) です。Web と Python で同じファイルを参照し、仕様を二重管理しません。

| 判定 | 意味 |
| --- | --- |
| Schema `PASS` / `FAIL` | JSON が構造・型・列挙値の契約を満たすか |
| UI `INVALID` | JSON 構文エラー、または Schema 不適合 |
| UI `REVIEW_REQUIRED` | Schema 適合かつ `assumed` / `unknown` / `review_required` を含む |
| UI `VALID` | Schema 適合かつ上記の要確認状態を含まない |

出典状態は `official_verified`、`user_provided`、`drawing_derived`、`llm_researched`、`assumed`、`unknown`、`review_required` の 7 種です。`VALID` は法規適合や情報の正しさを保証しません。`llm_researched` を `official_verified` へ自動昇格させず、人が根拠を確認します。

選択した JSON はブラウザ内で処理します。Web から Python を呼び出さず、入力をサーバー・ストレージ・ログへ送信しません。公開リポジトリ、CI、レビュー用プレビューには合成データのみを使用してください。

## Phase 0 の範囲

- Next.js / TypeScript の Web、プロンプトコピー、JSON 読込・検証、出典状態表示。
- JSON Schema v0.1、匿名の合成 fixture、BVE Core の import / 検証 CLI と最小テスト。
- README、開発指示、ignore 設定、空の環境変数サンプル、境界文書、ADR、合成データ専用 CI、再開用 Run 記録。
- DXF / PDF は無効なプレースホルダーのみ。成果物は Draft PR まで。

幾何計算、DXF 読込、マッシング、検索、法規エンジン、認証、保存・DB、CAD/BIM 連携、最適化、デザインシステムは範囲外です。将来の Run Package は文書上の契約検討に留め、実装・保存・実行を追加しません。

Phase 0 完了後は停止します。独立レビューと人の承認を経るまで Ready、merge、production、Phase 1 へ進みません。

## Vercel のビルド構成

将来のレビュー用プレビューでは、次の設定を使用する想定です。この文書自体はデプロイを許可せず、実際の Vercel ビルド成功も示しません。

| 設定 | 値 |
| --- | --- |
| Root Directory | `apps/web` |
| Framework Preset | Next.js |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | `.next`（自動設定） |
| Include source files outside of the Root Directory | 有効（必須） |

Vercel 上の `npm run build` は Web workspace のスクリプトを実行します。`npm ci` はルートの workspace 定義と lockfile を参照します。Web はルートの `schemas` / `cases` を直接参照するため、Root Directory 外のソースを含める設定が必須です。Next.js の `turbopack.root` / `outputFileTracingRoot` もリポジトリのルートを指す構成です。設定の考え方は [Vercel のモノレポ設定](https://vercel.com/docs/monorepos) と [ビルド設定](https://vercel.com/docs/builds/configure-a-build) を参照してください。ホスト上のプレビュー検証は別途必要です。

## 設計文書

- [アーキテクチャ](docs/architecture.md)
- [公開・非公開データの境界](docs/public-private-data-boundary.md)
- [ADR: モノレポと共通契約](docs/adr/0001-monorepo-and-contract-boundary.md)
