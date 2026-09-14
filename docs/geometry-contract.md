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

詳細CLI操作・エラーcode・制限は実装後に本書へ追記します。Project Schemaや既存CLIは変更しません。
