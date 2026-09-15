# ADR 0005: Explicit floor-height search

Status: Accepted for Phase 4 foundation (2026-09-15).

Humanが列挙した階高だけをPhase 3 Generatorへ逐次渡す。最大64、既定gridなし。
幾何・floor計算はPhase 3に集約し、floor-height parserだけをpublic helperへ最小refactorする。
入力と出力はDecimal順に正規化し、duplicateは拒否する。
共有・構造的失敗をSearch全体へ伝播し、point rejectionは2固定codeだけに限定する。

GFA降順を唯一の指標とする。階高/hashのtie-breakはserializationにだけ使う。
設計品質、ユーザー嗜好、最適性や実法規を表現しない。footprint探索・score・optimizer・並列化は追加しない。
Searchが所有するcandidateのみを対象とし、export時にPhase 3検証とhash、partition、rankingを再確認する。
既存schemaのoffline参照で構造を再利用し、外部candidate readerや新依存は追加しない。

結果: 探索範囲と順位の意味は狭いが、全pointとrejectionを追跡できる。
zero acceptedは実行成功として明示し、建築可能性を主張しない。
D02はOPEN / PLATFORM_BLOCKED。Vercelの原因調査・再開は別Run。
詳細は[Search契約](../search-contract.md)。
