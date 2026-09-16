import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import test from "node:test";
import { createElement, type ComponentType } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";
import projectSample from "../../../cases/example-urban-office/project-far-stack.json" with { type: "json" };
import { validateJson } from "../src/lib/validation.ts";
import { validateSearchJson, type SearchResultDocument, type FloorAreaRatioContext } from "../src/lib/search-validation.ts";
import { toSearchViewModel, type SearchViewModel } from "../src/lib/search-view.ts";
import { FAR_MINIMUM_NOTICE, FAR_LEGAL_NOTICE, farStackDisplay } from "../src/lib/far-display.ts";
import { validateRunPackage } from "../src/lib/run-package-validation.ts";
import { canonicalPackage, document, files, packageBytes, rehash, setDocument } from "./package-fixture.ts";

const bytes = canonicalPackage(["4","5","6","7","8"], projectSample);
const zeroProject = structuredClone(projectSample);
zeroProject.zoning.additionalFloorAreaRatioCaps[0].value = 0;
const zero = canonicalPackage(["4","5"], zeroProject);
const tieProject = structuredClone(projectSample);
tieProject.zoning.additionalFloorAreaRatioCaps[0].value = 600;
const tie = canonicalPackage(["4"], tieProject);

const file = fileURLToPath(new URL("../src/components/far-stack-panel.tsx", import.meta.url));
const require = createRequire(import.meta.url);
const source = readFileSync(file, "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, jsx: ts.JsxEmit.ReactJSX },
}).outputText.replace(/from "([^"]+)"/g, (_, specifier: string) => {
  const target = specifier.startsWith(".") ? resolve(dirname(file), specifier) : require.resolve(specifier);
  return `from ${JSON.stringify(pathToFileURL(target).href)}`;
});
const { FarStackPanel } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`) as {
  FarStackPanel: ComponentType<{model: SearchViewModel}>;
};
function model(data = document(bytes,"search-result.json")) { return toSearchViewModel(data as SearchResultDocument); }
function render(data = document(bytes,"search-result.json")) { return renderToStaticMarkup(createElement(FarStackPanel,{model:model(data)})); }

test("P10-WEB-01/04/05/06/07 Search v0.3 displays canonical FAR stack and exact statuses", () => {
  const data = document(bytes,"search-result.json");
  assert.equal(validateSearchJson(JSON.stringify(data)).state,"DISPLAYABLE");
  const html = render(data);
  for (const text of ["Base FAR", "Additional FAR caps", "600.0%", "400.0%", "road-width-cap", "road_width_derived", "user_provided",
    "Effective FAR cap", "Effective cap source ID(s)", "Effective max GFA cap", "800 m²"]) assert.ok(html.includes(text),text);
  const before = JSON.stringify(data);
  render(data);
  assert.equal(JSON.stringify(data),before);
});

test("P10-WEB-02/03 direct legacy Search routes retain interpretation without inferred FAR", () => {
  const data = document(packageBytes(),"search-result.json");
  for (const version of ["0.2","0.1"]) {
    data.schemaVersion=version;
    if (version === "0.1") delete data.constraintContext;
    assert.equal(validateSearchJson(JSON.stringify(data)).state,"DISPLAYABLE");
    assert.ok(render(data).includes("Unavailable in this Search Result version"));
    assert.ok(!render(data).includes("Effective FAR cap"));
  }
});

test("P10-WEB-08 tie IDs retain authoritative order", () => {
  const data = document(tie,"search-result.json");
  const far = data.constraintContext.floorAreaRatio as FloorAreaRatioContext;
  assert.deepEqual(far.effectiveCapIds,["base-zoning","road-width-cap"]);
  assert.deepEqual(farStackDisplay(far).effectiveIds,far.effectiveCapIds);
  assert.ok(render(data).includes("base-zoning / road-width-cap"));
});

test("P10-WEB-09 zero and UNAVAILABLE context display safely without fabricated caps", () => {
  const data = document(zero,"search-result.json");
  assert.equal(validateSearchJson(JSON.stringify(data)).state,"DISPLAYABLE");
  assert.ok(render(data).includes("0.0%"));
  // Schema-valid display-only context; Python still rejects unknown shared caps for Search execution.
  const far = data.constraintContext.floorAreaRatio;
  far.state="UNAVAILABLE"; far.effectiveCapPercent=null; far.maxTotalFloorAreaM2=null; far.effectiveCapIds=[];
  far.capStack[1].condition.value=null; far.capStack[1].condition.status="unknown"; far.capStack[1].reviewRequired=true; far.reviewRequired=true;
  data.constraintContext.constraintCaps.maxTotalFloorAreaM2=null;
  assert.equal(validateSearchJson(JSON.stringify(data)).state,"DISPLAYABLE");
  assert.ok(render(data).includes("UNAVAILABLE"));
  assert.ok(render(data).includes("Unavailable"));
  assert.ok(!render(data).includes("null%"));
});

test("P10-WEB-10 authoritative values win over browser min, hardcode, tie inference and sort", () => {
  const data = document(bytes,"search-result.json");
  const far = data.constraintContext.floorAreaRatio as FloorAreaRatioContext;
  // Deliberately not Python-semantic-valid: Web must display, not recompute, these fields.
  far.effectiveCapPercent=237.25; far.effectiveCapIds=["z-source","a-source"];
  far.maxTotalFloorAreaM2=474.5;
  assert.equal(validateSearchJson(JSON.stringify(data)).state,"DISPLAYABLE");
  const display = farStackDisplay(far);
  assert.equal(display.effective,"237.3%");
  assert.equal(display.maxGfa,"474.5");
  assert.deepEqual(display.effectiveIds,["z-source","a-source"]);
  assert.ok(render(data).includes("237.3%"));
  assert.ok(render(data).includes("z-source / a-source"));
  const helper = readFileSync(new URL("../src/lib/far-display.ts",import.meta.url),"utf8");
  assert.doesNotMatch(helper+source,/Math\.(?:min|max)|\.sort\(|\.toSorted\(|\.reduce\(/);
});

test("P10-WEB-11 real FAR panel renders the legal boundary disclaimer", () => {
  const html = render();
  assert.ok(html.includes(FAR_MINIMUM_NOTICE));
  assert.ok(html.includes(FAR_LEGAL_NOTICE));
  assert.equal(FAR_LEGAL_NOTICE,"It does not identify the governing legal rule or prove regulatory compliance.");
  assert.ok(html.includes("法的な支配規定の判定は行いません"));
});

for (const [version,sourceBytes] of [["sdg-run-package-v0.1",packageBytes()],["sdg-run-package-v0.2",bytes]] as const) {
  test(`P10-WEB-12/13 package ${version} intake uses its own matrix`, async () => {
    for (const root of [undefined,"SDG_Run"]) {
      const result = await validateRunPackage(files(sourceBytes,root));
      assert.equal(result.state,"DISPLAYABLE");
      if (result.state === "DISPLAYABLE") assert.equal(result.packageVersion,version);
    }
  });
}

for (const name of ["manifest.json","project.json","site.geojson","constraints.json","search-result.json"] as const) {
  test(`P10-WEB-14 version/artifact mismatch ${name} rejects`, async () => {
    const changed = structuredClone(bytes);
    const value = document(changed,name);
    value.schemaVersion = name === "site.geojson" ? "0.2" : "0.1";
    setDocument(changed,name,value);
    if (name !== "manifest.json") rehash(changed,name,true);
    const result = await validateRunPackage(files(changed));
    assert.equal(result.state,"INVALID");
    assert.equal(result.issues[0]?.code,"schema");
  });
}

test("package versions cannot accept each other's entire artifact collection", async () => {
  for (const [target,other] of [[structuredClone(bytes),packageBytes()],[packageBytes(),bytes]]) {
    const manifest = document(target,"manifest.json");
    const alternate = document(other,"manifest.json");
    manifest.artifacts=alternate.artifacts;
    for (const name of ["project.json","site.geojson","constraints.json","search-result.json"] as const) target[name]=other[name];
    setDocument(target,"manifest.json",manifest);
    assert.equal((await validateRunPackage(files(target))).state,"INVALID");
  }
});

test("Project v0.2 explicit stack, structural IDs and separate LLM review policy", () => {
  const value = structuredClone(projectSample);
  value.site.area.status="official_verified";
  value.zoning.buildingCoverageRatio.status="official_verified";
  value.zoning.floorAreaRatio.status="official_verified";
  value.zoning.heightLimit.status="official_verified";
  assert.equal(validateJson(JSON.stringify(value)).outcome,"VALID");
  value.zoning.additionalFloorAreaRatioCaps[0].status="llm_researched";
  assert.equal(validateJson(JSON.stringify(value)).outcome,"REVIEW_REQUIRED");
  value.zoning.additionalFloorAreaRatioCaps.push({...value.zoning.additionalFloorAreaRatioCaps[0],value:300});
  assert.equal(validateJson(JSON.stringify(value)).outcome,"INVALID");
});

test("P10-WEB-15 FAR panel is part of the existing result state removed by Clear", () => {
  const viewer = readFileSync(new URL("../src/components/search-result-viewer.tsx",import.meta.url),"utf8");
  assert.equal((viewer.match(/<FarStackPanel model=\{model\}/g)??[]).length,1);
  assert.ok(viewer.includes('result?.state === "DISPLAYABLE" && model'));
  assert.ok(viewer.includes("setResult(null)"));
});

test("P10-WEB-16 FAR panel has controlled table overflow and stacked mobile metrics", () => {
  const css=readFileSync(new URL("../src/app/globals.css",import.meta.url),"utf8");
  assert.ok(source.includes('className="table-scroll far-table"'));
  assert.ok(css.includes(".far-effective { grid-template-columns: 1fr; }"));
  assert.ok(css.includes("overflow-wrap: anywhere"));
});
