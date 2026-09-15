import assert from "node:assert/strict";
import { MAX_SEARCH_BYTES, validateSearchJson } from "../src/lib/search-validation.ts";

const kind = process.argv[2] ?? "wide4";
assert.ok(["wide4", "wide6", "wide8", "deep6"].includes(kind));
const elements = kind === "wide4" ? 2_000_001 : kind === "wide8" ? 4_000_001 : 3_000_001;
const input = kind === "deep6"
  ? "[".repeat(3_000_000) + "0" + "]".repeat(3_000_000)
  : `[${"0,".repeat(elements - 1)}0]`;
assert.ok(Buffer.byteLength(input) < MAX_SEARCH_BYTES);

const parse = JSON.parse;
let parseCalls = 0;
try {
  JSON.parse = (text, reviver) => { parseCalls += 1; return parse(text, reviver); };
  const result = validateSearchJson(input);
  assert.equal(result.state, "VIEWER_LIMIT");
  assert.equal(result.schema, "NOT_CHECKED");
  assert.equal(parseCalls, 0, "resource rejection must precede JSON.parse");
} finally {
  JSON.parse = parse;
}

process.stdout.write("PASS\n");
