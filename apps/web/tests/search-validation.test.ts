import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";
import sample from "../../../cases/example-urban-office/search-result.json" with { type: "json" };
import {
  MAX_SEARCH_BYTES,
  MAX_SEARCH_DEPTH,
  MAX_SEARCH_NODES,
  validateSearchFile,
  validateSearchJson,
} from "../src/lib/search-validation.ts";
import { searchTextWithinResources } from "../src/lib/search-resource-preflight.ts";

function changed(mutator: (value: typeof sample) => void): string {
  const value = structuredClone(sample);
  mutator(value);
  return JSON.stringify(value);
}

test("canonical Search Result sample is displayable through the shared schema registry", () => {
  const result = validateSearchJson(JSON.stringify(sample));
  assert.equal(result.state, "DISPLAYABLE");
  assert.equal(result.schema, "PASS");
  if (result.state !== "DISPLAYABLE") return;
  assert.deepEqual(result.value.summary, {
    accepted: 5,
    evaluated: 5,
    hasFeasibleCandidate: true,
    rejected: 0,
    reviewRequired: true,
  });
});

test("zero accepted is a displayable completed Search Result", () => {
  const value = structuredClone(sample);
  value.search.floorHeightsM = [32, 40];
  value.summary = {
    accepted: 0,
    evaluated: 2,
    hasFeasibleCandidate: false,
    rejected: 2,
    reviewRequired: true,
  };
  value.rankedCandidates = [];
  (value as unknown as { rejections: Array<{ floorHeightM: number; code: string }> }).rejections = [
    { floorHeightM: 32, code: "NO_FEASIBLE_MASSING" },
    { floorHeightM: 40, code: "NO_FEASIBLE_MASSING" },
  ];
  assert.equal(validateSearchJson(JSON.stringify(value)).state, "DISPLAYABLE");
});

test("Search Schema tampering fails without exposing values", () => {
  const marker = "SYNTHETIC_DO_NOT_ECHO";
  const inputs = [
    changed((value) => { value.schemaVersion = "unsupported"; }),
    changed((value) => { delete (value as Partial<typeof value>).summary; }),
    changed((value) => { delete (value.rankedCandidates[0].candidate as Partial<typeof value.rankedCandidates[0]["candidate"]>).candidate; }),
    changed((value) => { delete (value.rankedCandidates[0] as Partial<typeof value.rankedCandidates[0]>).rank; }),
    changed((value) => { value.rankedCandidates[0].candidateReference = marker; }),
    changed((value) => {
      (value as unknown as { rejections: Array<{ floorHeightM: number; code: string }> })
        .rejections.push({ floorHeightM: 32, code: marker });
    }),
  ];
  for (const input of inputs) {
    const result = validateSearchJson(input);
    assert.equal(result.state, "INVALID");
    assert.equal(result.schema, "FAIL");
    assert.ok(!JSON.stringify(result).includes(marker));
    assert.ok(result.issues.every((issue) => issue.path && issue.keyword && issue.message === "Search Result Schemaに適合しません。"));
  }
});

test("viewer byte and depth limits stay distinct from schema invalid", () => {
  const oversized = validateSearchJson(" ".repeat(MAX_SEARCH_BYTES + 1));
  assert.equal(oversized.state, "VIEWER_LIMIT");
  assert.equal(oversized.schema, "NOT_CHECKED");
  const deeplyNested = validateSearchJson("[".repeat(70) + "0" + "]".repeat(70));
  assert.equal(deeplyNested.state, "VIEWER_LIMIT");
  assert.equal(deeplyNested.schema, "NOT_CHECKED");
});

for (const kind of ["wide4", "wide6", "wide8", "deep6"]) {
  test(`${kind} input is rejected before parsing under a 128 MiB heap`, () => {
    const probe = fileURLToPath(new URL("search-resource-probe.ts", import.meta.url));
    const execution = spawnSync(
      process.execPath,
      ["--max-old-space-size=128", "--experimental-strip-types", probe, kind],
      { encoding: "utf8", timeout: 30_000 },
    );
    assert.equal(execution.status, 0, execution.stderr);
    assert.equal(execution.stdout.trim(), "PASS");
  });
}

test("raw resource rejection precedes JSON.parse for node and depth budgets", (t) => {
  const parse = t.mock.method(JSON, "parse");
  for (const input of [
    `[${"0,".repeat(MAX_SEARCH_NODES - 1)}0]`,
    "[".repeat(MAX_SEARCH_DEPTH + 1) + "0" + "]".repeat(MAX_SEARCH_DEPTH + 1),
  ]) {
    const result = validateSearchJson(input);
    assert.equal(result.state, "VIEWER_LIMIT");
    assert.equal(result.schema, "NOT_CHECKED");
  }
  assert.equal(parse.mock.callCount(), 0);
});

test("node budget counts root and values but not object keys", () => {
  for (const count of [MAX_SEARCH_NODES - 1, MAX_SEARCH_NODES, MAX_SEARCH_NODES + 1]) {
    const array = `[${"0,".repeat(count - 2)}0]`;
    const object = `{${Array.from({ length: count - 1 }, (_, index) => `"k${index}":0`).join(",")}}`;
    for (const input of [array, object]) {
      assert.equal(searchTextWithinResources(input, MAX_SEARCH_DEPTH, MAX_SEARCH_NODES), count <= MAX_SEARCH_NODES);
      const result = validateSearchJson(input);
      assert.equal(result.state, count <= MAX_SEARCH_NODES ? "INVALID" : "VIEWER_LIMIT");
      if (count <= MAX_SEARCH_NODES) assert.equal(result.issues[0].message, "Search Result Schemaに適合しません。");
    }
  }
});

test("preflight and parsed depth agree at root zero and depth 64", () => {
  for (const depth of [0, MAX_SEARCH_DEPTH, MAX_SEARCH_DEPTH + 1]) {
    for (const pair of [["[", "]"], ['{"k":', "}"]]) {
      for (const leaf of ["0", '"value"', "null", "{}", "[]"]) {
        const input = pair[0].repeat(depth) + leaf + pair[1].repeat(depth);
        assert.equal(searchTextWithinResources(input, MAX_SEARCH_DEPTH, MAX_SEARCH_NODES), depth <= MAX_SEARCH_DEPTH);
        assert.equal(validateSearchJson(input).state, depth <= MAX_SEARCH_DEPTH ? "INVALID" : "VIEWER_LIMIT");
      }
    }
  }
});

test("resource scanner ignores string structure, escaped quotes and backslashes", () => {
  const strings = [",,,:", "[]{}:".repeat(100), 'abc\\\"[,]{}', "\\\\", "日本語🌱", 'a\\\\\"b'];
  for (const value of strings) {
    for (const input of [JSON.stringify(value), JSON.stringify({ [value]: value }), JSON.stringify([value])]) {
      assert.equal(searchTextWithinResources(input, 1, 2), true);
      assert.equal(searchTextWithinResources(input, 1, 1), !input.startsWith("{") && !input.startsWith("["));
    }
  }
  const largeString = JSON.stringify("[],{}:".repeat(500_000));
  assert.equal(searchTextWithinResources(largeString, 0, 1), true);
  assert.equal(validateSearchJson(largeString).state, "INVALID");
});

test("duplicate member occurrences consume preflight budget before overwriting", () => {
  assert.equal(searchTextWithinResources('{"k":0,"k":1}', 1, 3), true);
  assert.equal(searchTextWithinResources('{"k":0,"k":1}', 1, 2), false);
});

test("preflight leaves below-budget malformed syntax to JSON.parse", (t) => {
  const parse = t.mock.method(JSON, "parse");
  const inputs = ['{"k":}', "[0,]", "[", '"unterminated', "{]", "true false", "", '"\\uZZZZ"'];
  for (const input of inputs) {
    const result = validateSearchJson(input);
    assert.equal(result.state, "INVALID");
    assert.equal(result.issues[0].keyword, "syntax");
  }
  assert.equal(parse.mock.callCount(), inputs.length);
});

test("manageable input at and just under the byte limit retains EOF whitespace", async () => {
  const text = JSON.stringify(sample);
  for (const size of [MAX_SEARCH_BYTES - 1, MAX_SEARCH_BYTES]) {
    const input = text + " ".repeat(size - Buffer.byteLength(text) - 4) + "\t\r\n\n";
    const file = new File([input], "boundary.json");
    assert.equal(file.size, size);
    assert.equal((await validateSearchFile(file)).state, "DISPLAYABLE");
  }
});

test("actual-buffer limit precedes UTF-8 decoding when reported size is small", async () => {
  const result = await validateSearchFile({
    name: "search.json",
    size: 1,
    arrayBuffer: async () => new Uint8Array(MAX_SEARCH_BYTES + 1).fill(0xff).buffer,
  });
  assert.equal(result.state, "VIEWER_LIMIT");
  assert.equal(result.schema, "NOT_CHECKED");
});

test("malformed JSON and non-finite parsing stay invalid with generic diagnostics", () => {
  const marker = "SYNTHETIC_DO_NOT_ECHO";
  assert.equal(validateSearchJson(`{"${marker}":`).state, "INVALID");
  assert.ok(!JSON.stringify(validateSearchJson(`{"${marker}":`)).includes(marker));
  const overflow = JSON.stringify(sample).replace('"grossFloorAreaM2":1120', '"grossFloorAreaM2":1e400');
  assert.equal(validateSearchJson(overflow).state, "INVALID");
});

test("file boundary rejects extension, oversize, malformed UTF-8, BOM and read errors", async () => {
  const text = JSON.stringify(sample);
  assert.equal((await validateSearchFile(new File([text], "search.json"))).state, "DISPLAYABLE");
  assert.equal((await validateSearchFile(new File([text], "search.txt"))).state, "INVALID");
  let read = false;
  const oversized = await validateSearchFile({
    name: "search.json",
    size: MAX_SEARCH_BYTES + 1,
    arrayBuffer: async () => { read = true; return new ArrayBuffer(0); },
  });
  assert.equal(oversized.state, "VIEWER_LIMIT");
  assert.equal(read, false);
  const misreported = await validateSearchFile({
    name: "search.json",
    size: 1,
    arrayBuffer: async () => new ArrayBuffer(MAX_SEARCH_BYTES + 1),
  });
  assert.equal(misreported.state, "VIEWER_LIMIT");
  assert.equal((await validateSearchFile(new File([new Uint8Array([0xff])], "search.json"))).state, "INVALID");
  assert.equal((await validateSearchFile(new File(["\ufeff", text], "search.json"))).state, "INVALID");
  const failed = await validateSearchFile({
    name: "search.json",
    size: 1,
    arrayBuffer: async () => { throw new Error("SYNTHETIC_DO_NOT_ECHO"); },
  });
  assert.equal(failed.state, "INVALID");
  assert.ok(!JSON.stringify(failed).includes("SYNTHETIC_DO_NOT_ECHO"));
});
