# SDG Run Package v0.1

Phase 8はlocal orchestration / packagingだけを追加する。Geometry / Constraints / Massing / Searchの
計算・単位・status・ranking・rejection契約は変更しない。追加dependencyなし。Webから実行しない。

## CLIと構造

`python -m bve.run create`は`--project`、`--geometry`、`--format geojson|dxf`、
`--area-basis declared_project_area|geometry_area`、1件以上の`--floor-height-m`、`--output`を必須とする。
階高は既存`canonical_heights`を通るSearch engineが検証・昇順化し、数値的duplicateを拒否する。
DXFの`--layer`と`--unit m|mm`は既存Geometry contractへそのまま渡す。GeoJSONには指定できない。
出力親は既存directoryでなければならない。入力はregular fileのみ。

```text
SDG_Run/
  manifest.json
  project.json
  site.geojson
  constraints.json
  search-result.json
```

v0.1はstrict fixed file set。追加file/directory、OSの隠しmetadata、missing、symlink、Windows reparse pointを拒否する。
artifact数は4（manifestは別）。manifestの自己hashは持たない。CSV、個別candidate、画像、report、DXF出力はない。
canonical packageを圧縮・uploadする機構やWeb直接読込UIは追加しない。

## Canonical bytesと参照

| File | 正本 |
| --- | --- |
| project.json | shared Project schemaで検証後、既存Decimal encoderを公開する`project_bytes`でcanonical化 |
| site.geojson | Geometry Coreの`json_bytes(normalized_feature(site))` |
| constraints.json | `result_bytes` |
| search-result.json | `search_bytes`、v0.2 |
| manifest.json | closed schema `urn:sdg:run-manifest:0.1`、既存Decimal encoder |

Project canonicalizationは全field/statusを保持する。元のpretty-print inputとhashが変わる場合があるため、
Constraints / Searchは**package内のcanonical Project bytes**へbindingする。手動pipeline照合でもまず同じ公開
`project_bytes`でProjectを確定し、そのfileを既存CLIの入力にする。既存CLIのhash計算は変更しない。

Geometry normalization後に既存normalized loaderへ渡し、後段は**package内のsite.geojson bytes**を参照する。
Geometry内のsourceReferenceは元のGeometry入力bytesのdigestであり、元ファイル名は含まない。
同形のGeoJSONとDXFでもsourceFormat/sourceReferenceが異なるため、normalized・後段bytesを同一とは扱わない。
形式ごとに既存CLIとのexact-byte一致を検証する。

同じcanonical Project、同じGeometry入力bytes、area basis、階高集合を同じ対応Core環境で処理すると、
出力directoryに依存しない5ファイルを生成する。時刻・hostname・user名・絶対パス・一時directory名は含めない。
別machineの浮動小数点/GEOS実装差まで無条件に保証しない。依存versionとCore semanticsが再現の前提。

## Verify

`python -m bve.run verify --package <directory>`は書込を行わない。

1. strict file set、package rootとartifactの通常file属性、size limitを確認。
2. manifest schema、canonical serialization、固定相対path、4 artifactのexact-byte SHA-256を確認。
3. Project schema、Geometry schema/Polygon/metrics、Constraint schema/semantic loaderとcanonical bytesを確認。
4. Constraintsのproject/geometry参照、Searchのproject/geometry/constraints参照をmanifestへ照合。
5. 明示basis/heightsを照合。packageのProject/Geometryから既存`compute_constraints`を呼び、canonical出力を比較。
6. Search v0.2 schemaを確認し、既存engineとsemantic exporterを再実行してexact bytesを比較。

serialized Search用のsemantic loaderは既存Coreにないため、6はreplayによる検証とする。
candidate cap/containment、partition、rank/hash、context、review、rejectionを別実装で計算しない。
元のGeometry入力fileはpackageに含まれないため、そのsourceReferenceが示す原本の真実性を再証明はしない。
hash整合性は署名・作成者認証ではない。accepted=0をSearch failureと混同しない。

読込はbounded。Project 256 KiB、Geometry/Constraints 4 MiBは既存limitを維持。
manifest 256 KiB、Search package reader 256 MiBを上限とし、超過は固定INPUT_TOO_LARGEで拒否する。
Webの8 MiB viewer limitとは別であり、すべての有効packageのWeb表示を保証する意味ではない。

## Atomic createとエラー

Project → Geometry → Constraints → Search → canonical bytes → manifestの順に既存APIを使う。
出力親内の所有一時directoryへ書き、完全verify後にfinalへrenameする。file単位の部分公開はしない。
existing output file/directory/symlinkはOUTPUT_EXISTS。公開直前の競合もnative no-replaceで拒否する。

Windowsは既存targetを拒否する`os.rename`、Linuxは`renameat2(RENAME_NOREPLACE)`を使用する。
Linuxで関数/kernel/filesystemが対応しない場合、および他OSではATOMIC_PUBLISH_UNAVAILABLE。
危険なreplaceへのfallbackはない。
根拠：[Python os.rename](https://docs.python.org/3/library/os.html#os.rename)、
[Linux rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html)。

catch可能な失敗では所有stagingだけをcleanupし、sourceや既存user dataを変更しない。
成功後のpackage内容と親directoryは利用者が保護する前提。信頼できる安定したlocal親directoryを使う。
hard process crash/停電によるstaging残留や永続化は保証しない。cleanup自体がOSから拒否された場合もFAILであり、成功と報告しない。

CLI成功はpackageVersion / artifacts / reviewRequired / evaluated / accepted / rejectedだけ。
失敗は`FAIL stage=<fixed stage> code=<fixed code>`。既存Core codeを保持し、入力全文・座標・名前・path・例外詳細を出さない。

## 検証・公開境界

integration sourceは`cases/example-urban-office/`だけ。package fixtureは追跡せず、test/CIのtemporary生成で
manual CLI exact-byte regressionと決定性を検証する。重複fixtureやruntime出力をpublicへ増やさないための選択。
CIはrunner tempへGeoJSON/DXF packageをcreate/verifyし、artifact uploadを行わない。
一般の入力・packageにはProject情報や形状が含まれるためprivate runtimeとして扱い、manifestだけが匿名でも公開許可を意味しない。

法規適合、設計品質、最適性、governing判定は追加しない。Vercel NOT TOUCHED。
SDG-VP-001 BLOCKED_EXTERNAL、D02 OPEN / PLATFORM_BLOCKED、VMVP-001 PASS WITH TARGET ANOMALY、D04 OPENを継承。
