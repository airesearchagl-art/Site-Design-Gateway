# ADR 0003: Explicit area basis and traced constraint arithmetic

Status: Accepted for Phase 2 implementation; Independent Review/Human gate pending.

Projectの宣言面積とPolygonの計算面積は別の出典を持つ。暗黙の統合は候補生成に誤った上限を渡すため、
二択のarea basisを必須とし、両面積と符号付き差を残す。差分閾値・行政上の判定は導入しない。

Project/Geometryの既存schemaを消費し、Constraint Resultだけに独立したschemaを追加する。
Geometry metadataの整合検査はGeometry packageへ集約し、Constraint側へPolygon検証を複製しない。
出典enum/条件定義は正本Project schemaをoffline参照する。入力参照はexact bytesのSHA-256。

3計算は固定Python functionで実装する。Decimalと独立Contextで丸めや環境precision依存を避け、
同じ入力から同じJSON number表現を出力する。係数/指数の資源上限は明示rejectとし、値を切り詰めない。
JSON出力の小さな固定型encoderは数値表現だけを担い、formula/DSL/plugin機構は持たない。

COMPUTED/UNAVAILABLE/ABSENTを個別に表し、入力ごとのprovenanceを保持する。
reviewRequiredは要確認出典の有無で、法規適合や建築可能性を意味しない。
独立CLIのみを提供し、Web接続・実法規・massing・storageを先行実装しない。

追加dependencyなし。同期source/editable installを維持し、wheel配布/サービスは未検証。
Phase 0/1 ADRは歴史として保持する。Phase 2 Draft作成後STOP。
次工程は別RunのVercel Preview Smoke（Phase 2 merge後、Phase 3前に必須）。

参照: [Decimal context](https://docs.python.org/3.12/library/decimal.html)、
[JSON Schema offline references](https://python-jsonschema.readthedocs.io/en/stable/referencing/)。
