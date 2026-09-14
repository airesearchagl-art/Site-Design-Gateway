# Phase 2 独立検証

- Run: `LR-20260915-SDG-P2-001`
- Task Packet: `LRP-20260915-SDG-P2-001`, revision 1
- Packet SHA-256: `ba34e9db0f06a8fc7302985fb3215e21da79abdf0d9bb00be3631cd616f7908e`
- Branch: `feat/phase2-constraint-engine`
- Exact base / observed origin/main: `eb4d3ea4711955bf137bc27137a71c3e55787787`
- 検証対象HEAD: `e285f9c55d82b0dac253451efdb694f36642e140`
- 判定: **ローカル独立検証 PASS。受入条件に対するblocking findingなし。**

実装担当と別Contextで要求原本、Read First、manifest/state/queue/debt/evidence、変更差分、
API/CLI/Schema/テストを確認した。開始時のbranch/base/head/clean treeとexact packetのhashを照合。
ソース・Schema・既存テストは編集せず、検証用synthetic入力・script・結果はGit除外local/cache内に限定した。
この判定はremote CI観測、Draft PR作成、Independent Review/Human承認を代行しない。

## 独立実行したチェック

| チェック | 観測結果 |
| --- | --- |
| Python全回帰 | 492件、全成功、exit 0。収集件数も別途確認 |
| Phase 0/1既存回帰 | 上記に含む346件。元の5 test filesがexact baseと同一、収集件数346を確認 |
| Phase 2追加テスト | 上記に含む146件 |
| Web tests | 28件、全成功 |
| `npm run lint` | ESLint・TypeScript成功 |
| `npm run build` | Next.js build・静的生成成功 |
| `pip check` | No broken requirements found |
| 公開境界scan | 検証開始時94 candidate filesでPASS。レポート追加後も96 filesでPASS |
| `git diff --check` | 成功 |
| 独立追加probe | 184 assertion成功。詳細は下記 |
| 隔離mutation再実行 | baseline53成功、4種のmutationをすべて検出 |

Pythonはrepositoryの仮想環境を使用。pytestは専用のignored cache/tempを使い、
`--basetemp`を使用していない。全回帰の実行は`python -m pytest --tb=no -q`相当。
npm依存更新・credential取得・権限変更・deployは行っていない。

## 主要契約の判定

| 契約 | 判定・証拠 |
| --- | --- |
| 明示area basis | PASS。未指定AREA_BASIS_REQUIRED、不正値INVALID_AREA_BASIS。default・自動選択なし |
| synthetic上限 | PASS。両basisとも160 m2 / 1200 m2 / 31 m、reviewRequired=true |
| 200/198の乖離 | PASS。declaredは160/1200、geometryは158.4/1188。両面積とdifference=2を保持 |
| 差分の意味 | PASS。declared−geometryの符号付き差。逆符号とnullも保持し、差を合否thresholdに使わない |
| null/absent | PASS。BCR/FAR/height nullは個別UNAVAILABLE、height欠落ABSENT。他条件の計算を継続 |
| 選択面積null | PASS。declared選択はAREA_BASIS_UNAVAILABLE。geometry選択は宣言面積・差分nullを保持して計算 |
| 7 status・review | PASS。各5入力位置の全7状態を保持。BCR/FARはarea+ratio、heightはheightのみ。未選択面積も比較証跡に残る |
| LLM非昇格 | PASS。llm_researched保持。昇格mutationで5 assertion failureを独立に再観測 |
| normalized Geometry | PASS。既存Schema、有限2D座標、閉ring、Shapely validity、再計算面積/boundsをGeometry package内で確認 |
| Geometry改変 | PASS。200の面積を199とする改変、bounds変更、非有限座標、開ring、自己交差、余分metadataを拒否。floatより細かいmetadata改変も拒否 |
| encoded ring順序 | PASS。穴付きPolygonの逆順・開始点変更8種類をWKB・面積・bounds・hashで確認。producerのencoded順で再計算し、比較前の再配列をしない |
| exact input references | PASS。Project/normalized Geometryそれぞれexact bytesのSHA-256。Unicode・空白・CRLFを含む入力でも照合。旧sourceReferenceをcurrent input hashと誤認しない |
| 固定3計算 | PASS。coverage/floor/heightの明示関数と固定identifierのみ。eval・DSL・任意formulaなし |
| 数値決定性 | PASS。Decimal結果を独立Fraction計算60ケースと完全比較。caller precision=1・狭い指数範囲・全trap有効でも60ケースの結果bytesとcaller contextを保持 |
| export決定性 | PASS。Decimalをfloatへ戻さずJSON number化。キー順・配列順・末尾LFを固定。複数hash seedの同一入力でbytes一致 |
| output Schema | PASS。既存Projectの条件/statusをoffline参照。state/value/provenance形状の不整合を拒否。Schemaは出力構造契約であり法規確認ではない |
| CLI非開示 | PASS。成功は件数/review、失敗は固定code。試験した失敗でstderrは空。名前・path・入力全文・座標を結果/診断に複製しない |
| exclusive export | PASS。既存出力・入力自身への出力を拒否しbytes不変。no-outputはファイルを作らない。部分書込障害はIO_ERROR |
| offline参照 | PASS。socket接続を拒否した状態でcache再構築・入力/出力Schema検証が成功 |
| 既存契約・scope | PASS。Project/Geometry Schema、fixture、dependency、Web source、既存test filesはexact baseから不変 |
| Web境界 | PASS。Web/Python未接続。TS計算複製・API/subprocess・storage・upload・telemetry追加なし |
| docs・次Gate | PASS。Phase 2、法規検証との区別、独立CLI、Draft STOP、次のVercel Gateを記載 |

## 独立probeの内訳

| 分類 | 成功assertion数 |
| --- | ---: |
| FractionをoracleとするBCR/FAR完全一致 | 60 |
| ambient Decimal contextから独立、context不変 | 60 |
| area/BCR/FAR null × height value/null/absentの組合せ | 24 |
| 選択declared area nullの拒否 | 12 |
| 穴付きringの逆順・開始点変更roundtrip | 8 |
| Geometry/metadataの改変拒否 | 6 |
| float精度より小さなarea/bounds改変拒否 | 2 |
| CLI seed 0/77/randomの固定summary・stderr | 3 |
| exact digestとprivate marker非複製 | 3 |
| seed間のexport bytes完全一致 | 1 |
| CLI basis未指定・不正・既存出力の固定失敗 | 3 |
| 入力bytes不変 | 1 |
| offline Schema検証 | 1 |
| 合計 | 184 |

probe作成時の一時的な失敗2件はharnessの数値token置換とWindows標準出力改行の期待値に起因した。
harnessだけを修正し全184 assertionを再実行した。production sourceの修正はない。

## Mutation検出力

既存mutation手順を読み、別のignored隔離コピーで再実行。各processがcopy内moduleを
importしていることをassertし、collection errorではなく対象assertionのfailureであることを確認した。

| Probe | 観測 |
| --- | --- |
| 無変更baseline | 53 PASS |
| llm_researchedをofficial_verifiedへ変換 | 5 FAIL、検出 |
| 未指定basisをdeclaredへ置換 | 1 FAIL、検出 |
| metadata mismatchを無視 | 5 FAIL、検出 |
| Project/Geometry digestを固定値へ置換 | 8 FAIL、検出 |

元のsource/testsのSHA-256は前後一致。mutationはrepository実装へ適用していない。

## 未観測・既知の制限

- remote exact-head CI、Draft PR状態、PR作成後の状態はこのVerifierでは未観測。親Runの最終Gateで確認する。
- Vercel deploy/Hosted Preview、390px hosted UI、Production、Phase 3は未実施。D02はPhase 2中nonblocking。
- source/editable installと現在の依存版・ローカルWindows環境で検証。wheel単体配布、別依存版間の数値同一性、サービス並行実行は未検証。
- 出典statusは申告を保持する契約。法規適合・測量精度・出典の真偽をこの計算から証明しない。
- 直接Python APIで渡すSiteGeometryのreferenceは生成readerのreference。normalizedファイルを消費する経路は専用loaderを使用する。
- output Schema単独で演算結果やフィールド間の全数値同一性を証明するものではない。本Phaseではengineとその出力経路を検証した。
- OS書込失敗時の部分ファイル残留は契約に明記済み。成功扱いせず、既存ファイルへ再実行しても上書きしない。
- Gitのglobal ignore読込に環境権限warningが出たが、対象コマンドはexit 0。repository内ignoreの適用とpublic candidate scanは確認済み。

Next Gate: **Vercel Preview Smoke — REQUIRED BEFORE PHASE 3**。
Phase 2 merge後の別Runで実施。Human Gate: **STOP — Independent Review required**。
Documentation Sync Trigger: **yes**。Notion/Obsidianへの直接更新なし。

## 検証対象bytesのSHA-256

以下は実行対象ファイルのローカルexact bytes。git blob hashではない。
親がsource/schema/testsを後から変更した場合は、この表との差分に対応する再検証が必要。
Python source/schema/testsは独立probeの前後で一致し、既存mutation証跡のsource/testsとも照合した。
Webはexact baseから不変で、上記lint/test/buildの対象。相対パスだけを公開する。

| ファイル | SHA-256 |
| --- | --- |
| apps/web/eslint.config.mjs | `43fcf069eece8c11d1cc5abfc76225a4a12ed968e5437ee0365b76a7baa9caaf` |
| apps/web/next.config.ts | `ca584b9da7a79a4b7bbcd9418d4dba9e617a94527f7a4520489ffda1cc98c7d6` |
| apps/web/package.json | `c93fea48347d6aeeb5718481e5ee30d7a7b910ca3f8e98d0534552fb9de8c4e7` |
| apps/web/src/app/globals.css | `faabc830a7ff0cee87cba60eeefb5b964d2c8dd19e7d167dbca7c2836b580b04` |
| apps/web/src/app/layout.tsx | `71b8e3ba94acfd10a84a637775a50b0779ead505bf3d174b72e607d930b0834e` |
| apps/web/src/app/page.tsx | `b002e435e76ba57e936f8b188ce22a40794ba2006bd7c038d293360f30fbbe69` |
| apps/web/src/lib/prompt.ts | `c9e007a1a5e8eb50e0f244afe072669ee7c199fecd4d08fc9c43a9944213a808` |
| apps/web/src/lib/validation.ts | `fcccc28660217bc2bc39acb7c3ca7012d2cbc968e666c6308186a5b0d02d94eb` |
| apps/web/tests/validation.test.ts | `5502e641fab178273262a7d32e994193e61adcdf44315386d5202b618a6e81aa` |
| apps/web/tsconfig.json | `d0c57096850b4e14d8288e255f5c74cd94e0868a164a1175eb2c62389df4b376` |
| schemas/sdg-constraint-result-v0.1.schema.json | `2da9fcb39acf8236cfd0a4fe9857b6b637d53bcebf88539e9e396a36a50381a9` |
| schemas/sdg-project-v0.1.schema.json | `5c042a93fc4274db470275b3d966c8e6bb4ce84e69c205a076754d7cef2b46ce` |
| schemas/sdg-site-geometry-v0.1.schema.json | `49b26fe9e01a5e7fc474affa7782b32210b231d8343b0e9875bd2f7010f7ed11` |
| src/bve/__init__.py | `74863d33175ecf8db35dbb25276c8e0c8d56288a6c8d121546b5e3cce8224fdf` |
| src/bve/__main__.py | `6ac75b875e71a8c3c8117dd37ae91f2413aa163eae756df33f1a4ab053ef1ba4` |
| src/bve/_json.py | `5253702e94f0e9c91b04e3c89d5ed4349b2dc40a708d0dbe393d0bc95b234929` |
| src/bve/_schemas.py | `dcf5cd744d3036362af90dfff1518a860f384688496699efe5840e9e42203987` |
| src/bve/constraints/__init__.py | `1b089185167078a3f1a81d8dbb1d627001819c73491cf7c31226f105e6105af4` |
| src/bve/constraints/__main__.py | `ba57ac8787109b4eef9522b938b94217b52dbf7f3b61ba4942b3cb5121dd66f2` |
| src/bve/constraints/arithmetic.py | `3af7bfdc779bb6d7fe2a67e77bbd7ff4465db3bd8c9a094d9d337897b0cc7d8c` |
| src/bve/constraints/engine.py | `0dc3a51f7340f87e4db3286de8ed84c8c3e6e07a0602edd8185f9e85470adcac` |
| src/bve/constraints/errors.py | `38d46a25dc7422f95e20705af718cffcdd861ebf572957fcdaf8d978adf2cc28` |
| src/bve/constraints/export.py | `4ac1c1ffe4c60f003de74260eff53138bfb04772a55bd29d594edd4ec8a45fb4` |
| src/bve/constraints/inputs.py | `1bf02cd1d7ff22451a79e0e7075168c06970ed16fd9f50fc12cfdcb8fc5de08e` |
| src/bve/constraints/model.py | `3622611625eae81efce79e71c5d9c59cadd0d56bd928469d6ed9ffa8d45ba0a9` |
| src/bve/geometry/__init__.py | `0d8ea55972f0cccfb5df417d886eeafe21c67d24b3326e2de91fe7521182cc12` |
| src/bve/geometry/__main__.py | `b9fef8fd39755cb232040837b34934c1441a116364b5188dde6b8d926d93b265` |
| src/bve/geometry/_dxf_runtime.py | `2a96dae712b61d82e4e158fb5b73608b7898219b9421d1ee7f3f577bc17e9e74` |
| src/bve/geometry/dxf.py | `d28857420a661db75c8002a29ef631135e34de026db68f780bcbdc7279505fba` |
| src/bve/geometry/errors.py | `c50845a46908462a23a08bf015707f33d340a2e3df4072c7879b3ee92c6c0c23` |
| src/bve/geometry/export.py | `db6fe8c9f62cd17e2260b380c07a05ccd741285a4476ac5450361d23327dc9e3` |
| src/bve/geometry/geojson.py | `220f46e8e1b67ce1605eb8e22e351cc9e9496117c8abbb8cc4b3ea2c99a1c01a` |
| src/bve/geometry/model.py | `81c7712ec3a8243a7742f300738cb7b89f383320123c8363944e14687f518293` |
| src/bve/geometry/normalization.py | `06139b353babc712d7730c8633cb8a8bbf47a57460e1dbd97fd53fdce397a346` |
| src/bve/geometry/normalized.py | `c5f7cb1b9ab745f6ba22c8358e77c30bbe75f2fd4d84d1af48ca4773021257f1` |
| src/bve/validation.py | `19513010366cb9c92167e2efe0fa57309403511e7a83798fbded408be46b22b3` |
| tests/conftest.py | `841a538fe77968c96df44481a78d93a10d8fc4114a8eb6541fe608e960bde8b4` |
| tests/test_constraints_adversarial.py | `9e472bfc8d736a79334798fc0d85b33fb9ba8930f51347b2abfa26303dfd0789` |
| tests/test_constraints_cli.py | `6bcbf51b507df49ee2e98764b15e908375fd4f28ed49f9f72e972e43be7e542e` |
| tests/test_constraints_engine.py | `5b32c02af0b0a97b08b548dda6129c2010b2d3b683084bc8bc2e9fac88003a08` |
| tests/test_constraints_inputs.py | `900c8be9013cea527fb8c141090e6a4ef77125a121af65ef36fbcd8be464144b` |
| tests/test_constraints_provenance.py | `7bec65bf3dffee485bf741a262c76ce97510273d0a7d8535130455a9c86694c7` |
| tests/test_geometry_cli.py | `72b48a7e0769d27f2745bb96beb170a347c43f05081189c247bc02de0ec1f796` |
| tests/test_geometry_dxf.py | `cc3d60588a2f83f2ba78da1e03798652367d3a5a52e86459afcdadb46de261fb` |
| tests/test_geometry_geojson.py | `999809aafbf938238d8db242bf08efaa7f75f93d315ae4fd40668553eea62648` |
| tests/test_geometry_integration.py | `80c14034cacdf5f7e76a3c1ebe8e589555f1e11f6173fb21b2a6a30cc4a181d9` |
| tests/test_geometry_normalized.py | `2cbacd030dcf4c0131d778b4278c1f9ee6a9aad50521d54eddc1cf2ef3bcc75b` |
| tests/test_validation.py | `06aab9f230f64f09d307d28882a9e1a85f2ea821f66ea86cca33fb876c923927` |
