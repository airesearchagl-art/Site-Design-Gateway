import assert from "node:assert/strict";
import test from "node:test";
import schema from "../../../schemas/sdg-project-v0.1.schema.json" with { type: "json" };
import sample from "../../../cases/example-urban-office/project.json" with { type: "json" };
import { validateJson, validateFile, MAX_JSON_BYTES } from "../src/lib/validation.ts";
import { PROJECT_PROMPT } from "../src/lib/prompt.ts";

function trustedSample() {
  const value = structuredClone(sample);
  for (const quantity of [value.site.area, ...Object.values(value.zoning)]) quantity.status = "user_provided";
  return value;
}

test("synthetic sample passes schema but requires review", () => {
  const result = validateJson(JSON.stringify(sample));
  assert.equal(result.schema, "PASS");
  assert.equal(result.outcome, "REVIEW_REQUIRED");
  assert.equal(result.sources.length, 4);
  assert.deepEqual(result.issues, []);
});

test("declared statuses are fixed to seven values", () => {
  assert.deepEqual(schema.$defs.status.enum, ["official_verified", "user_provided", "drawing_derived", "llm_researched", "assumed", "unknown", "review_required"]);
});

for (const status of schema.$defs.status.enum) {
  test(`source status ${status} has the required UI outcome`, () => {
    const value = trustedSample();
    value.site.area.status = status;
    const result = validateJson(JSON.stringify(value));
    assert.equal(result.schema, "PASS");
    assert.equal(result.outcome, ["assumed", "unknown", "review_required"].includes(status) ? "REVIEW_REQUIRED" : "VALID");
    assert.equal(result.sources[0].status, status);
  });
}

for (const text of ["", "{", '{"x":}', "null", "[]", '"text"', "1", "NaN", "Infinity"]) {
  test(`invalid syntax or root (${JSON.stringify(text)}) fails`, () => {
    const result = validateJson(text);
    assert.equal(result.schema, "FAIL");
    assert.equal(result.outcome, "INVALID");
    assert.ok(result.issues.length > 0);
    assert.deepEqual(result.sources, []);
  });
}

test("invalid status is rejected before review classification", () => {
  const value = structuredClone(sample);
  value.site.area.status = "verified_by_ai";
  const result = validateJson(JSON.stringify(value));
  assert.equal(result.outcome, "INVALID");
  assert.ok(result.issues.some((issue) => issue.path === "/site/area/status"));
});

test("missing fields, extra fields, wrong units, and numeric constraints fail", () => {
  const mutations = [
    { ...sample, schemaVersion: "0.2" },
    { ...sample, zoning: {} },
    { ...sample, extra: true },
    { ...sample, site: { area: { ...sample.site.area, unit: "mm2" } } },
    { ...sample, site: { area: { ...sample.site.area, value: "200" } } },
    { ...sample, site: { area: { ...sample.site.area, value: 0 } } },
    { ...sample, zoning: { ...sample.zoning, buildingCoverageRatio: { ...sample.zoning.buildingCoverageRatio, value: 101 } } },
    { ...sample, zoning: { ...sample.zoning, floorAreaRatio: { ...sample.zoning.floorAreaRatio, value: -1 } } },
  ];
  for (const value of mutations) assert.equal(validateJson(JSON.stringify(value)).schema, "FAIL");
});

test("null is accepted only with unknown or review_required status", () => {
  for (const status of schema.$defs.status.enum) {
    const value = { ...sample, site: { area: { value: null, unit: "m2", status } } };
    const result = validateJson(JSON.stringify(value));
    assert.equal(result.schema, ["unknown", "review_required"].includes(status) ? "PASS" : "FAIL");
  }
});

test("LLM provenance survives validation; input is never mutated", () => {
  const value = trustedSample();
  value.site.area.status = "llm_researched";
  const raw = JSON.stringify(value);
  const result = validateJson(raw);
  assert.equal(result.outcome, "VALID");
  assert.equal(result.sources[0].status, "llm_researched");
  assert.equal(JSON.stringify(value), raw);
  assert.ok(!result.sources.some((source) => source.status === "official_verified"));
});

test("malformed input snippets do not appear in issues", () => {
  const secretMarker = "SYNTHETIC_DO_NOT_ECHO";
  assert.ok(!JSON.stringify(validateJson(`{"${secretMarker}":`)).includes(secretMarker));
});

test("oversized, deeply nested and overflowing inputs fail safely", () => {
  assert.equal(validateJson(" ".repeat(MAX_JSON_BYTES + 1)).outcome, "INVALID");
  assert.equal(validateJson("[".repeat(40) + "0" + "]".repeat(40)).outcome, "INVALID");
  const text = JSON.stringify(sample).replace('"value":600', '"value":1e400');
  assert.equal(validateJson(text).schema, "FAIL");
});

test("file reading, extension, size and read errors use the actual input boundary", async () => {
  const text = JSON.stringify(sample);
  assert.equal((await validateFile(new File([text], "sample.json"))).schema, "PASS");
  assert.equal((await validateFile(new File([text], "sample.JSON"))).schema, "PASS");
  assert.equal((await validateFile(new File([text], "sample.txt"))).schema, "FAIL");
  let read = false;
  assert.equal((await validateFile({ name: "sample.json", size: MAX_JSON_BYTES + 1, text: async () => { read = true; return text; } })).schema, "FAIL");
  assert.equal(read, false);
  assert.equal((await validateFile({ name: "sample.json", size: 1, text: async () => { throw new Error("SYNTHETIC_DO_NOT_ECHO"); } })).schema, "FAIL");
});

test("copy prompt embeds the authoritative schema and synthetic sample", () => {
  assert.ok(PROJECT_PROMPT.includes(JSON.stringify(schema, null, 2)));
  assert.ok(PROJECT_PROMPT.includes(JSON.stringify(sample, null, 2)));
});
