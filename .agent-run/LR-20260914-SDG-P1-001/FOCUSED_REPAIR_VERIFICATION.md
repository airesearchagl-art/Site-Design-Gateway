# PR #2 Required Fix — Focused Independent Verification

実装担当とは別Contextで差分レビューとfocused検証を実施した。
RF-01〜04はすべて **FIXED**。今回の4件に対応する未解決問題・regressionは検出されなかった。
この判定はIndependent FULL Re-Reviewの代用ではない。

## 検証対象の固定

- Run: LR-20260914-SDG-P1-001
- Task Packet: LRP-20260914-SDG-P1-001 / revision 1（変更なし）
- Exact packet SHA-256: `93fee6c5f33b17c412a3b2141a9ada385eded1dde3185f51e51565e21291efee` — 独立再計算MATCH
- Branch: `feat/phase1-geometry-foundation`
- Reviewed head: `03c9e775ee9828bddcb5d1daea630d153d32f55b`
- Base: `8b673999118d7109c6530399e324c8fa324f83e1`
- 検証時点のHEADとorigin featureはreviewed headと一致。origin/mainはbaseと一致。
- 対象は同じbranch上の未commit修復差分。実装・テストの内容は末尾のSHA-256で固定した。

## RF個別判定

| RF | 判定 | 独立に確認した根拠 |
| --- | --- | --- |
| RF-01 unsupported curve entity | FIXED | modelspaceの選択範囲にARC/CIRCLE/SPLINE/ELLIPSEがあればUNSUPPORTED_CURVE。curve単独と正常境界同居、明示layerと無指定を網羅。別layerのcurveは明示SITE選択で許容し、layer無指定では拒否。paperspace/block内のcurveは探索対象外。追加24テストが通過し、曲線guard無効化mutationで20テストが失敗。 |
| RF-02 raw SEQEND integrity | FIXED | raw group順序でPOLYLINE→VERTEX*→SEQENDを検証。欠落、orphan VERTEX/SEQEND、重複、中断、ネスト、同数でも順序不正のsequenceを拒否し、ezdxf.read未呼出をassert。R12/modern・LF/CRLF/CR、zero-vertex構造、LWPOLYLINE、INSERT属性の正常系を維持。追加16テストと独立追加42テストが通過。raw sequence guard除去mutationで8テストが失敗。 |
| RF-03 source digest test | FIXED | GeoJSON 4件とDXF 6件で入力exact bytesのhashlib.sha256を独立計算し、source_reference全体と完全一致。bytesとUTF-8 str、非ASCII metadata/layer、整形・改行差を含む。両readerのdigestを全0へ置換したmutationで10テストが失敗。 |
| RF-04 logging restore test | FIXED | fresh subprocessで_dxf_runtime import前にbaselineを保存。通常・例外の両出口、disable値0/WARNING、stdout/stderrの同一object復元、隠蔽出力の非漏出を4件で確認。別のfresh subprocess 2件でcustom streams・disable値100・nested contextも確認。finallyのlogging復元削除mutationで4テストが失敗。 |

## 独立実行

1. `tests/test_geometry_dxf.py` と `tests/test_geometry_geojson.py`: **202 passed**。
2. Git除外のtemporary synthetic verifier: **44 passed**。
   - raw sequenceの6破損種別 × R12/modern × LF/CRLF/CR: 36件。
   - INSERT属性sequenceと複数POLYLINEを含む正常入力 × R12/modern × 3改行: 6件。
   - import前baseline、custom streams、nested quiet_dxfの通常・例外: 2件。
3. 元headの全Python test関数をASTで比較: **93関数保持、削除0**。
   92関数はAST不変。変更した1関数はcurve拒否assertを追加し、curve削除後の既存NO_BOUNDARY検証も保持。

Pythonはrepositoryのvenvを使用。pytestは専用PYTEST_DEBUG_TEMPROOTと
`-o cache_dir=.cache/pytest-repair-verifier`で実行し、`--basetemp`は未使用。
追加44件は検証用temporary scriptであり、恒久suiteの件数には含めない。
旧unknown unit、mm→m、自己交差、open/ambiguous boundary、Z、bulge、width、thicknessの
検証は削除されておらず、対象DXF/GeoJSON suite内の該当ケースも通過した。

## Mutation証跡の独立照合

実装担当が実行した隔離copy probeのscript、結果manifest、実際のpytestログ、copy上の
test bytes、現在のsource SHA-256を独立に照合した。以下はその実行証跡であり、
focused verifierによるmutation再実行ではない。

| Probe | 実行結果 | 判定 |
| --- | --- | --- |
| 非破壊baseline | 54 passed | PASS |
| RF-01 曲線guard無効化 | 20 failed | MUTATION_KILLED |
| RF-02 raw sequence guard除去 | 8 failed | MUTATION_KILLED |
| RF-03 GeoJSON/DXF digest全0 | 10 failed | MUTATION_KILLED |
| RF-04 logging復元除去 | 4 failed | MUTATION_KILLED |

各probeはcopyからのmodule importを確認している。copyの対象test bytesは元repositoryと一致。
collection errorはなく、ログの実件数とmanifestは一致した。元source/testのbefore/after
SHA-256一致に加え、focused検証後の現ファイルも記録値に一致した。
生ログ・temporary script・mutation copy・raw inputはGit除外local領域に限定し、本報告には含めない。

## 検証範囲と残るゲート

- 親担当から全体Python 346件、Web 28件、lint/type/build、pip check、public boundary scan、
  diff checkの通過報告を受領。focused verifier自身の実行は上記202件と追加44件である。
- 既存292件のPython testを削除・弱体化して件数を調整した差分はない。追加恒久testは54件。
- 新headのcommit/push、PR Draft状態、exact-head CIは本focused検証では未観測。
  配送担当が別途確認する。未観測事項をPASSとしていない。
- 実装・既存test・Git/PR状態をverifierは変更していない。恒久変更は本報告だけ。
- 新たな品質負債は追加しない。既存D01/D02/D03は本検証の対象外。
- Human Gate: **STOP — Independent Re-Review required before Ready / merge**。
- Documentation Sync Trigger: **yes**。Notion/Obsidianへの直接更新は行っていない。

## 検証した実装・テストのSHA-256

| File | SHA-256 |
| --- | --- |
| `src/bve/geometry/dxf.py` | `d28857420a661db75c8002a29ef631135e34de026db68f780bcbdc7279505fba` |
| `tests/test_geometry_dxf.py` | `cc3d60588a2f83f2ba78da1e03798652367d3a5a52e86459afcdadb46de261fb` |
| `tests/test_geometry_geojson.py` | `999809aafbf938238d8db242bf08efaa7f75f93d315ae4fd40668553eea62648` |
