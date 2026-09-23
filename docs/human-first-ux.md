# Human-first UX / MVP-RC2A

設計者が「敷地条件から初期ボリュームを比較する」目的と、次の行動を理解できる画面を提供する。
UXR-01（JSON中心の入口）、UXR-02（engine用語）、UXR-03（比較条件の不明瞭さ）を対象とする。
一般的な資料準備・候補比較のパターンを採用し、競合製品の画面を複製しない。

## 最初の3つの行動

1. **サンプルで試す**：既存の公開synthetic ProjectとSearchを1操作で表示する。架空の案件と明記する。
2. **自分の検討結果を開く**：ローカルSDG / BVE Coreで作成済みのフォルダを選択する。
   全ファイル同時選択と単体Search JSONは折りたたんだ補助経路として維持する。
3. **自分の案件を準備する**：敷地形状、敷地・法規条件、計画条件、任意の配置検討範囲の4分類を案内する。
   最初から全資料を揃える必要はない。ただし実計算の必須入力や未知値のfail-closed契約は緩めない。

初期viewportには目的と3行動を置き、長いプロンプトやPhase名を表示しない。
資料準備の詳細欄に既存PROJECT_PROMPTを変更せず保持する。利用者が外部AIへ資料・条件とプロンプトを渡し、
生成されたProjectの値と出典を人が確認してlocal BVE Coreで使う手順を説明する。
このWebから外部AIへの送信は行わず、AI調査値を公式確認済みへ昇格しない。

## 用語と出典状態

通常の条件表は「項目 / 値 / 確認状態」。固定のmapperで建築用語へ変換する。
未知pathは「その他の入力条件」とし、任意の内部pathを主画面へechoしない。

| 内部の意味 | 通常表示 |
| --- | --- |
| site area | 敷地面積 |
| building coverage ratio | 建ぺい率 |
| floor area ratio | 容積率 |
| height cap / limit | 高さ制限 |
| floor height / floor count | 想定階高 / 階数 |
| footprint area / gross floor area | 建築面積 / 延床面積 |
| area basis | 面積算定の基準 |
| constraint usage | 条件に対する利用状況 |
| FAR stack / Height stack | 容積率の計算条件 / 高さ制限の計算条件 |
| buildable area | 指定された配置検討範囲 |

| 入力status（変更しない） | 通常表示 |
| --- | --- |
| official_verified | 公式資料で確認済み |
| user_provided | ユーザー入力 |
| drawing_derived | 図面から取得 |
| llm_researched | AI調査・公式未確認 |
| assumed | 仮定・要確認 |
| unknown | 未確認 |
| review_required | 要確認 |

値と由来・確認状態は通常画面にも残す。表示する状態は入力データの申告であり、Webによる出典認証ではない。
色だけに依存しない。reviewRequiredを再計算しない。高さの未指定、値を確定できない状態、既知0mを混同しない。
配置検討範囲は外部で指定されたpolygonであり、「法的建築可能範囲」と呼ばない。

## 比較の読み方

候補表の前に「今回、何を比較しているか」を表示する。
現行strategyの比較条件は想定階高。比較値はSearchの`search.floorHeightsM`を元の順序で投影する。
値をsample固定値で補わず、sort・default grid・順位計算を追加しない。
並び順は延床面積が大きい順、同値時は想定階高が低い順と説明し、正本のrankと配列順を維持する。
最終candidateReference tie-breakの詳細は技術欄に保持する。

案 A/B/C…は正本rankの表示名。rankとcandidateReferenceで選択を照合し、
選択案の延床面積・建築面積・階数・建物高さ・想定階高をKPIと表・平面図へ表示する。
authoritative caps / basis / review / provenanceを使い、既存の表示用差分・比率以外の算術を追加しない。
FAR min、Height min、tie、legal governing、containmentをブラウザで再計算しない。
丸めは表示だけで原本を変えない。順位は設計品質・推奨・最適性・法規適合を意味しない。
zero acceptedは正常な完了結果として、比較した階高と案が作成されなかったケースを表示する。

## 通常画面と詳細データの境界

通常画面には目的、操作、比較軸、KPI、確認状態と短い安全説明を置く。
次の事実は削除せず、default collapsedのnative details/summaryへ置く。

- Schema判定、schemaVersion、packageVersion、artifact数、browser integrityの意味。
- Search / Ranking strategy ID、candidateReference、inputReferences、SHA-256参照。
- raw status、JSON path、cap ID / kind、rejection code。
- Pythonのsemantic authority、exact ranking規則、表示丸めとD04数値字句の制限。

Pythonが計算・意味検証の正本であること、ブラウザで送信・保存しないことは通常画面にも短く表示する。
通常画面の安全説明は次を維持する。

> この結果は入力された条件による初期ボリューム検討です。法規適合や建築可能最大値を証明するものではありません。

## 現MVPの境界と検証

資料・条件の準備 → local Python BVE Coreによる計算・semantic verify → browser-only viewerという経路。
WebでのPDF/DXF自動解析、住所からの法規取得、LLMによる法規確認、BVE計算は実装しない。
未実装機能をdisabled upload buttonで提供中のように見せない。
Source/Core/schema/fixtureのcanonical bytes、Search0.1〜0.5 / Package0.1〜0.4のvalidator契約を維持する。
入力はmemory-only。ClearはProject/sample/package/candidate/図形/inputを破棄し、進行中の読込・hashからの遅延handoffを拒否する。
追加dependency、network/storage/API、編集・保存、3Dはない。

semantic heading、input/button label、aria-live、keyboard、focus-visible、table headerを維持する。
390×844でKPIを縦配置し、比較表だけを横スクロール可能にしてroot overflowを発生させない。
RC2A-WEB-01〜24と既存205件、Python1165件、128MiB probes4件、local production実画面・privacyを検証する。
詳細な実行結果は対応するRunのEVIDENCEを参照する。Vercel検証はこのRunの対象外。
D02 OPEN / PLATFORM_BLOCKED、D04 OPENを継承する。

Documentation Sync Trigger: yes — MVP-RC2A human-first UX milestone。
外部Notion/Obsidianへこの実装から直接書き込まない。
