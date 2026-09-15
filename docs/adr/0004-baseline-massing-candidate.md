# ADR 0004: convex homothetic baseline massing

Status: Accepted for Phase 3 implementation; independent review pending.

Phase 2のcapとPhase 1のGeometryを1つの再現可能なconceptual candidateへ接続する。
凸・穴なしに限定すれば、内点centroid中心の一様縮小を検証可能な最初の方式にできる。
生成後の倍精度actual areaと包含を必ず検査し、厳密Decimal capの超過を許容しない。

固定strategyはmax_footprint_stack_v0.1、方式はconvex_homothetic_footprint_v0.1。
明示階高を使い、footprint優先の同形整数階stackを生成する。
複数案・検索・順位・最適化・3D mesh・法規後退・Web接続は後続Phaseまで実装しない。
既存schemaは改版せず、Candidate出力schemaのみ追加する。新dependencyは不要。

Constraint JSONはschemaだけを信用せず、Phase 2の同じ計算経路を使いprovenanceから再計算する。
全metadataとreviewRequiredを比較してからimmutable validated objectへ変換する。
Geometry hash一致を要求し、Constraint canonical bytesもhash化する。
これらは内部整合性と入力bindingを示し、元Projectの真正性や法規確認を証明しない。

Shapely精度によるcap超過は縮小方向ULP調整を最大64回まで認める。
任意epsilon・自動修復・actual area丸めは使わない。階数floorは明示Generator離散化である。
10,000階は資源上限としてrejectする。法規上限ではない。

SDG-VP-001は2回の意図しないProduction分類後に両deployment削除、Git切断済み。
D02をOPEN / PLATFORM_BLOCKEDとして保持し、HumanがPhase 3例外遷移を承認した。
このPhaseでVercelを再試行せず、Draft PR作成直後に停止する。
