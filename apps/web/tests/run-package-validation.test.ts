import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { PACKAGE_FILES, PACKAGE_LIMITS, validateRunPackage, type SelectedPackageFile } from "../src/lib/run-package-validation.ts";
import { MAX_SEARCH_DEPTH, MAX_SEARCH_NODES, validateSearchJson } from "../src/lib/search-validation.ts";
import { initialCandidate, toSearchViewModel } from "../src/lib/search-view.ts";
import { artifactNames, document, files, packageBytes, rehash, setDocument } from "./package-fixture.ts";

const marker = "SYNTHETIC_DO_NOT_ECHO";
const fakeReference = "sha256:" + "0".repeat(64);

test("P9-WEB-01 canonical five-file package passes in fallback and directory modes", async () => {
  for (const root of [undefined, "SDG_Run"]) {
    const bytes = packageBytes();
    const result = await validateRunPackage(files(bytes, root));
    assert.equal(result.state, "DISPLAYABLE");
    if (result.state !== "DISPLAYABLE") return;
    assert.equal(result.packageVersion, "sdg-run-package-v0.1");
    assert.equal(result.artifactCount, 4);
    assert.deepEqual(result.search.value.summary, { evaluated: 5, accepted: 5, rejected: 0, hasFeasibleCandidate: true, reviewRequired: true });
    assert.deepEqual(bytes, packageBytes());
  }
});

for (const name of PACKAGE_FILES) {
  test(`P9-WEB-02 missing ${name} is invalid before reads`, async () => {
    let reads = 0;
    const selected = files(packageBytes()).filter((file) => file.name !== name).map((file) => ({
      name: file.name, size: file.size, arrayBuffer: async () => { reads++; throw new Error(marker); },
    }));
    const result = await validateRunPackage(selected);
    assert.equal(result.state, "INVALID");
    assert.equal(result.issues[0]?.code, "fileSet");
    assert.equal(reads, 0);
  });
}

for (const name of ["extra.json", ".DS_Store", "Thumbs.db"]) {
  test(`P9-WEB-03 extra file ${name} is invalid`, async () => {
    const result = await validateRunPackage([...files(packageBytes()), new File([marker], name)]);
    assert.equal(result.state, "INVALID");
    assert.equal(result.issues[0]?.code, "fileSet");
  });
}
test("P9-WEB-04 duplicate names cannot replace a missing file", async () => {
  const selected = files(packageBytes());
  selected[4] = selected[0];
  const result = await validateRunPackage(selected);
  assert.equal(result.state, "INVALID");
  assert.equal(result.issues[0]?.code, "fileSet");
});

for (const relative of ["SDG_Run/sub/search-result.json", "Other/search-result.json", "", "/search-result.json", "../search-result.json",
  "X:/search-result.json", "SDG_Run\\sub/search-result.json", "SDG_Run/wrong.json"]) {
  test(`P9-WEB-05/06 selected relative path variant ${relative || "empty"} is invalid`, async () => {
    const selected = files(packageBytes(), "SDG_Run");
    const file = selected[4];
    selected[4] = { name: file.name, size: file.size, arrayBuffer: () => file.arrayBuffer(), webkitRelativePath: relative };
    const result = await validateRunPackage(selected);
    assert.equal(result.state, "INVALID");
    assert.equal(result.issues[0]?.code, "relativePath");
  });
}

for (const [index, name] of PACKAGE_FILES.entries()) {
  test(`P9-WEB-${String(index + 7).padStart(2, "0")} ${name} shared schema is mandatory`, async () => {
    const bytes = packageBytes();
    const value = document(bytes, name);
    value.schemaVersion = marker;
    setDocument(bytes, name, value);
    if (name !== "manifest.json") rehash(bytes, name);
    const result = await validateRunPackage(files(bytes));
    assert.equal(result.state, "INVALID");
    assert.equal(result.issues[0]?.code, "schema");
    assert.equal(result.issues[0]?.file, name);
    assert.ok(!JSON.stringify(result).includes(marker));
  });
}

for (const name of artifactNames) {
  test(`P9-WEB-12 ${name} exact-byte hash tamper is rejected`, async () => {
    const bytes = packageBytes();
    const old = bytes[name];
    bytes[name] = new Uint8Array(old.byteLength + 1);
    bytes[name].set(old);
    bytes[name][old.byteLength] = 32; // Valid JSON, changed exact bytes.
    const result = await validateRunPackage(files(bytes));
    assert.equal(result.state, "INVALID");
    assert.equal(result.issues[0]?.code, "hashMismatch");
    assert.equal(result.issues[0]?.file, name);
  });
}

for (const [id, name, field] of [
  [13, "constraints.json", "project"], [14, "constraints.json", "geometry"],
  [15, "search-result.json", "project"], [16, "search-result.json", "geometry"], [17, "search-result.json", "constraints"],
] as const) {
  test(`P9-WEB-${id} ${name} ${field} reference mismatch survives valid hashes`, async () => {
    const bytes = packageBytes();
    const value = document(bytes, name);
    value.inputReferences[field] = fakeReference;
    setDocument(bytes, name, value);
    rehash(bytes, name, true);
    const result = await validateRunPackage(files(bytes));
    assert.equal(result.state, "INVALID");
    assert.equal(result.issues[0]?.code, "referenceMismatch");
    assert.equal(result.issues[0]?.file, name);
  });
}

test("P9-WEB-18 area basis configuration must match", async () => {
  const bytes = packageBytes();
  const manifest = document(bytes, "manifest.json");
  manifest.configuration.areaBasis = "geometry_area";
  setDocument(bytes, "manifest.json", manifest);
  const result = await validateRunPackage(files(bytes));
  assert.equal(result.state, "INVALID");
  assert.equal(result.issues[0]?.code, "configurationMismatch");
});

for (const heights of [[4, 5], [4, 5, 6, 7, 9], [8, 7, 6, 5, 4]]) {
  test(`P9-WEB-19 height length/value/order ${heights.join("-")} must match without sorting`, async () => {
    const bytes = packageBytes();
    const manifest = document(bytes, "manifest.json");
    manifest.configuration.floorHeightsM = heights;
    setDocument(bytes, "manifest.json", manifest);
    const result = await validateRunPackage(files(bytes));
    assert.equal(result.state, "INVALID");
    assert.equal(result.issues[0]?.code, "configurationMismatch");
    assert.deepEqual(document(bytes, "manifest.json").configuration.floorHeightsM, heights);
  });
}

for (const [index, name] of PACKAGE_FILES.entries()) {
  test(`P9-WEB-${20 + index} oversized ${name} causes zero arrayBuffer calls across the entire selection`, async () => {
    let reads = 0;
    const selected = files(packageBytes()).map((file) => ({
      name: file.name, size: file.name === name ? PACKAGE_LIMITS[name] + 1 : file.size,
      arrayBuffer: async () => { reads++; throw new Error(marker); },
    }));
    const result = await validateRunPackage(selected);
    assert.equal(result.state, "VIEWER_LIMIT");
    assert.equal(result.issues[0]?.code, "maxBytes");
    assert.equal(result.issues[0]?.file, name);
    assert.equal(reads, 0);
  });
  test(`actual-buffer recheck precedes decode for misreported ${name}`, async () => {
    const selected = files(packageBytes());
    selected[index] = { name, size: 1, arrayBuffer: async () => new Uint8Array(PACKAGE_LIMITS[name] + 1).fill(255).buffer };
    const result = await validateRunPackage(selected);
    assert.equal(result.state, "VIEWER_LIMIT");
    assert.equal(result.issues[0]?.file, name);
  });
}

test("P9-WEB-25 package handoff reuses the validated Search object and existing view model", async () => {
  const bytes = packageBytes();
  const result = await validateRunPackage(files(bytes));
  assert.equal(result.state, "DISPLAYABLE");
  if (result.state !== "DISPLAYABLE") return;
  assert.deepEqual(result.search, validateSearchJson(new TextDecoder().decode(bytes["search-result.json"])));
  assert.equal(initialCandidate(toSearchViewModel(result.search.value))?.rank, 1);
  const serialized = JSON.stringify(result);
  assert.ok(!serialized.includes("Example Urban Office"));
  assert.ok(!serialized.includes('"artifacts":'));
  assert.ok(!serialized.includes('"bytes":'));
});

test("P9-WEB-26 zero accepted canonical package is displayable", async () => {
  const result = await validateRunPackage(files(packageBytes(true)));
  assert.equal(result.state, "DISPLAYABLE");
  if (result.state !== "DISPLAYABLE") return;
  const model = toSearchViewModel(result.search.value);
  assert.equal(model.summary.accepted, 0);
  assert.equal(model.rejections.length, 2);
  assert.equal(model.candidates.length, 0);
  assert.equal(initialCandidate(model), undefined);
  assert.ok(model.constraintContext);
});

test("P9-WEB-27/28 direct Search v0.1 and v0.2 still use the original validator", () => {
  const value = document(packageBytes(), "search-result.json");
  assert.equal(validateSearchJson(JSON.stringify(value)).state, "DISPLAYABLE");
  value.schemaVersion = "0.1";
  delete value.constraintContext;
  assert.equal(validateSearchJson(JSON.stringify(value)).state, "DISPLAYABLE");
});

test("Package v0.1 requires Search v0.2 while the direct legacy route stays supported", async () => {
  const bytes = packageBytes();
  const value = document(bytes, "search-result.json");
  value.schemaVersion = "0.1";
  delete value.constraintContext;
  setDocument(bytes, "search-result.json", value);
  rehash(bytes, "search-result.json");
  const result = await validateRunPackage(files(bytes));
  assert.equal(result.state, "INVALID");
  assert.equal(result.issues[0]?.file, "search-result.json");
});

for (const path of ["../project.json", "/synthetic/project.json", "X:/synthetic.json", "folder/project.json", "other.json"]) {
  test(`fixed manifest path rejects ${path}`, async () => {
    const bytes = packageBytes();
    const manifest = document(bytes, "manifest.json");
    manifest.artifacts.project.path = path;
    setDocument(bytes, "manifest.json", manifest);
    const result = await validateRunPackage(files(bytes));
    assert.equal(result.state, "INVALID");
    assert.equal(result.issues[0]?.code, "schema");
    assert.ok(!JSON.stringify(result).includes(path));
  });
}

test("browser accepts schema/integrity consistency without replaying ranking or legal semantics", async () => {
  const bytes = packageBytes();
  const search = document(bytes, "search-result.json");
  search.rankedCandidates[0].candidateReference = fakeReference;
  search.rankedCandidates.reverse();
  setDocument(bytes, "search-result.json", search);
  rehash(bytes, "search-result.json");
  const result = await validateRunPackage(files(bytes));
  assert.equal(result.state, "DISPLAYABLE");
  if (result.state !== "DISPLAYABLE") return;
  assert.deepEqual(result.search.value.rankedCandidates.map((entry) => entry.rank), [5, 4, 3, 2, 1]);
});

test("SHA-256 uses exact selected bytes through native Web Crypto only", async (t) => {
  const digest = t.mock.method(globalThis.crypto.subtle, "digest");
  const bytes = packageBytes();
  const result = await validateRunPackage(files(bytes));
  assert.equal(result.state, "DISPLAYABLE");
  assert.equal(digest.mock.callCount(), 4);
  digest.mock.calls.forEach((call, index) => {
    assert.equal(call.arguments[0], "SHA-256");
    assert.deepEqual(new Uint8Array(call.arguments[1] as ArrayBuffer), bytes[artifactNames[index]]);
  });
});

test("native crypto/read failures and attacker keys never leak raw diagnostics", async (t) => {
  const bytes = packageBytes();
  const manifest = document(bytes, "manifest.json");
  manifest[marker] = marker;
  setDocument(bytes, "manifest.json", manifest);
  assert.ok(!JSON.stringify(await validateRunPackage(files(bytes))).includes(marker));
  t.mock.method(globalThis.crypto.subtle, "digest", async () => { throw new Error(marker); });
  const result = await validateRunPackage(files(packageBytes()));
  assert.equal(result.state, "INVALID");
  assert.equal(result.issues[0]?.code, "crypto");
  assert.ok(!JSON.stringify(result).includes(marker));
});

for (const name of PACKAGE_FILES) {
  test(`${name} malformed UTF-8/BOM/syntax/read exception stays generic`, async () => {
    for (const body of [new Uint8Array([255]), new TextEncoder().encode("\ufeff{}"), new TextEncoder().encode(`{"${marker}":`)]) {
      const bytes = packageBytes();
      bytes[name] = body;
      const result = await validateRunPackage(files(bytes));
      assert.equal(result.state, "INVALID");
      assert.ok(!JSON.stringify(result).includes(marker));
    }
    const selected = files(packageBytes()).map((file) => file.name === name
      ? { name, size: 1, arrayBuffer: async () => { throw new Error(marker); } } : file);
    const result = await validateRunPackage(selected);
    assert.equal(result.state, "INVALID");
    assert.equal(result.issues[0]?.code, "read");
    assert.ok(!JSON.stringify(result).includes(marker));
  });
}

test("package Search resources remain screened before JSON.parse", async (t) => {
  const bytes = packageBytes();
  const inputs = ["[".repeat(MAX_SEARCH_DEPTH + 1) + "0" + "]".repeat(MAX_SEARCH_DEPTH + 1),
    `[${"0,".repeat(MAX_SEARCH_NODES - 1)}0]`];
  const parse = t.mock.method(JSON, "parse");
  for (const input of inputs) {
    bytes["search-result.json"] = new TextEncoder().encode(input);
    const result = await validateRunPackage(files(bytes));
    assert.equal(result.state, "VIEWER_LIMIT");
    assert.ok(!parse.mock.calls.some((call) => call.arguments[0] === input));
  }
});

test("other artifacts also screen raw depth before parsing", async (t) => {
  const parse = t.mock.method(JSON, "parse");
  const input = "[".repeat(66) + "0" + "]".repeat(66);
  for (const name of ["manifest.json", "project.json", "site.geojson", "constraints.json"] as const) {
    const bytes = packageBytes();
    bytes[name] = new TextEncoder().encode(input);
    assert.equal((await validateRunPackage(files(bytes))).state, "VIEWER_LIMIT");
    assert.ok(!parse.mock.calls.some((call) => call.arguments[0] === input));
  }
});

test("cancelled package read does not read another artifact or hand off Search", async () => {
  const controller = new AbortController();
  let finish!: (value: ArrayBuffer) => void;
  let reads = 0;
  const bytes = packageBytes();
  const selected: SelectedPackageFile[] = files(bytes).map((file, index) => ({
    name: file.name, size: file.size,
    arrayBuffer: async () => { reads++; return index === 0 ? new Promise<ArrayBuffer>((resolve) => { finish = resolve; }) : file.arrayBuffer(); },
  }));
  const pending = validateRunPackage(selected, controller.signal);
  controller.abort();
  finish(bytes["manifest.json"].buffer);
  const result = await pending;
  assert.equal(result.state, "INVALID");
  assert.equal(result.issues[0]?.code, "cancelled");
  assert.equal(reads, 1);
  assert.equal((await validateRunPackage(selected, controller.signal)).issues[0]?.code, "cancelled");
  assert.equal(reads, 1);
});

test("manifest schema version and package version remain fixed", async () => {
  const bytes = packageBytes();
  const manifest = document(bytes, "manifest.json");
  manifest.packageVersion = "sdg-run-package-v0.2";
  setDocument(bytes, "manifest.json", manifest);
  assert.equal((await validateRunPackage(files(bytes))).state, "INVALID");
});

test("shared registry imports twenty-one canonical schemas including the fifteen legacy contracts", () => {
  const source = readFileSync(new URL("../src/lib/schema-registry.ts", import.meta.url), "utf8");
  assert.equal((source.match(/schemas\/sdg-/g) ?? []).length, 21);
  assert.ok(source.includes("sdg-run-manifest-v0.1.schema.json"));
  assert.ok(!source.includes("compileAsync"));
});
