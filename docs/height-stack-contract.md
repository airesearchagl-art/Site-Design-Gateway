# Explicit scalar height stack / Phase 11

明示されたscalar上限だけを扱う。斜線・方位・道路幅員・用途地域・高度地区・日影・天空率・setbackを計算しない。
spatial planeからscalarへの変換、LLM値の法令採用、governing legal rule / 法規適合の判定も行わない。

## Version matrix

| Package | Project | Geometry | Constraint | Search | Manifest |
| --- | --- | --- | --- | --- | --- |
| sdg-run-package-v0.1 | 0.1 | 0.1 | 0.1 | 0.2 | 0.1 |
| sdg-run-package-v0.2 | 0.2 | 0.1 | 0.2 | 0.3 | 0.2 |
| sdg-run-package-v0.3 | 0.3 | 0.1 | 0.3 | 0.4 | 0.3 |

旧11schema・legacy fixture・canonical bytes・calculation IDs・review policyは不変。
Project versionとmanifest packageVersionを明示dispatchし、unknown/mixedを拒否する。latest fallback / auto upgradeなし。

## Inputs and scalar semantics

Project0.3はFAR stackを継承し、additionalHeightCapsを必須とする。0..16件、追加なしは明示 `[]`。
IDはstable slug・最大80・height配列内unique、base-heightはreserved。FARと高さのID空間は別。
kindはabsolute_height_explicit / district_plan_explicit / external_rule_result / other_explicit。
各kindは外部から数値化済みの入力という分類であり、BVEが空間規制を解釈した意味ではない。
追加値はnumber >=0またはnull、unit m、既存7statuses。nullはunknown/review_requiredだけ。
base heightLimitはoptionalのまま、既存positive/null schemaを参照する（base0は不適合）。

baseが存在する場合だけbase-height / base_height / zoning.heightLimitをstack先頭に作る。
追加はzoning.additionalHeightCaps、stable IDで識別し、入力順を維持する。array indexをidentityにしない。
referenceはcanonical Project bytesのSHA-256。statusを昇格せず、任意descriptionやsource pathを追加しない。

- baseなし・追加なし: ABSENT、maxHeightM/effectiveHeightMはnull、IDs/stackは空、review false。
- declared entryにnullあり: UNAVAILABLE、数値はnull、IDsは空、stackを保持。
- 全numeric: Python Decimal min、maxHeightMとeffectiveHeightMは同じ値。0mもCOMPUTED。
- tie: minimumの全IDをbase first / 追加入力順で保持。hidden rounding / sortなし。

v0.3 height固有review対象はllm_researched / assumed / unknown / review_required。
FAR v0.2とlegacy review policyは変更しない。height計算IDはheight_cap_stack_v0.3。

## Reader authority — Human-confirmed API distinction

`load_constraint_result(payload)` はcapStackから派生値を再計算し、値/IDs/review・固定input・内部referenceを照合する。
自己整合した元条件の変更は、それだけでは検出できない。単体ファイルの自己申告hashは出典認証ではない。

`load_constraint_result(payload, project=validated_project)` は、上記に加えて元Projectのreference/versionと
全source条件を使って再計算する。id/kind/非最小値/status/input/順序まで元Projectと一致する必要がある。
Package0.3のcreate/verifyはこの照合を必須とする。単体readerとの区別はTask中にHuman確認済み。
元Project全文をConstraint Resultに複製せず、新たな入力保存・漏出経路を作らない。
geometryの真正性は既存normalized geometry binding / package replayで確認する。

## Search / Package / browser

Search0.4はareaBasis、FAR、height、derived constraintCapsをcanonical exact比較する。
effective maxHeightMだけを既存Massingへ渡し、floor count / ranking / tie-breakは維持する。
0mは既存NO_FEASIBLE_MASSINGの全point rejection、completed zero accepted。
ABSENT/UNAVAILABLEは共有REQUIRED_CONSTRAINT_UNAVAILABLEで失敗。partial/staging packageを残さない。
Candidate0.1のpositive cap schemaは変更せず、Search0.4のcontextCapsだけが0/nullを受け入れる。

Webは15schema registryで構造/integrityを確認し、出力済みeffectiveHeightM/IDsを表示する。
min/tie/sort/geometry/法的判断を行わない。ABSENT/UNAVAILABLEのschema-only表示はPython実行成功を示さない。
legacy Search0.1/0.2/0.3、Package0.1/0.2、FAR/Area Basis/Usage/SVGを維持する。

- Effective height cap is the minimum of the explicit scalar height caps supplied to BVE.
- It does not evaluate spatial slope planes, identify the governing legal rule, or prove regulatory compliance.

入力はbrowser memoryのみ、Clearで破棄。既存resource/preflight/8MiB/128MiB/network/storage境界は維持する。
D04 OPEN。新dependency NONE。Vercel NOT TOUCHED、D02 OPEN / PLATFORM_BLOCKED。

公開synthetic project-height-stack.jsonはFAR400%、高さ24mがeffective。
実engineの階高4/5/6/7/8m結果はGFA800/640/640/480/480m²。旧v0.1/v0.2の全5ファイルhashも固定検証する。
