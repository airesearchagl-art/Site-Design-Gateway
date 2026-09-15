import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";
import sample from "../../../cases/example-urban-office/search-result.json" with { type: "json" };
import {
  MAX_SEARCH_BYTES,
  validateSearchFile,
  validateSearchJson,
} from "../src/lib/search-validation.ts";

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
    changed((value) => { value.schemaVersion = "0.2" as "0.1"; }),
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

test("wide input reaches the node limit under a 128 MiB heap", () => {
  const probe = fileURLToPath(new URL("search-resource-probe.ts", import.meta.url));
  const execution = spawnSync(
    process.execPath,
    ["--max-old-space-size=128", "--experimental-strip-types", probe],
    { encoding: "utf8", timeout: 30_000 },
  );
  assert.equal(execution.status, 0, execution.stderr);
  assert.equal(execution.stdout.trim(), "PASS");
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
