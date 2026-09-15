# ADR 0006: Search Resultをlocal-only browser viewerで扱う

- Status: Accepted
- Date: 2026-09-15

## Context

Phase 4 はcanonical Search Result JSONをローカルCLIから出力できる。Phase 5ではこの結果を比較できる入口が必要だが、
WebへBVE計算やprivate inputの送信経路を追加すると、計算の二重実装と公開境界の破壊につながる。

## Decision

Webはローカルファイルをbrowser memoryへ読み、shared canonical schemasで構文・resource・Schemaだけを確認する。
8 MiBをviewer固有上限としてSchema不正と区別する。表示はsummary、既存rank、rejection、read-only candidate metrics、
exterior ringだけの2D SVGに限定する。semantic validation、hash/input binding、BVE arithmeticはPythonの責務に残す。

public sampleはPython CLI pipelineから生成したexact canonical bytesを追跡し、Python testで再生成結果と一致させる。
Web用schema copy、API route、Server Action、upload、persistence、telemetry、新dependencyは追加しない。

## Consequences

ユーザーのSearch Resultは送信・永続化されず、CoreとUIの計算契約は分離される。
Schema PASSだけではPython semantic validation済みとは証明できず、UIにその限界を明示する。
JavaScript Numberの表示はPython Decimalの字句忠実性を保証しないためD04として継続管理する。

