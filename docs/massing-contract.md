# Massing Candidate v0.1

Current Phase = Phase 3 Massing Candidate Foundation。
本書はPhase 3時点の契約・Gateを保持する。Phase 4はconsumerとして再利用し、現行Searchは[Search契約](search-contract.md)を参照する。
成果は **constraint-bounded conceptual massing candidate** を1案だけ生成するPython基盤。
道路・壁面後退、斜線、日影、天空率、地区計画等は扱わず、法規適合・建築可能性・最適性を保証しない。

## 入力と信頼境界

`generate_massing_candidate(site_geometry, constraint_result, floor_height_m=...)` は
Phase 1 `SiteGeometry` と `load_constraint_result(bytes | str)` の検証済みobjectを要求する。
raw dictや未検証のConstraintResultは受け付けない。
Constraint readerは既存schemaをoffline検証し、provenanceをPhase 2と同じ計算経路で再計算する。
全state/value、固定calculation ID、参照、選択・非選択面積、差分、unit/status、reviewRequiredの一致を要求する。
内部整合性の検証であり、元Projectを渡さずにprovenance全体を整合的に書き換えた場合の真正性は証明できない。

Geometry参照は `constraint.inputReferences.geometry == site_geometry.source_reference` が必須。
同じ面積/boundsでもhashが異なれば `INPUT_REFERENCE_MISMATCH`。
Geometry provenanceの面積・statusも実際のSiteGeometryと比較する。
Project参照は継承、Geometry参照はnormalized入力exact bytes、Constraint参照は検証後canonical bytesのSHA-256。
pathやfilenameを参照へ入れない。SHA-256は署名や認証ではない。

Required statesはbuildingCoverage / floorAreaRatio / heightすべてCOMPUTED。
UNAVAILABLE / ABSENTは `REQUIRED_CONSTRAINT_UNAVAILABLE`。
階高は明示finite >0 meterの設計入力。未指定は `FLOOR_HEIGHT_REQUIRED`、不正は `INVALID_FLOOR_HEIGHT`。
statusは固定 `user_provided`。既定値・法規値への昇格・Project schema変更はない。
Python APIはstr/int/float/Decimalを受け、floatはstr経由でDecimal化する。boolは拒否。
数値文字列はASCII decimal/scientific表記のみ、係数1024桁・指数絶対値1024まで。空白・単位suffixは拒否する。

## 固定アルゴリズム

strategy `max_footprint_stack_v0.1`、footprintMethod `convex_homothetic_footprint_v0.1`。
local XY / mのvalid 2D convex Polygon・穴なしだけを扱う。
concave / holeは `UNSUPPORTED_MASSING_SITE_GEOMETRY`。MultiPolygon / 3D / curveも非対応で、
Geometry readerで先に拒否される入力はその固定codeを返す。凸包への置換や自動修復を行わない。

target = min(site area, maxFootprintAreaM2, maxTotalFloorAreaM2)。容量0以下は `NO_MASSING_CAPACITY`。
target >= site areaなら正規化敷地形状を使い、拡大しない。
それ以外はcentroid中心にX/Y同率でsqrt(target/site area)縮小する。法規のoffsetではない。
Phase 1 canonicalizationを使い、Shapely actual areaを `Decimal(str(area))` へ変換する。
cap超過をepsilonで認めず、scaleをnextafterで縮小する調整は最大64回。
解消しない超過、不正形状、敷地外は `GEOMETRY_GENERATION_FAILED`。

全階同一footprint。階数は min(floor(GFA cap / actual area), floor(height cap / floor height))。
商は整数比から厳密に切り捨て、法規の端数処理とは区別する。partial top floorなし。
1階未満は `NO_FEASIBLE_MASSING`。10,000階超はresource limitとしてrejectし、切り詰めない。
高さ・GFAは厳密Decimal乗算。最後にBCR/FAR/height capとsite.coversを再確認する。
reviewRequiredはConstraint Resultから継承し、trueをfalseへ降格しない。
footprint優先であり、FAR消化率最大化や複数候補探索を行わない。

## 出力と資源境界

正本出力schemaは `schemas/sdg-massing-candidate-v0.1.schema.json`。
Project/Geometry/Constraintの既存schemaは維持し、参照定義をoffline共有する。
数値はJSON number、key順・Polygon順・数値書式固定、末尾LF。
同じ入力と固定Shapely 2.1.2 / GEOSでbytes一致を検証する。異なる依存版間のbit一致は未保証。
Constraint readerは4 MiB / depth 32 / 数値係数8,192桁・指数絶対値8,192の上限。
Phase 2の派生値と固定小数表記を再読込するため、元Projectの字句上限とは別にする。
計算は既存8,192桁contextでInexact等を拒否。元Project/Geometry readerの上限は変更しない。

```sh
python -m bve.massing --geometry runtime-data/normalized-site.geojson --constraints runtime-data/constraints.json --floor-height-m 4 --output runtime-data/massing.json
```

親directoryは事前に明示作成。新規outputだけを排他作成し、既存・入力file・symlinkを上書きしない。
output省略時は検証とsummaryだけ。成功は `PASS floors=N reviewRequired=true|false`、
失敗は `FAIL code=<fixed code>`。座標・入力値全文・path・filename・raw exception/argsを表示しない。
Web接続、runtime upload、保存サービス、telemetry、新dependencyは追加しない。
OS書込障害時はIO_ERRORで停止し、部分fileが残る可能性がある。既存出力を再試行で上書きしない。

synthetic floorHeight=4は架空設計値。site200、target160、actual<=160、7階、28m、GFA約1120<=1200、
height<=31、敷地内、reviewRequired=trueを期待する。actualを160へ丸め直さない。

## Campaign境界

SDG-VP-001 = BLOCKED_EXTERNAL、D02 = OPEN / PLATFORM_BLOCKED。
Previewを意図した独立2経路がProduction分類され、両deploymentは削除済み。
直前のclosure確認はGit Integration DISCONNECTED、deployments0、latestDeployment null、live false、domains0。
HumanのPhase 3 transition exception = AUTHORIZED。このPhaseでVercelを操作・再検証しない。
Draft PR作成後STOP。Ready/merge/Phase 4/Productionは禁止。Documentation Sync Trigger = yes。

## Phase 12 supplied footprint domain

[Buildable Area契約](buildable-area-contract.md)が詳細正本。Project0.4 / Buildable Area Geometry0.1 /
Constraint0.4 / Massing Candidate0.2 / Search0.5 / Run Package0.4を明示dispatchする。
旧Package0.1〜0.3は固定5ファイル、0.4だけbuildable-area.geojsonを加えた固定6ファイル。
明示convex/no-hole polygonのsite完全包含、status一致、source/site/artifact hashを検証する。
BCR/FARは敷地面積基準のまま。scalar calculation IDs、legacy bytes、rankingは維持する。
既存homothetic shrinkをsupplied domainへ適用し、最終footprintはdomainとsiteの両方でcoversを要求。
後退・斜線・法規からgeometryを生成せず、修復も行わず、法規適合を主張しない。
Pythonがsemantic authority。Browserは21schema、hash/reference/statusと5/6-file matrixを確認し、
authoritative spatialContextの表示のみ。containmentを再計算しない。buildable上限4MiB、全file size先行、
actual buffer再確認、Clearの遅延handoff禁止、memory-only入力を維持。D04 OPEN。
Documentation Sync Trigger: yes — Phase 12 major spatial geometry / Massing domain contract。
