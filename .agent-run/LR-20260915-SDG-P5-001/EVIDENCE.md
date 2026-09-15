# Evidence

Only executed checks may be marked PASS. Private paths, runtime results and raw logs remain ignored.

## Wave 0

Fresh Gate PASS: `origin/main` and local branch base are `2abb5c8a8508eacdbf629466c4f9726c85a94f16`; the worktree was clean and the Phase 5 feature branch did not already exist. The exact ignored packet snapshot matches SHA-256 `d685b90ea2cf98ac3014fa0f74c7c54caa915b822f945b62cbb473b5cea0ed72`. No Vercel operation was performed.

## Wave 1

The complete current Python CLI pipeline generated `cases/example-urban-office/search-result.json`: Geometry PASS, Constraints PASS and Search PASS with evaluated=5 / accepted=5 / rejected=0 / reviewRequired=true. Fixture length is 6,147 bytes and SHA-256 is `96b81ec252622bce9721d100b70264238b4db083599af0c6cd58c3cc6f9b017a`. The new integration test regenerated all intermediate files under a temporary directory and matched the tracked fixture byte-for-byte.

## Wave 2

Search validation tests cover the canonical shared-schema registry, six contract tamper classes, extension, 8 MiB pre-read and actual-buffer limits, malformed UTF-8/BOM/JSON, depth overflow, non-finite values, read errors and raw-value suppression. Pure view tests cover five accepted candidates, zero/mixed rejection results, preserved order, exact rank/reference lookup, exterior-ring Local XY rendering and degenerate/non-finite fallback. Full Web checks remain for later waves.

## Wave 3

The production UI compiles with STEP 03 and explicit EMPTY / LOADING / DISPLAYABLE / INVALID / VIEWER_LIMIT states. Web 38 tests, ESLint/TypeScript and Next production build PASS. React review found no effects, server data flow, nested component definitions or persistence; async file races are cancelled by request identity. Browser interaction and responsive smoke remain pending.

## Wave 4

Static UI/accessibility/responsive/privacy contracts PASS. `npm ci` installed the lockfile set (353 packages, audit 0 vulnerabilities), then production build/start ran on 127.0.0.1:3015. Desktop browser smoke: page and Project sample REVIEW_REQUIRED; local canonical Search fixture DISPLAYABLE; 5 rows with ranks 1..5; Rank 3 selection showed floor height 6 / GFA 800; REVIEW REQUIRED and one accessible SVG visible; Clear returned EMPTY and removed rows/SVG. The final rebuilt page repeated Project/local-file/5-rank/SVG/review/Clear checks with no console error/warn and no added observable page resource URL after file selection.

At 390px requested viewport, controls, 5 rows, initial Rank 1 and SVG remained available. Initial smoke found a root width 936px defect. After CSS repair and rebuild, BODY measured clientWidth=375 / scrollWidth=375 with overflow clipped at the root; the candidate table remained its own clientWidth=250 / scrollWidth=984 horizontal scroller. Visual screenshot showed no root horizontal bar. Browser storage globals are not exposed by the available read-only inspector; source guard tests prove no localStorage/sessionStorage/IndexedDB/Cache/network API call exists in Web source. No screenshot or runtime input was written to the repository.
