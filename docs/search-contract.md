# Phase 4 Search & Ranking contract

Current Phase = Phase 4 Search & Ranking Foundation。
探索軸はfloorHeightMだけ。Humanが明示した有限値を逐次評価する。
`floor_height_sweep_v0.1`は各値についてPhase 3の
`max_footprint_stack_v0.1` / `convex_homothetic_footprint_v0.1`を一度呼ぶ。
footprint探索、default grid、範囲の自動拡張、optimizer、並列pool、cacheはない。

## 入力

`search_massing_candidates(site_geometry, constraint_result, *, floor_heights_m=None)`。
GeometryとConstraintsは既存readerのvalidated objectが必須。raw dictは拒否する。
floor_heights_mはlistまたはtupleで1..64個。None/空はSEARCH_SPACE_REQUIRED、
65個以上はSEARCH_SPACE_TOO_LARGE。切り捨てない。その他のcontainerはINVALID_ARGUMENTS。
各値はPhase 3のpublic `parse_floor_height`で検証する。str/int/float/Decimal、
有限・正・m・user_provided。bool、単位suffix、非数値等は既存Phase 3 errorになる。
数値同値の重複はDUPLICATE_SEARCH_VALUE。silent dedupしない。
Decimalの数値昇順で評価・出力し、順序や等価な数値表記でbytesを変えない。

## 評価と順位

共有入力の検証はpoint rejectionの外で行う。各Generator呼出しの
NO_FEASIBLE_MASSING / RESOURCE_LIMITだけをpoint rejectionにできる。
geometry不正、参照不一致、利用不能constraint、生成失敗、schema/I/O失敗等はSearch全体FAIL。
accepted=0でも正常なSearch Resultであり、hasFeasibleCandidate=false、rankedCandidates=[]。
reviewRequiredは共有Constraintから正確に継承し、降格しない。

唯一のrankingは `maximize_gross_floor_area_v0.1`：GFA降順、階高昇順、candidateReference辞書昇順。
階高/hashのtie-breakは決定論的serializationのためだけで、design preferenceではない。
rankはacceptedの1..N。rejectionにはrankを付けない。
GFAはPhase 3のactual footprint面積から求めたmetricをそのまま使う。
Rank 1はこの指標における順位だけで、最良案・推奨案・最適案、設計品質・経済価値・法的優位を意味しない。
weighted score、AI ranking、実法規、後退・斜線、Web/3D/保存基盤は対象外。

## 出力と意味検証

Search schemaは既存4schemaをoffline $refで再利用する。
candidateReferenceはPhase 3 `candidate_bytes`全体（terminal LFを含む）のSHA-256。
同一referenceの二重生成はDUPLICATE_CANDIDATE。外部candidate collection readerはない。
exportはcanonical heights、exact-once accepted/rejected partition、summary counts、
hash、metric、共有input binding、Phase 3全cap/包含、review、連続rankと順位を再検証する。
内部Search modelはGeneratorが渡した共有入力objectを保持する。別入力への差替えを拒否する。
JSONは既存Decimal encoderのsorted keys、座標順維持、LF終端。rejectionも数値昇順。

## CLI

事前にGit除外runtime-dataディレクトリとPhase 1/2出力を用意し、新しいファイル名を指定する。

```sh
python -m bve.search --geometry runtime-data/normalized-site.geojson --constraints runtime-data/constraints.json --floor-height-m 4 --floor-height-m 5 --floor-height-m 6 --floor-height-m 7 --floor-height-m 8 --output runtime-data/search.json
```

output省略時は検証とsummaryだけ。明示outputはexclusive new fileで既存file・symlinkを上書きせず、mkdirしない。
OS fault時の部分新規fileは既知limit。CLIは固定FAIL codeまたは
`PASS evaluated=N accepted=N rejected=N reviewRequired=true|false`だけを表示する。
PASSはSearch実行成功であり、建築可能性・法規適合・feasible projectの証明ではない。
path、filename、座標、入力値、raw exception、JSONは表示しない。

synthetic [4,5,6,7,8]は5acceptedでGFA [1120,960,800,640,480]。
[4,32]は1accepted/1rejected、[32,40]は0accepted/2rejected。
これらは既存の匿名synthetic条件の結果で、実案件データではない。

Vercelは操作しない。SDG-VP-001 BLOCKED_EXTERNAL、D02 OPEN / PLATFORM_BLOCKEDを継続する。

Phase 5 Web Results Viewerはこのcanonical出力をbrowser-onlyでconsumeする。
authoritative semantic validationは引き続きPython exportの責務であり、Webは再実行しない。
