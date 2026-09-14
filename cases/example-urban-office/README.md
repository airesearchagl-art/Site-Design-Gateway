# Example Urban Office

完全に合成した架空データ。実敷地・自治体・法規調査から転記していません。
面積200m2、高容積率、高さ31mの数値は将来の境界テストのための例示です。
Phase 0では形状・階数・ボリュームを定義しませんでした。Phase 1で匿名敷地Polygonを追加しました。

期待結果: Schema PASS / UI REVIEW_REQUIRED。
`llm_researched`も表示確認用の合成ラベルであり、実際の調査結果ではありません。
`assumed`、`unknown`、`review_required`の扱いは形式検証と別に判定します。

## Phase 1 synthetic geometry

`site.geojson` はlocal XY / m、`site.dxf` はmodelspace / mm、layer `SITE` のclosed LWPOLYLINEです。
両方とも原点から作った5頂点の架空Polygonで、面積200 m2、bounds [0, 0, 12, 20] mです。
実案件の形状をコピー・変形していません。GeoJSONのsourceStatusはassumed。
DXF readerのdrawing_derivedは形式からの導出を示すだけで、実在や公式確認を意味しません。

`python scripts/generate_synthetic_geometry.py` で、同じ頂点定数から両fixtureを再生成できます。
固定DXF metadataを使用し、ユーザー名・パス・実時刻を含めません。テストは再生成bytesとの一致、
Polygon同値、面積差0、出力schemaとCLI非開示を検証します。
