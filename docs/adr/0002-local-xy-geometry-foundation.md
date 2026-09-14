# ADR 0002: 明示local XYのGeometry基盤

- Status: Accepted for Phase 1 implementation; Draft PR / independent review pending
- Human authorization: LR-20260914-SDG-P1-001 revision 1
- Base: 8b673999118d7109c6530399e324c8fa324f83e1 (Phase 0 squash merge)

Shapelyを唯一の幾何計算Core、ezdxfをDXF parserとして採用します。GeometryはProject入力条件と
別契約です。Web、既存Python validation、Project Schemaは変更せず、独立CLIで検証します。

単位だけから座標系を推測しないため、GeoJSON形状の入力にlocal_xy宣言を要求します。
DXFは地理参照のないmodelspace XYのみ。mm→m以外の投影・変換は今回行いません。
未対応曲線、曖昧な候補、invalid Polygonはrejectし、最大面積推測や自動修復を排除します。

この狭い契約で敷地Polygonを安全にBVEへ入れることを優先します。一般CAD/GIS framework、
法規、massing、保存機構、Bridge、Web compute APIは後続のHuman Gateです。
ADR 0001とPhase 0 Run記録は当時の判断として保持します。
