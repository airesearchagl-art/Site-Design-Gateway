import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import test from "node:test";
import { createElement, type ComponentType } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";
import projectSample from "../../../cases/example-urban-office/project-height-stack.json" with { type: "json" };
import farProject from "../../../cases/example-urban-office/project-far-stack.json" with { type: "json" };
import { validateJson } from "../src/lib/validation.ts";
import { validateSearchJson, type SearchResultDocument, type HeightContext } from "../src/lib/search-validation.ts";
import { toSearchViewModel, type SearchViewModel } from "../src/lib/search-view.ts";
import { heightStackDisplay, HEIGHT_MINIMUM_NOTICE, HEIGHT_LEGAL_NOTICE } from "../src/lib/height-display.ts";
import { farStackDisplay } from "../src/lib/far-display.ts";
import { validateRunPackage } from "../src/lib/run-package-validation.ts";
import { canonicalPackage, document, files, packageBytes, rehash, setDocument } from "./package-fixture.ts";

const bytes=canonicalPackage(["4","5","6","7","8"],projectSample);
const legacyFar=canonicalPackage(["4","5","6","7","8"],farProject);
const zeroProject=structuredClone(projectSample);zeroProject.zoning.additionalHeightCaps[0].value=0;
const zero=canonicalPackage(["4","5"],zeroProject);
const tieProject=structuredClone(projectSample);tieProject.zoning.additionalHeightCaps[0].value=31;
const tie=canonicalPackage(["4"],tieProject);

const file=fileURLToPath(new URL("../src/components/height-stack-panel.tsx",import.meta.url));
const require=createRequire(import.meta.url);
const source=readFileSync(file,"utf8");
const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,jsx:ts.JsxEmit.ReactJSX}}).outputText
  .replace(/from "([^"]+)"/g,(_,specifier:string)=>`from ${JSON.stringify(pathToFileURL(specifier.startsWith(".")?resolve(dirname(file),specifier):require.resolve(specifier)).href)}`);
const {HeightStackPanel}=await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`) as {
  HeightStackPanel:ComponentType<{model:SearchViewModel}>;
};
function render(data=document(bytes,"search-result.json")) {
  return renderToStaticMarkup(createElement(HeightStackPanel,{model:toSearchViewModel(data as SearchResultDocument)}));
}

test("P11-WEB-01/05/06 Search0.4 renders height stack from canonical Python output",()=>{
  const data=document(bytes,"search-result.json");
  assert.equal(validateSearchJson(JSON.stringify(data)).state,"DISPLAYABLE");
  const html=render(data);
  for(const text of ["Base height cap","31 m","Additional scalar height caps","explicit-height-cap","24 m","absolute_height_explicit","user_provided","assumed","REVIEW REQUIRED"]) assert.ok(html.includes(text),text);
  const original=JSON.stringify(data);render(data);assert.equal(JSON.stringify(data),original);
});

for(const version of ["0.1","0.2","0.3"]){
  test(`P11-WEB-02/03/04 legacy Search${version} retains existing context`,()=>{
    const data=document(version==="0.3"?legacyFar:packageBytes(),"search-result.json");
    data.schemaVersion=version;if(version==="0.1")delete data.constraintContext;
    assert.equal(validateSearchJson(JSON.stringify(data)).state,"DISPLAYABLE");
    assert.ok(render(data).includes("Unavailable in this Search Result version"));
    if(version==="0.3")assert.equal(farStackDisplay(data.constraintContext.floorAreaRatio).effective,"400.0%");
  });
}

test("P11-WEB-07/12 authoritative height beats local min, hardcode and sorting",()=>{
  const data=document(bytes,"search-result.json");const h=data.constraintContext.height as HeightContext;
  // Schema-valid only: Web must not claim to repeat Python semantic verification.
  h.effectiveHeightM=17.125;h.maxHeightM=17.125;h.effectiveCapIds=["z-source","a-source"];
  assert.equal(validateSearchJson(JSON.stringify(data)).state,"DISPLAYABLE");
  assert.equal(heightStackDisplay(h).effective,"17.125 m");
  assert.deepEqual(heightStackDisplay(h).effectiveIds,["z-source","a-source"]);
  assert.ok(render(data).includes("17.125 m"));assert.ok(render(data).includes("z-source / a-source"));
  const helper=readFileSync(new URL("../src/lib/height-display.ts",import.meta.url),"utf8");
  assert.doesNotMatch(helper+source,/Math\.(?:min|max)|\.sort\(|\.toSorted\(|\.reduce\(/);
});

test("P11-WEB-08 canonical tie IDs preserve input order",()=>{
  const data=document(tie,"search-result.json");
  assert.deepEqual(data.constraintContext.height.effectiveCapIds,["base-height","explicit-height-cap"]);
  assert.ok(render(data).includes("base-height / explicit-height-cap"));
});

for(const state of ["ABSENT","UNAVAILABLE"]){
  test(`P11-WEB-09/10 ${state} display is safe and never fabricates a numeric cap`,()=>{
    // Python execution rejects these shared states; this tests the read-only schema/display boundary.
    const data=document(zero,"search-result.json");const h=data.constraintContext.height;
    h.state=state;h.effectiveHeightM=null;h.maxHeightM=null;h.effectiveCapIds=[];
    if(state==="ABSENT"){h.capStack=[];h.reviewRequired=false;}
    else{h.capStack[1].condition.value=null;h.capStack[1].condition.status="unknown";h.capStack[1].reviewRequired=true;h.reviewRequired=true;}
    data.constraintContext.constraintCaps.maxHeightM=null;
    assert.equal(validateSearchJson(JSON.stringify(data)).state,"DISPLAYABLE");
    const html=render(data);assert.ok(html.includes(state));assert.ok(html.includes("Unavailable"));assert.ok(!html.includes("null m"));
  });
}

test("P11-WEB-11 zero height remains a known numeric cap",()=>{
  const data=document(zero,"search-result.json");
  assert.equal(validateSearchJson(JSON.stringify(data)).state,"DISPLAYABLE");
  assert.equal(data.summary.accepted,0);assert.equal(data.summary.rejected,2);
  assert.ok(render(data).includes("0 m"));assert.ok(render(data).includes("COMPUTED"));
});

test("P11-WEB-13 real panel renders scalar and spatial/legal disclaimers",()=>{
  const html=render();assert.ok(html.includes(HEIGHT_MINIMUM_NOTICE));assert.ok(html.includes(HEIGHT_LEGAL_NOTICE));
  assert.equal(HEIGHT_MINIMUM_NOTICE,"Effective height cap is the minimum of the explicit scalar height caps supplied to BVE.");
  assert.equal(HEIGHT_LEGAL_NOTICE,"It does not evaluate spatial slope planes, identify the governing legal rule, or prove regulatory compliance.");
});

for(const [version,sourceBytes] of [["0.1",packageBytes()],["0.2",legacyFar],["0.3",bytes]] as const){
  test(`P11-WEB-14/15/16 Package${version} intake`,async()=>{
    for(const root of [undefined,"SDG_Run"]){
      const result=await validateRunPackage(files(sourceBytes,root));
      assert.equal(result.state,"DISPLAYABLE");
      if(result.state==="DISPLAYABLE")assert.equal(result.packageVersion,"sdg-run-package-v"+version);
    }
  });
}

for(const name of ["project.json","site.geojson","constraints.json","search-result.json"] as const){
  test(`P11-WEB-17 Package0.3 rejects mixed artifact version ${name}`,async()=>{
    const changed=structuredClone(bytes);const data=document(changed,name);data.schemaVersion="0.2";
    setDocument(changed,name,data);rehash(changed,name);
    const result=await validateRunPackage(files(changed));assert.equal(result.state,"INVALID");assert.equal(result.issues[0]?.code,"schema");
  });
}

test("package0.3 cannot accept an entire legacy artifact set",async()=>{
  for(const other of [legacyFar,packageBytes()]){
    const changed=structuredClone(bytes);const manifest=document(changed,"manifest.json");manifest.artifacts=document(other,"manifest.json").artifacts;
    for(const name of ["project.json","site.geojson","constraints.json","search-result.json"] as const)changed[name]=other[name];
    setDocument(changed,"manifest.json",manifest);assert.equal((await validateRunPackage(files(changed))).state,"INVALID");
  }
});

test("Project0.3 unique height IDs and isolated LLM review policy",()=>{
  const data=structuredClone(projectSample);data.site.area.status="official_verified";
  for(const name of ["buildingCoverageRatio","floorAreaRatio","heightLimit"] as const)data.zoning[name].status="official_verified";
  assert.equal(validateJson(JSON.stringify(data)).outcome,"VALID");
  data.zoning.additionalHeightCaps[0].status="llm_researched";assert.equal(validateJson(JSON.stringify(data)).outcome,"REVIEW_REQUIRED");
  data.zoning.additionalHeightCaps.push({...data.zoning.additionalHeightCaps[0],value:20});assert.equal(validateJson(JSON.stringify(data)).outcome,"INVALID");
});

test("P11-WEB-18 Clear removes the height panel with the existing result state",()=>{
  const viewer=readFileSync(new URL("../src/components/search-result-viewer.tsx",import.meta.url),"utf8");
  assert.equal((viewer.match(/<HeightStackPanel model=\{model\}/g)??[]).length,1);
  assert.ok(viewer.includes('result?.state === "DISPLAYABLE" && model'));assert.ok(viewer.includes("setResult(null)"));
});

test("P11-WEB-19 height metrics stack on mobile and table overflow is contained",()=>{
  const css=readFileSync(new URL("../src/app/globals.css",import.meta.url),"utf8");
  assert.ok(css.includes(".height-effective { grid-template-columns: 1fr; }"));
  assert.ok(source.includes('className="table-scroll height-table"'));
});
