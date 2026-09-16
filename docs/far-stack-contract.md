# Explicit FAR Constraint Stack / Phase 10

入力済みの数値上限を比較するgeneric contract。道路幅員×係数、用途地域・自治体・地区計画の解釈、
LLMによる法令採用、governing legal rule / 法規適合の判定を行わない。

## Version compatibility

| Package | Project | Geometry | Constraint | Search | Manifest |
| --- | --- | --- | --- | --- | --- |
| sdg-run-package-v0.1 | 0.1 | 0.1 | 0.1 | 0.2 | 0.1 |
| sdg-run-package-v0.2 | 0.2 | 0.1 | 0.2 | 0.3 | 0.2 |

既存7schemaは変更せず、新4schemaから共通定義を参照する。旧canonical bytes / calculation ID /
REVIEW_STATUSES / ranking・rejection semanticsを維持する。versionの自動変換・latest fallbackはない。
直接ViewerはSearch0.1/0.2/0.3を受け入れる。

## Project0.2 and provenance

`zoning.additionalFloorAreaRatioCaps` は必須、0..16件。追加なしは `[]`。
entryはstable slug ID（最大80・unique・base-zoning禁止）、kind、value、unit、statusのみ。
kindはroad_width_derived / district_plan_explicit / other_explicit。外部で得た値の分類に留まる。
valueは0以上のnumberまたはnull、unitはpercent、statusは既存7種。nullはunknown/review_requiredのみ。
description・案件名・source pathを追加しない。

base FARは `zoning.floorAreaRatio` からimplicit `base-zoning` / `base_zoning` entryを作る。
追加entryは入力順で保持し、provenance inputは `zoning.additionalFloorAreaRatioCaps`、identityはID。
array indexをidentityにしない。referenceはcanonical Project bytesのSHA-256。
statusはそのまま保持し、official_verifiedへ昇格しない。

## Decimal composition

全cap numericならPython Decimalの最小値をeffectiveCapPercentとする。
同値minimumの全IDをbase first / 追加入力順でeffectiveCapIdsへ格納する。hidden sortはない。
`maxTotalFloorAreaM2` は既存 `floor_area_cap` helperでselected area × effective percent / 100を計算する。
float比較・別の面積式・任意の丸めは追加しない。

一つでもnullならstate UNAVAILABLE、effective percent / max GFAはnull、effective IDsは空。
capStack自体は保持する。未知capを無視した数値採用はしない。
v0.2 FAR固有review対象はllm_researched / assumed / unknown / review_required。
selected area provenanceの既存reviewも集約する。旧v0.1 review policyは変更しない。

## Constraint / Search / Package

Constraint0.2 FARは `floor_area_cap_stack_v0.2`、ordered capStack、state、effective値/IDs、
max GFA、review、selected area provenanceを保持する。BCR/height/area basisは既存契約のまま。
readerはprovenanceから再計算して全派生値を照合する。
Search0.3はauthoritative FAR contextをexact copyし、Python exportが全fieldを検証する。
areaBasis・constraintCaps照合も維持する。

候補生成時のconstraintCapsはeffective numeric値のみ。Massing generator / candidate0.1 schema、
GFA ranking・階高/hash tie-breakは変更しない。0% FARは全pointが既存NO_FEASIBLE_MASSINGとなり、
zero acceptedの完了結果を出す。context用capsはConstraint0.2のversioned定義を参照し、0を許容する。
未知FARでは従来の共有入力エラーREQUIRED_CONSTRAINT_UNAVAILABLEでSearchを停止し、packageを作らない。

Run createはProject version、verifyはmanifest packageVersionで明示dispatchする。
version混在を拒否し、固定5ファイル・exact hashes・相互参照・exclusive atomic publishを維持する。

## Browser authority and privacy

11schemaのoffline registryを共有する。Webはschema/integrityと表示だけを扱う。
Python出力のeffectiveCapPercent / effectiveCapIdsをそのまま表示し、min・tie・sortを実装しない。
UNAVAILABLEのschema-only表示受入はPython semantic PASSを意味しない。D04 OPEN。
FAR panelには以下を表示する。

- Effective FAR cap is the minimum of the explicit numeric caps supplied to BVE.
- It does not identify the governing legal rule or prove regulatory compliance.

legacyではcontext unavailableと表示する。入力はmemoryのみ、Clearで破棄する。
既存resource guard・8 MiB・128 MiB probes・全storage/network禁止を維持する。
新dependencyなし。Vercelは操作しない。D02 OPEN / PLATFORM_BLOCKED。

## Synthetic evidence

公開project-far-stack.jsonはbase600%、additional400%、敷地200m²。
実エンジンはeffective400%、max GFA800m²、階高4/5/6/7/8mでGFA800/800/800/640/480m²を生成する。
実案件・道路幅員・法令係数は使わない。test matrixと実行結果はPhase 10 Run記録に記載する。
