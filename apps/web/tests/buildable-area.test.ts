import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import test from "node:test";
import { createElement, type ComponentType } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";
import projectSample from "../../../cases/example-urban-office/project-buildable-area.json" with { type: "json" };
import heightProject from "../../../cases/example-urban-office/project-height-stack.json" with { type: "json" };
import farProject from "../../../cases/example-urban-office/project-far-stack.json" with { type: "json" };
import { validateJson } from "../src/lib/validation.ts";
import { validateSearchJson, type SearchResultDocument } from "../src/lib/search-validation.ts";
import { toSearchViewModel, footprintPreview, type SearchViewModel } from "../src/lib/search-view.ts";
import { validateRunPackage, PACKAGE_LIMITS } from "../src/lib/run-package-validation.ts";
import { canonicalPackage, document, files, packageBytes, rehash, setDocument } from "./package-fixture.ts";

const bytes = canonicalPackage(["4", "5", "6", "7", "8"], projectSample);
const legacy = [packageBytes(), canonicalPackage(["4"], farProject), canonicalPackage(["4"], heightProject)];
const componentFile = fileURLToPath(new URL("../src/components/buildable-area-panel.tsx", import.meta.url));
const require = createRequire(import.meta.url);
const source = readFileSync(componentFile, "utf8");
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, jsx: ts.JsxEmit.ReactJSX } }).outputText
  .replace(/from "([^"]+)"/g, (_, specifier: string) => `from ${JSON.stringify(pathToFileURL(specifier.startsWith(".") ? resolve(dirname(componentFile), specifier) : require.resolve(specifier)).href)}`);
const { BuildableAreaPanel } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`) as {
  BuildableAreaPanel: ComponentType<{ model: SearchViewModel }>;
};
function render(value = document(bytes, "search-result.json")) {
  return renderToStaticMarkup(createElement(BuildableAreaPanel, { model: toSearchViewModel(value as SearchResultDocument) }));
}

test("P12-WEB-01/12 Search0.5 authoritative domain display", () => {
  const value = document(bytes, "search-result.json");
  assert.equal(validateSearchJson(JSON.stringify(value)).state, "DISPLAYABLE");
  const before = JSON.stringify(value); const html = render(value);
  for (const text of ["Supplied buildable area", "98 m²", "drawing_derived", "explicit_buildable_area", "No spatial review flag",
    "Candidate footprint is constrained to the supplied domain by Python BVE."]) assert.ok(html.includes(text), text);
  assert.equal(JSON.stringify(value), before);
});

for (const version of ["0.1", "0.2", "0.3", "0.4"]) {
  test(`P12-WEB-02 legacy Search${version} displayable without inferred domain`, () => {
    const value = document(legacy[version === "0.4" ? 2 : version === "0.3" ? 1 : 0], "search-result.json");
    if (version === "0.1") { value.schemaVersion = "0.1"; delete value.constraintContext; }
    assert.equal(validateSearchJson(JSON.stringify(value)).state, "DISPLAYABLE");
    assert.equal(render(value), "");
  });
}

for (const [version, sourceBytes] of [["0.1", legacy[0]], ["0.2", legacy[1]], ["0.3", legacy[2]], ["0.4", bytes]] as const) {
  test(`P12-WEB-03/04 Package${version} explicit file matrix`, async () => {
    for (const root of [undefined, "SDG_Run"]) {
      const result = await validateRunPackage(files(sourceBytes, root));
      assert.equal(result.state, "DISPLAYABLE");
      if (result.state === "DISPLAYABLE") {
        assert.equal(result.packageVersion, "sdg-run-package-v" + version);
        assert.equal(result.artifactCount, version === "0.4" ? 5 : 4);
      }
    }
  });
}

test("P12-WEB-05/06 exact version-specific file sets", async () => {
  const missing = files(bytes).filter((file) => file.name !== "buildable-area.geojson");
  const extra = [...files(legacy[2]), files(bytes).find((file) => file.name === "buildable-area.geojson")!];
  for (const selected of [missing, extra, [...files(bytes), files(bytes)[0]], files(bytes).slice(1)]) {
    const result = await validateRunPackage(selected);
    assert.equal(result.state, "INVALID"); assert.equal(result.issues[0]?.code, "fileSet");
  }
});

test("P12-WEB-07 every size including buildable preflighted before any read", async () => {
  let reads = 0;
  const selected = files(bytes).map((file) => ({ ...file, name: file.name,
    size: file.name === "buildable-area.geojson" ? PACKAGE_LIMITS["buildable-area.geojson"] + 1 : file.size,
    arrayBuffer: async () => { reads++; return file.arrayBuffer(); } }));
  const result = await validateRunPackage(selected);
  assert.equal(result.state, "VIEWER_LIMIT"); assert.equal(result.issues[0]?.file, "buildable-area.geojson");
  assert.equal(reads, 0);
});

test("buildable actual buffer checked despite false small metadata", async () => {
  const selected = files(bytes).map((file) => file.name !== "buildable-area.geojson" ? file : {
    name: file.name, size: 1, arrayBuffer: async () => new ArrayBuffer(PACKAGE_LIMITS["buildable-area.geojson"] + 1),
  });
  const result = await validateRunPackage(selected);
  assert.equal(result.state, "VIEWER_LIMIT"); assert.equal(result.issues[0]?.file, "buildable-area.geojson");
});

test("P12-WEB-08 buildable SHA is checked independently of schema", async () => {
  const changed = structuredClone(bytes); const value = document(changed, "buildable-area.geojson");
  value.properties.areaM2 = 97; setDocument(changed, "buildable-area.geojson", value);
  const result = await validateRunPackage(files(changed));
  assert.equal(result.state, "INVALID"); assert.equal(result.issues[0]?.code, "hashMismatch");
  assert.equal(result.issues[0]?.file, "buildable-area.geojson");
});

for (const target of ["site", "status", "search", "candidate", "spatial"]) {
  test(`P12-WEB-09/10/11 reference and status integrity ${target}`, async () => {
    const changed = structuredClone(bytes);
    if (target === "site" || target === "status") {
      const value = document(changed, "buildable-area.geojson");
      if (target === "site") value.properties.siteReference = "sha256:" + "0".repeat(64);
      else value.properties.sourceStatus = "assumed";
      setDocument(changed, "buildable-area.geojson", value); rehash(changed, "buildable-area.geojson");
    } else {
      const value = document(changed, "search-result.json");
      if (target === "search") value.inputReferences.buildableArea = "sha256:" + "0".repeat(64);
      else if (target === "candidate") value.rankedCandidates[0].candidate.inputReferences.buildableArea = "sha256:" + "0".repeat(64);
      else value.spatialContext.buildableArea.artifactReference = "sha256:" + "0".repeat(64);
      setDocument(changed, "search-result.json", value); rehash(changed, "search-result.json");
    }
    const result = await validateRunPackage(files(changed));
    assert.equal(result.state, "INVALID"); assert.equal(result.issues[0]?.code, "referenceMismatch");
  });
}

test("P12-WEB-12 authoritative area/status/review win over browser recomputation", () => {
  const value = document(bytes, "search-result.json");
  value.spatialContext.buildableArea.areaM2 = 73.125;
  value.spatialContext.buildableArea.sourceStatus = "assumed";
  value.spatialContext.buildableArea.reviewRequired = false;
  assert.equal(validateSearchJson(JSON.stringify(value)).state, "DISPLAYABLE");
  const html = render(value); assert.ok(html.includes("73.125 m²")); assert.ok(html.includes("assumed"));
  assert.ok(html.includes("No spatial review flag")); assert.ok(!html.includes("REVIEW REQUIRED"));
  value.spatialContext.buildableArea.reviewRequired = true; assert.ok(render(value).includes("REVIEW REQUIRED"));
});

test("P12-WEB-13/14 browser does not calculate containment or legal geometry", async () => {
  const helper = readFileSync(new URL("../src/lib/run-package-validation.ts", import.meta.url), "utf8");
  assert.doesNotMatch(source + helper, /\.covers\(|convexHull|pointInPolygon|turf|shapely|buffer\(0\)|make_valid/);
  const changed = structuredClone(bytes); const value = document(changed, "buildable-area.geojson");
  // Deliberately only structurally valid: Python must reject this, browser never computes containment.
  value.geometry.coordinates[0][1][0] = 100;
  setDocument(changed, "buildable-area.geojson", value); rehash(changed, "buildable-area.geojson");
  const manifest = document(changed, "manifest.json"); const search = document(changed, "search-result.json");
  search.inputReferences.buildableArea = manifest.artifacts.buildableArea.reference;
  search.spatialContext.buildableArea.artifactReference = manifest.artifacts.buildableArea.reference;
  search.spatialContext.buildableArea.geometry = value.geometry;
  for (const entry of search.rankedCandidates) entry.candidate.inputReferences.buildableArea = manifest.artifacts.buildableArea.reference;
  setDocument(changed, "search-result.json", search); rehash(changed, "search-result.json");
  assert.equal((await validateRunPackage(files(changed))).state, "DISPLAYABLE");
});

test("P12-WEB-15 actual panel renders all three exact disclaimers", () => {
  const html = render();
  for (const notice of ["The supplied buildable area is an explicit footprint domain.",
    "SDG did not derive this geometry from setback or slope regulations.", "This does not prove regulatory compliance."]) assert.ok(html.includes(notice));
});

test("P12-WEB-16 SVG uses supplied outlines only, including both viewport extents", () => {
  const model = toSearchViewModel(document(bytes, "search-result.json")); assert.equal(model.schemaVersion, "0.5");
  if (model.schemaVersion !== "0.5") return;
  const coordinates = model.spatialContext.buildableArea.geometry.coordinates;
  const original = JSON.stringify(coordinates);
  const preview = footprintPreview(model.candidates[0], coordinates);
  assert.ok(preview.available);
  if (preview.available) {
    assert.equal(preview.buildablePoints, coordinates[0].map(([x, y]) => `${x},${-y}`).join(" "));
    assert.equal(preview.points, model.candidates[0].footprint[0].map(([x, y]) => `${x},${-y}`).join(" "));
  }
  assert.equal(JSON.stringify(coordinates), original);
  const viewer = readFileSync(new URL("../src/components/search-result-viewer.tsx", import.meta.url), "utf8");
  assert.ok(viewer.includes('className="buildable-outline"')); assert.ok(viewer.includes('className="candidate-footprint"'));
});

test("P12-WEB-17 Clear aborts pending buildable read without late handoff", async () => {
  const controller = new AbortController();
  const selected = files(bytes).map((file) => file.name !== "buildable-area.geojson" ? file : {
    name: file.name, size: file.size, arrayBuffer: async () => { controller.abort(); return file.arrayBuffer(); },
  });
  const result = await validateRunPackage(selected, controller.signal);
  assert.equal(result.state, "INVALID"); assert.equal(result.issues[0]?.code, "cancelled");
  const viewer = readFileSync(new URL("../src/components/search-result-viewer.tsx", import.meta.url), "utf8");
  assert.equal((viewer.match(/<BuildableAreaPanel model=\{model\}/g) ?? []).length, 1);
  assert.ok(viewer.includes('result?.state === "DISPLAYABLE" && model'));
  assert.ok(viewer.includes("setResult(null)")); assert.ok(viewer.includes("request.current === current && !controller.signal.aborted"));
});

test("P12-WEB-18 responsive spatial layout contains long metadata", () => {
  const css = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");
  assert.ok(css.includes(".buildable-facts { grid-template-columns: 1fr; }"));
  assert.ok(css.includes(".buildable-facts dd { margin: 4px 0 0; overflow-wrap: anywhere; }"));
  assert.ok(css.includes("stroke-dasharray: 6 4"));
});

test("Project0.4 spatial LLM review is isolated from unchanged legacy policy", () => {
  const value = structuredClone(projectSample); value.site.area.status = "official_verified";
  for (const name of ["buildingCoverageRatio", "floorAreaRatio", "heightLimit"] as const) value.zoning[name].status = "official_verified";
  assert.equal(validateJson(JSON.stringify(value)).outcome, "VALID");
  for (const status of ["llm_researched", "assumed", "unknown", "review_required"]) {
    value.spatialConstraints.buildableArea.status = status;
    assert.equal(validateJson(JSON.stringify(value)).outcome, "REVIEW_REQUIRED");
  }
});
