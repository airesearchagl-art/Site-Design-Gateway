# Constraint Result v0.1

Current Phase = Phase 2 Constraint Engine Foundation。入力済みの面積・BCR・FAR・heightを
決定論的に変換する独立Python API/CLI。法規確認、行政確認、建築可能性証明ではない。
Project/Geometry v0.1を改版せず、出力だけを`sdg-constraint-result-v0.1.schema.json`で定義する。

## 入力とarea basis

`load_project(bytes | str)`は正本Project Schemaをoffline参照し、数値tokenをDecimalで検証する。
返すValidatedProjectはimmutableで、計算に必要な4条件とexact入力hashだけを保持する。
案件名・id・任意metadata・入力全文はConstraint Resultにコピーしない。

`load_normalized_geometry(bytes | str)`はGeometry packageの再利用API。既存Geometry schema、
有限XY、ring closure、Shapely validityを検査し、Polygonから面積・boundsを再計算する。
encoded ring順序の再計算値をPython floatの最短decimal表現にし、metadataと完全一致を要求する。
epsilon、snap、修復は使わない。sourceStatus/sourceUnit等の申告を保持し、source_referenceは
今回読んだnormalized JSONのexact bytesのhashとする。metadata内の旧sourceReferenceを入力hashとして信用しない。

`compute_constraints(validated_project, site_geometry, *, area_basis=...)`は次を必須とする。

- `declared_project_area`: Projectのsite.area。nullならAREA_BASIS_UNAVAILABLE。
- `geometry_area`: 検証済みPolygonの再計算面積。
- 未指定はAREA_BASIS_REQUIRED、不正値はINVALID_AREA_BASIS。既定値・自動選択なし。

`areaBasis`はselectedBasis、declaredAreaM2、geometryAreaM2、differenceM2、basisAreaM2、
両面積のprovenanceを保持。differenceM2は**declared−geometry**。宣言面積nullなら差もnull。
差分は証跡だけで、任意の許容差・合否・review閾値を追加しない。

## 3つの固定計算

| Constraint | Calculation identifier | 計算 |
| --- | --- | --- |
| buildingCoverage | coverage_area_cap_v0.1 | area basis × BCR / 100 → maxFootprintAreaM2 |
| floorAreaRatio | floor_area_cap_v0.1 | area basis × FAR / 100 → maxTotalFloorAreaM2 |
| height | height_cap_v0.1 | heightLimit → maxHeightM |

各Constraintはstate、calculationId、derived value、入力provenance、reviewRequiredを持つ。
BCR/FAR provenanceは選択areaとratioの順、heightはheightLimitだけ。入力field、exact hash、
value/unit/statusを追跡し、申告statusを統合・昇格しない。出典statusと条件定義はProject Schemaを参照する。

- COMPUTED: 利用可能な入力から計算。BCR/FARの0は0を計算する。
- UNAVAILABLE: 条件valueがnull。derived valueもnull、存在する入力provenanceを保持。
- ABSENT: optional heightLimitが存在しない。maxHeightM=null、provenanceは空。
- BCR/FAR自体の欠落はProject schema不適合。選択area不能以外の個別nullはEngineを停止しない。

assumed / unknown / review_requiredを含む入力はreviewRequired=true。
各Constraintではその入力だけを集計し、結果全体では両面積の比較入力も含めて集計する。
未選択areaの要確認statusも全体から消さない。llm_researchedはそのまま保持し、自動公式確認しない。
reviewRequired=falseも法規確認済みを意味しない。

## 数値と決定性

Project値はJSON decimal tokenをそのまま保持。Geometry値はPhase 1のShapely倍精度結果を
`Decimal(str(value))`へ変換する。Geometryの測量精度を増やす主張ではない。
計算には独立Decimal Contextを使い、Inexactをtrapする。ambient precision/roundingに依存せず、
任意丸め・floor/ceil・推測した端数処理を行わない。

資源上限として入力数値は係数1024桁、指数の絶対値1024まで。超過はNUMERIC_RANGE。
Project最大256 KiB、normalized Geometry最大4 MiB、JSON depth32。非有限値・重複key・BOM・
壊れたUTF-8・孤立surrogateは拒否する。Geometryの既存100,000 positions制限も維持する。
これらは実行資源制限であり、法規・敷地面積の業務閾値ではない。

出力はDecimalをfloatに戻さずJSON numberとして書く。キーをsort、配列順を固定、
空白なし、末尾LF。不要な小数末尾0と負の0は表記だけ正規化し、数値を丸めない。
同じ入力bytes/area basis/依存版なら結果bytes・summary・hash・orderingが一致する。
精度を保持する消費側もJSON numberをDecimalとして読む。floatへの変換・丸めは別契約とする。
inputReferences.project/geometryは`sha256:<64 lowercase hex>`。path/filename/URLを使わない。

## CLIとexport

```sh
python -m bve.constraints --project cases/example-urban-office/project.json --geometry runtime-data/site.geojson --area-basis declared_project_area --output runtime-data/constraints.json
```

Geometry CLIでnormalized出力を先に作成する。--outputは任意で、省略時は検証・計算と件数のみ。
指定先は新規ファイルへ排他的書込。親directoryは利用者が作成し、上書き・暗黙mkdirはしない。
OS書込障害時に部分出力が残る可能性があり、その場合はIO_ERRORで停止する。
出力もruntimeでありGitへ追加しない。Constraint Result JSONは出力schemaで検証する。

成功はPASS、reviewRequiredとcomputed/unavailable/absent件数のみ。失敗はFAIL code=固定値。
stdout/stderrへ値・座標・入力引数・例外・pathを出さない。exit 0=成功、1=入力reject、2=引数/I/O/内部障害。
JSON/schema/Geometry/数値/area basisの拒否は固定codeで区別する。

Python APIの最小例:

```python
from pathlib import Path
from bve.geometry import load_normalized_geometry
from bve.constraints import load_project, compute_constraints
from bve.constraints.export import result_bytes

project = load_project(Path("cases/example-urban-office/project.json").read_bytes())
site = load_normalized_geometry(Path("runtime-data/normalized-site.geojson").read_bytes())
result = compute_constraints(project, site, area_basis="geometry_area")
output_bytes = result_bytes(result)
```

Python APIはValidatedProjectと検証済みSiteGeometryを受ける。geometry input referenceは
渡されたSiteGeometryを作ったreaderのsource_referenceを使う。Phase 2のファイル消費経路は
必ずload_normalized_geometryを使い、normalized JSONのexact bytesを参照する。

Web接続、formula DSL、自治体rulepack、形状生成は範囲外。既存Web/Geometry検証を維持する。
Vercel deployはこのRunでは行わない。
Next Gate: **Vercel Preview Smoke — REQUIRED BEFORE PHASE 3**（Phase 2 merge後の別Run）。
