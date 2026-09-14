# Site Design Gateway

CAD上で一案ずつ試す初期検討から、入力条件・制約・計算根拠・候補比較を明示した
再現可能な探索へ進めるWeb Gatewayです。計算主体はBVE Core（Buildable Volume Engine）です。

Current Phase = Phase 1 Geometry Foundation。共通JSON Schemaによる案件条件の検証を維持し、
Python BVE CoreにDXF / GeoJSONからの敷地Polygon読込・m正規化・検証を追加しています。
Webは従来のプロンプトコピー、合成サンプル・JSON読込、構文・Schema・出典状態確認を提供します。

## ローカルで開始する

前提: Node.js 22.18 以上、npm、Python 3.12 以上。以下はすべてリポジトリのルートで実行します。

```sh
npm install
npm run dev
```

起動ログに表示されるローカル URL を開き、「サンプルを読み込む」から動作を確認します。開発用の環境変数や API キーは不要です。

Python は仮想環境へインストールします。現在はsource/editable installを対象とし、
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

## Phase 1 Geometryの開始

上記editable installにはShapelyとezdxfが含まれます。仮想環境のPythonで実行します。

```sh
python -m bve.geometry cases/example-urban-office/site.geojson --format geojson
python -m bve.geometry cases/example-urban-office/site.dxf --format dxf --layer SITE
```

成功時は `PASS code=VALID warnings=0`。面積や座標を含む出力が必要な場合、Git除外の
`runtime-data` ディレクトリを作り、未使用の出力ファイル名を指定します。

```sh
python -m bve.geometry cases/example-urban-office/site.dxf --format dxf --layer SITE --output runtime-data/site.geojson --summary runtime-data/summary.json
```

入力はlocal XY / mまたはmmのみ。GeoJSONには `unit` と `coordinateSystem: "local_xy"` が必須です。
DXFはclosed LWPOLYLINE / 2D POLYLINEを対象とし、未知単位は明示 `--unit m|mm` が必要です。
地理座標、曲線、複数境界の推測選択、自己交差、自動修復は非対応。出力先の既存ファイルは上書きしません。
正規化出力は地理座標GeoJSONではありません。[入力契約・制限・エラー](docs/geometry-contract.md)を参照してください。
synthetic fixtureは両形式とも200 m2、面積差0です。WebにはGeometryを接続していません。

## Phase 0で作成した基盤

- Next.js / TypeScript の Web、プロンプトコピー、JSON 読込・検証、出典状態表示。
- JSON Schema v0.1、匿名の合成 fixture、BVE Core の import / 検証 CLI と最小テスト。
- README、開発指示、ignore 設定、空の環境変数サンプル、境界文書、ADR、合成データ専用 CI、再開用 Run 記録。
- DXF / PDF は無効なプレースホルダーのみ。成果物は Draft PR まで。

Phase 1の追加範囲はPython Geometry Foundationです。マッシング、検索、法規エンジン、認証、
保存・DB、CAD/BIM連携、最適化、Web compute APIは範囲外です。Run Packageは文書上の契約検討に留めます。

Phase 0は独立レビューとHuman承認後にmerge済みです。今回の出口はPhase 1のDraft PRです。
作成直後にSTOPし、Ready、merge、production、Phase 2へ進みません。過去のADR・Run記録は維持します。

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
- [Geometry契約とCLI](docs/geometry-contract.md)
- [ADR: local XY Geometry基盤](docs/adr/0002-local-xy-geometry-foundation.md)
