# 公開・非公開データの境界

このリポジトリは、公開可能なコード・契約・匿名の合成データを管理します。実案件の入力や運用記録を保管する場所ではありません。

| 対象 | 扱い |
| --- | --- |
| ソースコード、Schema、設計文書、匿名の合成 fixture | 公開 Git へ含められる |
| CI の入力 | 合成 fixture のみ |
| CI・検証ログ | 判定と必要最小限のエラー位置。入力全文や入力値を出力しない |
| 実案件データ、図面、住所、地番、個人情報、個人を識別できるパス | 公開 Git・CI・プレビューへ含めない |
| 認証情報、`.env`、署名付き URL、実行時 dump | 公開 Git・ログへ含めない |
| `.env.example` | 変数不要の説明コメントのみ。値を追加しない |
| ローカル Run 記録 | 公開適性を確認した要約のみ共有可能。元の指示書・添付・非公開パスは共有しない |

## Web の境界

JSON ファイルはブラウザ内で parse / validate し、結果をメモリ上で表示します。入力 JSON、ファイル内容、出典情報をサーバー、分析基盤、ストレージ、ログへ送信しません。永続化、アップロード API、Python 呼出、外部 LLM 呼出はありません。生成用プロンプトのコピー後、外部サービスへ渡す内容は人が確認します。

公開プレビューの確認には合成データのみを使います。ローカル処理という説明は、実案件データの公開利用を許可するものではありません。

## Python と開発運用の境界

CLI はローカルファイルを検証します。案件名や入力全文をテスト出力、例外、CI ログ、スクリーンショットへ残さず、エラー位置と判定だけを扱います。サンプルや特定自治体への例外分岐は Core に追加しません。

ignore 設定だけで公開可否を判断せず、コミット前に対象ファイルと差分を確認します。秘密情報・個人情報・入力全文の混入、データ破損が見つかった場合は共有を止めて報告します。認証や権限の変更、非公開情報の別経路への移送で解消しません。

Current Phase = Phase 11 Explicit Height Cap Stack / Effective Height Foundation。Vault / Notion への書込は禁止です。
公開 Git への反映は feature branch と Draft PR まで。Draft作成後STOPし、Ready、merge、
Vercel操作、Production、Phase 12には進みません。最終報告にDocumentation Sync Triggerを返します。

Geometry fixtureはゼロから作った `cases/example-urban-office/site.geojson` と `site.dxf`
だけを許可します。一般のDXF/GeoJSON原本・出力は公開しません。Python CLIの出力先は明示し、
通常はGit除外の `runtime-data/` を使います。source_referenceは入力bytesのSHA-256とし、
ファイル名、絶対パス、レイヤ名、任意の入力propertiesを出力へコピーしません。
エラーは固定codeのみ。ezdxfの診断ログと例外内容も公開しません。

Constraint Resultも明示したruntime出力のみ。Project名/id、private filename/path、入力全文、
座標列を複製せず、固定field名・数値条件・申告status・exact bytes SHA-256だけを保持します。
CLIはreviewRequiredと件数、または固定failure codeだけを表示します。追加fixtureはtest内/temporaryのsyntheticのみ。
Massing outputもruntimeでありGitへ追加しない。形状・階高・capは明示fileだけに出力し、
CLIにはfloors/reviewRequiredまたは固定codeだけを表示する。4mのsynthetic階高は架空設計値。
旧Preview必須GateはSDG-VP-001 BLOCKED_EXTERNAL / D02 OPEN・PLATFORM_BLOCKEDとして保持する。
2件の意図しないProduction分類は両方削除、Git切断後にHumanのPhase 3例外遷移が承認された。
Phase 4ではVercelを操作しない。認証・権限変更やNotion/Vault更新を行わない。
Search Resultもruntime出力でGitへ追加しない。4/5/6/7/8mは匿名syntheticの架空階高だけ。
CLIにはevaluated/accepted/rejected/reviewRequiredまたは固定codeだけを表示する。
candidate形状・hash・順位・rejection詳細は明示新規fileだけに出力し、CI artifactへ保存しない。

唯一の例外として `cases/example-urban-office/search-result.json` は、完全合成のcanonical contract fixtureとして追跡できる。
現在のPython CLI pipelineが生成するexact bytesとの一致をtestする。一般のprivate Search Result、
`runtime-data/*.json`、ブラウザ入力、file name/path、JSON全文、座標列をGit・CI artifact・log・screenshotへ含めない。
Phase 5 Webは入力をbrowser memoryだけで処理し、upload/API/fetch、localStorage、sessionStorage、IndexedDB、
Cache API、sendBeacon、analytics、telemetry、WebSocket、EventSourceを使わない。ClearはReact stateを破棄する。

Phase 7の公開Search fixtureは既存public synthetic CLIから再生成したv0.2だけ。
Phase 6 private workspaceのinput/output、詳細report、値、画像、パスをpublic code/docs/fixtureへ転記しない。
非ゼロarea difference等はtest内で完全syntheticに生成する。

Phase 8の一般Run Packageはprivate runtime。Project本文・形状を含むため、manifestがpathを持たなくても
公開可能とは扱わない。manifestには固定相対path、明示basis/heights、artifact hashだけを含める。
元ファイル名、source directory、個人path、時刻、machine/user名を追加しない。
testとCIはpublic synthetic sourceからtemporary packageを生成し、Gitへ追跡せずCI artifactへuploadしない。
検証CLIは固定stage/codeと件数だけを出す。Phase 6 private workspaceを参照・転用しない。

Phase 9のfolder/5-file選択もbrowser memoryだけで処理する。root pathやraw内容・例外を表示しない。
schema/hash/参照/設定の失敗は固定filename/code/一般説明のみ。Clearでstate/inputと遅延handoffを解除する。
Web Crypto SHA-256はlocal integrity確認のみ。network/storage、FS write、service worker persistenceを禁止する。
新たな検証packageはpublic syntheticから一時生成し、過去のprivate/runtime packageを取り込まない。

## Phase 10 FAR inputs

公開fixture追加は `cases/example-urban-office/project-far-stack.json` の完全syntheticのみ。
road_width_derivedは外部で与えられたnumeric capという分類であり、実道路幅員や法令係数を収録しない。
実FAR・用途地域・住所・案件名・原本/出典pathは持ち込まない。公開legacy project.jsonは維持する。
runtime package、browser証跡、mutation copy、exact task packetはGit除外のlocal evidenceとする。
公開Run記録には判定・件数・digestと相対source参照だけを記載する。Phase 6 private workspaceは読まない。

## Phase 11 height inputs

追加fixtureはexample-urban-office/project-height-stack.jsonの完全syntheticのみ。
既存project.json / project-far-stack.jsonは変更しない。31m/24mは架空値で法令・実案件値ではない。
実高さ・住所・高度地区・実CAD/PDF・Case001やprivate workspaceを参照しない。
元Project照合APIはcallerが渡した既存入力をmemoryで確認し、ConstraintへProject全文を複製しない。
Python/Webとも入力値や個人pathをlogに追加しない。runtime packagesと監査証跡はGit除外。
