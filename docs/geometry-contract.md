# Geometry v0.1 契約

`SiteGeometry` は検証済みShapely Polygon、area_m2、bounds、source_format、source_unit、
normalized_unit=m、source_status、source_reference、warningsを保持します。
面積とboundsはPolygonから導出し、別の入力値を信用しません。計算はShapelyのみです。

## 入力

- GeoJSON形状のFeature + Polygon、またはbare Polygon。Featureはproperties、bare Polygonは
  rootに `unit: "m" | "mm"` と `coordinateSystem: "local_xy"` を必須指定します。
  holesも閉じたringとして受け付け、Shapelyで位置・交差を検証します。
  `crs` 宣言はすべて非対応。Feature内geometryへの単位/座標系の重複指定も拒否します。
  EPSG:4326、緯度経度、投影座標、座標系不明は非対応で自動投影しません。
- DXFはmodelspaceのclosed LWPOLYLINE / 2D closed POLYLINE。対象layer内（未指定なら全体）の
  全polylineを候補とし、open/3Dも無視して候補を減らしません。候補が複数なら明示layer選択が必要。
  同layerに複数あれば引き続き拒否します。最大面積選択やblock展開はありません。
  `$INSUNITS` 6=m / 4=mm。unitless/unknown時のみ明示unit override可能。
  既知の別単位・矛盾するoverrideは拒否します。geodata付きDXFは非対応です。
  elevation=0、extrusion=(0,0,1)、厚み・幅=0のみ。曲線/bulge/fit情報、3D/meshは拒否します。

GeoJSONはRFC 7946互換の地理データを意味しません。ローカルXYを明示した独自契約です。
宣言の真偽・測量原点は自動確認できません。mへのスケール変換だけを行い、原点移動や丸めはしません。

## 検証と決定性

各ringは有限な数値2個のposition、3 distinct vertices以上、明示closureが必要です。
DXFだけはclosed flagから最後の直線edgeを形成します。重複した末尾closureを整理しますが、
交差・ゼロ面積・無効Polygonは修復しません。buffer(0)、snap、simplifyは使いません。
固定epsilonを面積判定に使わず、floatで表現できる有限の正面積を要件とします。
倍精度で失われる座標・mm変換で消える頂点や非有限面積は拒否します。
Shapely normalizeとring orientationで外周CCW/内周CWと安定した開始点・hole順序を出力します。
同じ入力bytesとオプションは同じJSON bytesを生成します（同じ依存版）。

## 出典と公開境界

GeoJSONのsourceStatusがあればProject契約の7状態を保持し、なければuser_providedです。
DXFはdrawing_derived、unit override使用時はuser_provided + UNIT_OVERRIDDENです。
状態をofficial_verifiedへ昇格しません。source_referenceは `sha256:` + 入力bytesのdigestのみ。
その他の入力properties、ファイル名、layer名、診断文や元の座標列をログへコピーしません。
正規化出力ファイルには座標が必要なため、明示指定したローカル出力先だけへ書きます。

## CLI

仮想環境を有効にしたリポジトリルートで実行します。既存 `python -m bve FILE` は変更しません。

```sh
python -m bve.geometry cases/example-urban-office/site.geojson --format geojson
python -m bve.geometry cases/example-urban-office/site.dxf --format dxf --layer SITE
```

`--output runtime-data/site.geojson` と `--summary runtime-data/summary.json` は任意です。
先に出力ディレクトリを作成してください。既存ファイル・入力ファイルは上書きしません。
2ファイルは個別書込で、OS障害時は一部が残る可能性があります。その場合はIO_ERRORで終了し、
PASSにはなりません。出力はGitへ自動追加しません。

GeoJSONはinput内の単位・座標系が必須です。`--unit m|mm` はDXFの未知単位にだけ使用でき、
既知単位に矛盾する指定はUNIT_CONFLICTになります。DXFのlayer名は大文字小文字を区別せず完全一致。
選択layerに候補が複数残る場合はAMBIGUOUS_BOUNDARYです。

stdoutは `PASS code=VALID warnings=N` または `FAIL code=固定コード` のみ。summary/座標は
明示出力ファイルで確認します。終了codeは0=成功、1=入力reject、2=引数/I/O/既存出力エラーです。
主なreject codeはUNIT_REQUIRED、UNSUPPORTED_UNIT、CRS_REQUIRED、UNSUPPORTED_CRS、
OPEN_BOUNDARY、AMBIGUOUS_BOUNDARY、UNSUPPORTED_CURVE、INVALID_POLYGON、ZERO_AREA、
NON_2D、NONFINITE_COORDINATES、NUMERIC_RANGEです。全codeは `geometry/errors.py` にあります。

## 実行制限

- 最大入力4 MiB、GeoJSON depth 32、全ring合計100,000 positions。倍精度範囲外はreject。
- DXFはUTF-8 text（ASCII含む）。binary、旧codepage、recover/auditによる修復は非対応。
- ezdxfが省略単位を既定値で補う前に原文headerを検査します。LWPOLYLINEのZ、非有限値、
  頂点数不整合・重複scalar・不正extrusionも、parserが捨てる前に検査します。
- 数値tokenをDecimalで保持してfloat化前の非零underflow、整数精度損失、座標衝突を拒否します。
  Decimalは読込境界だけで使用し、面積・validity・bounds計算はShapelyの倍精度です。
  DXFはsubclassの順序と個数、属性位置、読込前後のentity数も照合します。
  polyline/vertexのapplication-data group102、重複・矛盾subclassは非対応です。
  保守的にファイル内の全polyline/vertexを構造検査するため、未選択layer/blockに不正・非対応の
  情報があっても拒否する場合があります。LF / CRLF / CR改行は同じGeometryとして処理します。
  EOF以降の非空データも拒否します。subclass無しはR12のPOLYLINE/VERTEXだけを対象とします。
- ezdxf初回importは一時ディレクトリの空font cacheを使い、既存home cacheを作成・更新しません。
  設定はスコープ終了時に復元します。reader中の診断は保存せず捨て、固定codeで失敗を返します。
  この診断抑制はプロセス全体の標準stream/logに一時作用するため、Phase 1は同期CLIで使用します。
  同一プロセスで別threadのログ処理と並行運用するサービス接続は未対応です。
- JSON Schemaは出力構造の契約です。ring closure、finite、面積/bounds整合、幾何validityは
  Shapely Coreで検証します。sourceStatusは正本Project Schemaをoffline参照します。

参照: [Shapely normalize](https://shapely.readthedocs.io/en/stable/reference/shapely.normalize.html)、
[ring orientation](https://shapely.readthedocs.io/en/stable/reference/shapely.orient_polygons.html)、
[ezdxf units](https://ezdxf.readthedocs.io/en/stable/concepts/units.html)、
[LWPOLYLINE](https://ezdxf.readthedocs.io/en/stable/dxfentities/lwpolyline.html)、
[POLYLINE](https://ezdxf.readthedocs.io/en/stable/dxfentities/polyline.html)。
