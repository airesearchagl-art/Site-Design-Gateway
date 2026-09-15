# Evidence

Only executed checks may be marked PASS. Private paths, runtime results and raw logs remain ignored.

## Wave 0

Fresh Gate PASS: `origin/main` and local branch base are `2abb5c8a8508eacdbf629466c4f9726c85a94f16`; the worktree was clean and the Phase 5 feature branch did not already exist. The exact ignored packet snapshot matches SHA-256 `d685b90ea2cf98ac3014fa0f74c7c54caa915b822f945b62cbb473b5cea0ed72`. No Vercel operation was performed.

## Wave 1

The complete current Python CLI pipeline generated `cases/example-urban-office/search-result.json`: Geometry PASS, Constraints PASS and Search PASS with evaluated=5 / accepted=5 / rejected=0 / reviewRequired=true. Fixture length is 6,147 bytes and SHA-256 is `96b81ec252622bce9721d100b70264238b4db083599af0c6cd58c3cc6f9b017a`. The new integration test regenerated all intermediate files under a temporary directory and matched the tracked fixture byte-for-byte.
