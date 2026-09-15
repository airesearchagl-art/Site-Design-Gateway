import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const WEB = join(dirname(fileURLToPath(import.meta.url)), "..");
const component = readFileSync(join(WEB, "src/components/search-result-viewer.tsx"), "utf8");
const page = readFileSync(join(WEB, "src/app/page.tsx"), "utf8");
const css = readFileSync(join(WEB, "src/app/globals.css"), "utf8");

function sourceFiles(directory: string): string[] {
  return readdirSync(directory).flatMap((name) => {
    const path = join(directory, name);
    return statSync(path).isDirectory() ? sourceFiles(path) : /\.(ts|tsx)$/.test(name) ? [path] : [];
  });
}

test("current phase header and all viewer states are explicit", () => {
  assert.ok(page.includes("PHASE 7 / RESULTS INTERPRETATION"));
  for (const state of ["EMPTY", "LOADING", "DISPLAYABLE", "INVALID", "VIEWER_LIMIT"]) {
    assert.ok(component.includes(state), `missing viewer state ${state}`);
  }
});

test("required ranking, review, zero-result and semantic-limit messages stay visible", () => {
  assert.ok(component.includes("順位はGFA降順による比較であり、設計品質・推奨・最適性・法規適合を意味しません。"));
  assert.match(component, /model\.summary\.reviewRequired\s*\?/);
  assert.ok(component.includes("REVIEW REQUIRED"));
  assert.match(component, /model\.candidates\.length === 0\s*\?/);
  assert.ok(component.includes("Search completed."));
  assert.ok(component.includes("semantic validationをブラウザで再実行したことを意味しません"));
});

test("viewer uses the tracked fixture and exposes read-only accessible controls", () => {
  assert.ok(component.includes('cases/example-urban-office/search-result.json'));
  for (const label of ["Search Result sample", "Clear result", "Search Result JSONファイルを選択", "Conceptual footprint · Local XY"]) {
    assert.ok(component.includes(label));
  }
  assert.ok(component.includes('role="img"'));
  assert.ok(component.includes('aria-pressed={active}'));
  assert.ok(component.includes('<th scope="col">'));
  assert.ok(!component.includes("download="));
});

test("responsive styles retain controlled table overflow at 390px", () => {
  assert.ok(css.includes("overflow-x: auto; contain: inline-size;"));
  assert.ok(css.includes("html, body { max-width: 100%; overflow-x: clip; }"));
  assert.match(css, /@media \(max-width: 760px\)/);
  assert.ok(css.includes(".search-controls { grid-template-columns: 1fr;"));
});

test("Web source has no input network, persistence or realtime capability", () => {
  const source = sourceFiles(join(WEB, "src")).map((path) => readFileSync(path, "utf8")).join("\n");
  for (const forbidden of [
    /\bfetch\s*\(/,
    /\bXMLHttpRequest\b/,
    /\bsendBeacon\b/,
    /\blocalStorage\b/,
    /\bsessionStorage\b/,
    /\bindexedDB\b/,
    /\bcaches\b/,
    /\bCacheStorage\b/,
    /\bWebSocket\b/,
    /\bEventSource\b/,
    /\bconsole\s*(?:\.|\[)/,
  ]) {
    assert.doesNotMatch(source, forbidden);
  }
});
