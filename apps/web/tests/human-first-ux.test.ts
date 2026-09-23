import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";
import project from "../../../cases/example-urban-office/project.json" with { type: "json" };
import far from "../../../cases/example-urban-office/project-far-stack.json" with { type: "json" };
import height from "../../../cases/example-urban-office/project-height-stack.json" with { type: "json" };
import spatial from "../../../cases/example-urban-office/project-buildable-area.json" with { type: "json" };
import sample from "../../../cases/example-urban-office/search-result.json" with { type: "json" };
import { candidateName, conditionLabel, SAFETY_NOTICE, statusLabel, TERMS } from "../src/lib/human-labels.ts";
import { validateJson } from "../src/lib/validation.ts";
import { validateSearchJson, type SearchResultDocument } from "../src/lib/search-validation.ts";
import { toSearchViewModel } from "../src/lib/search-view.ts";
import { validateRunPackage } from "../src/lib/run-package-validation.ts";
import { canonicalPackage, document, files } from "./package-fixture.ts";
import { primaryMarkup, renderComponent } from "./render-component.ts";

const source = (relative:string) => readFileSync(new URL(relative,import.meta.url),"utf8");
const render = <P extends object>(name:string,component:string,props:P) => renderComponent(fileURLToPath(new URL("../src/components/"+name+".tsx",import.meta.url)),component,props);
const home=await renderComponent(fileURLToPath(new URL("../src/app/page.tsx",import.meta.url)),"default",{});
const primary=primaryMarkup(home),viewer=source("../src/components/search-result-viewer.tsx"), page=source("../src/app/page.tsx");
const model=()=>toSearchViewModel(structuredClone(sample) as SearchResultDocument);
const conditions=await render("project-conditions","ProjectConditions",{result:validateJson(JSON.stringify(project))});
const publicConditions=primaryMarkup(conditions);

test("RC2A-WEB-01 human-first hero and three primary entry actions",()=>{
  for(const text of ["敷地条件から、","初期ボリュームを比較","サンプルで試す","自分の検討結果を開く","自分の案件を準備する"]) assert.ok(primary.includes(text));
  assert.match(primary,/aria-label="検討の始め方"/);
});
test("RC2A-WEB-02 Project JSON is not the primary heading",()=>assert.doesNotMatch(primary,/Create Project JSON|Upload Project JSON|PHASE 12/));
test("RC2A-WEB-03 result heading explains the architect workflow",()=>{assert.ok(primary.includes("ボリューム案を比較"));assert.doesNotMatch(primary,/Review Search Result|DISPLAYABLE|Schema PASS/);});
test("RC2A-WEB-04 prompt remains unchanged in a collapsed secondary area",()=>{assert.ok(home.includes("AIを使って入力データを準備する"));assert.ok(home.includes('id="project-prompt"'));assert.ok(!primary.includes('id="project-prompt"'));assert.doesNotMatch(home,/<details[^>]*\sopen(?:[=>\s])/);});
test("RC2A-WEB-05 project conditions use architectural labels and units",()=>{for(const text of ["敷地面積","建ぺい率","容積率","高さ制限","200 m²","80 %"])assert.ok(publicConditions.includes(text));assert.equal(conditionLabel("/zoning/additionalHeightCaps/1"),"追加の高さ制限 2");});
test("RC2A-WEB-06 raw condition paths stay in technical details",()=>{assert.ok(conditions.includes("/zoning/floorAreaRatio"));assert.doesNotMatch(publicConditions,/\/zoning\/|\/site\//);assert.equal(conditionLabel("/unrecognized/private-key"),"その他の入力条件");});
test("RC2A-WEB-07 all seven status codes have exact human labels without promotion",()=>{
  const expected={official_verified:"公式資料で確認済み",user_provided:"ユーザー入力",drawing_derived:"図面から取得",llm_researched:"AI調査・公式未確認",assumed:"仮定・要確認",unknown:"未確認",review_required:"要確認"};
  for(const [code,label] of Object.entries(expected))assert.equal(statusLabel(code),label);
  assert.ok(publicConditions.includes("AI調査・公式未確認"));assert.doesNotMatch(publicConditions,/>\s*(assumed|llm_researched|user_provided)\s*</);
});
test("RC2A-WEB-08 comparison axis explicitly identifies floor height",async()=>{const html=await render("candidate-comparison","ComparisonExplanation",{model:model()});assert.match(html,/比較条件<\/dt><dd>想定階高/);});
test("RC2A-WEB-09 values use all authoritative search inputs in original order",async()=>{
  const data=structuredClone(sample) as SearchResultDocument;data.search.floorHeightsM=[8.125,3.5,41];const before=structuredClone(data);
  const value=toSearchViewModel(data);assert.deepEqual(value.floorHeightsM,[8.125,3.5,41]);
  const html=await render("candidate-comparison","ComparisonExplanation",{model:value});assert.ok(html.includes("8.125 / 3.5 / 41.0 m"));
  assert.deepEqual(data,before);value.floorHeightsM[0]=99;assert.deepEqual(data,before);
});
test("RC2A-WEB-10 ordering is explained without a local tie or sort",async()=>{const html=await render("candidate-comparison","ComparisonExplanation",{model:model()});assert.ok(html.includes("延床面積が大きい順"));assert.ok(html.includes("同じ延床面積の場合は想定階高が低い順"));assert.doesNotMatch(source("../src/components/candidate-comparison.tsx"),/\.sort\(|\.toSorted\(|Math\.min/);});
test("RC2A-WEB-11 candidate names cover A-Z-AA without changing ranks",()=>{assert.deepEqual([1,2,3,26,27,64].map(candidateName),["案 A","案 B","案 C","案 Z","案 AA","案 BL"]);assert.ok(viewer.includes('candidateName(candidate.rank) + "（想定階高 "'));});
test("RC2A-WEB-12 table columns are Japanese architectural measures",()=>{for(const text of ["案","想定階高","階数","建物高さ","建築面積","延床面積"])assert.ok(viewer.includes('<th scope="col">'+text+'</th>'));});
test("RC2A-WEB-13 selected KPI values follow selection without mutation",async()=>{
  const value=model();const before=structuredClone(value);
  for(const selected of [value.candidates[0],value.candidates[4]]){const html=await render("candidate-comparison","CandidateKpis",{selected});for(const term of [TERMS.grossFloorArea,TERMS.footprint,TERMS.floorCount,TERMS.height,TERMS.floorHeight])assert.ok(html.includes(term));assert.ok(html.includes(candidateName(selected.rank)));assert.ok(html.includes(new Intl.NumberFormat("en-US").format(selected.grossFloorAreaM2)));}
  assert.deepEqual(value,before);
});
test("RC2A-WEB-14 candidate references are rendered only in the collapsed result details",()=>{
  const before=viewer.slice(0,viewer.indexOf('<details className="technical-details result-technical"'));
  assert.doesNotMatch(before,/>\s*candidateReference|\{candidate\.candidateReference\}<\/code>/);
  assert.ok(viewer.includes('<code>{candidate.candidateReference}</code>'));
});
test("RC2A-WEB-15 package technical facts are retained but collapsed",async()=>{
  const bytes=canonicalPackage(["4"],spatial);const result=await validateRunPackage(files(bytes));assert.equal(result.state,"DISPLAYABLE");
  const html=await render("package-check-summary","PackageCheckSummary",{result}),visible=primaryMarkup(html);
  assert.ok(html.includes("SHA-256"));assert.ok(html.includes("sdg-run-package-v0.4"));assert.ok(html.includes("D04 OPEN"));assert.doesNotMatch(visible,/SHA-256|DISPLAYABLE|sdg-run-package|Schema PASS/);
});
test("RC2A-WEB-16 legal and capability boundaries are visible and no disabled fake upload exists",()=>{assert.ok(primary.includes(SAFETY_NOTICE));assert.ok(home.includes("このWeb画面では計算・PDF / DXFの自動解析・住所からの法規取得は行いません"));assert.doesNotMatch(home,/DXF upload|PDF upload/);});
test("RC2A-WEB-17 result folder is the primary intake with collapsed fallback",()=>{assert.ok(home.includes("計算済みの検討結果を開く"));assert.ok(home.includes("検討結果フォルダを選択"));assert.ok(home.includes("うまくフォルダを選べない場合"));assert.ok(viewer.includes('webkitdirectory: ""'));});
test("RC2A-WEB-18 one event loads both existing public artifacts and cancels pending work",()=>{
  assert.ok(page.includes("viewer.current?.loadSample()"));assert.ok(viewer.includes("cases/example-urban-office/project.json"));assert.ok(viewer.includes("cases/example-urban-office/search-result.json"));assert.ok(viewer.includes("<ProjectConditions result={sampleConditions}"));
  const handler=viewer.slice(viewer.indexOf("function loadSample()"),viewer.indexOf("async function selectFile"));for(const statement of ["request.current += 1","resetPackage()","setIsSample(true)","validateSearchJson","focusResults()"])assert.ok(handler.includes(statement));
});
test("RC2A-WEB-19 legacy Search0.1-0.4 keeps the same human comparison",async()=>{
  const legacy=structuredClone(sample) as Record<string,unknown>;legacy.schemaVersion="0.1";delete legacy.constraintContext;
  const values=[legacy,sample,document(canonicalPackage(["4","7"],far),"search-result.json"),document(canonicalPackage(["4","7"],height),"search-result.json")];
  for(const data of values){const result=validateSearchJson(JSON.stringify(data));assert.equal(result.state,"DISPLAYABLE");if(result.state!=="DISPLAYABLE")throw Error();const value=toSearchViewModel(result.value);const html=await render("candidate-comparison","ComparisonExplanation",{model:value});assert.ok(html.includes("想定階高"));assert.equal(value.candidates[0].rank,1);}
});
test("RC2A-WEB-20 Search0.5/Package0.4 retains authoritative spatial display",async()=>{
  const bytes=canonicalPackage(["4","5","6","7","8"],spatial),data=document(bytes,"search-result.json"),before=JSON.stringify(data);assert.equal((await validateRunPackage(files(bytes))).state,"DISPLAYABLE");const value=toSearchViewModel(data);assert.equal(value.schemaVersion,"0.5");const html=await render("buildable-area-panel","BuildableAreaPanel",{model:value});assert.ok(primaryMarkup(html).includes("98 m²"));assert.ok(primaryMarkup(html).includes("図面から取得"));assert.equal(JSON.stringify(data),before);
});
test("RC2A-WEB-21 Clear also drops sample conditions and cancels parent input work",()=>{const clear=viewer.slice(viewer.indexOf("function clearResult()"),viewer.indexOf("async function selectPackage"));for(const statement of ["resetPackage()","setResult(null)","setSelection(null)","setIsSample(false)","onClear()"] )assert.ok(clear.includes(statement));assert.match(page,/function clearProject\(\).*request.current \+= 1/);});
test("RC2A-WEB-22 mobile stylesheet contains actions KPIs disclosures and table overflow",()=>{const css=source("../src/app/globals.css");for(const text of [".entry-actions { grid-template-columns: 1fr;",".kpi-grid { grid-template-columns: 1fr 1fr;","overflow-x: auto; contain: inline-size;","summary:focus-visible"])assert.ok(css.includes(text));});
test("RC2A-WEB-23 recursive privacy guards remain intact",()=>{const guard=source("search-ui-contract.test.ts");for(const token of ["fetch","sendBeacon","localStorage","sessionStorage","indexedDB","CacheStorage","serviceWorker","showSaveFilePicker","console"])assert.ok(guard.includes(token));});
test("RC2A-WEB-24 128MiB wide4/wide6/wide8/deep6 reject before parse",()=>{
  for(const kind of ["wide4","wide6","wide8","deep6"]){const output=execFileSync(process.execPath,["--max-old-space-size=128","--experimental-strip-types",fileURLToPath(new URL("search-resource-probe.ts",import.meta.url)),kind],{encoding:"utf8",timeout:30_000});assert.equal(output.trim(),"PASS");}
});
