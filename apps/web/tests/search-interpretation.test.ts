import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import test from "node:test";
import { createElement, type ComponentType } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";
import sample from "../../../cases/example-urban-office/search-result.json" with { type: "json" };
import { validateSearchJson, type SearchResultDocument } from "../src/lib/search-validation.ts";
import { toSearchViewModel, findCandidate, type CandidateView, type SearchViewModel } from "../src/lib/search-view.ts";
import { areaBasisDisplay, candidateUsage, constraintUsage, formatMeasure, RANKING_RULES, ROUNDING_NOTICE, USAGE_DISCLAIMER } from "../src/lib/search-display.ts";

// Render the real stateless TSX panels with existing TypeScript/React tooling; no generated files.
const file = fileURLToPath(new URL("../src/components/search-interpretation.tsx", import.meta.url));
const require = createRequire(import.meta.url);
const compiled = ts.transpileModule(readFileSync(file, "utf8"), {
  compilerOptions: { module: ts.ModuleKind.ESNext, jsx: ts.JsxEmit.ReactJSX },
}).outputText.replace(/from "([^"]+)"/g, (_, specifier: string) => {
  const target = specifier.startsWith(".") ? resolve(dirname(file), specifier) : require.resolve(specifier);
  return `from ${JSON.stringify(pathToFileURL(target).href)}`;
});
const panels = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`) as {
  AreaBasisPanel: ComponentType<{ model: SearchViewModel }>;
  ConstraintUsagePanel: ComponentType<{ model: SearchViewModel; selected?: CandidateView }>;
};
const viewer = readFileSync(new URL("../src/components/search-result-viewer.tsx", import.meta.url), "utf8");
function document(): SearchResultDocument { return structuredClone(sample) as SearchResultDocument; }
function model() { return toSearchViewModel(document()); }
function renderBasis(value: SearchViewModel) { return renderToStaticMarkup(createElement(panels.AreaBasisPanel, { model: value })); }
function renderUsage(value: SearchViewModel, selected?: CandidateView) {
  return renderToStaticMarkup(createElement(panels.ConstraintUsagePanel, { model: value, selected }));
}

test("P7-WEB-01 v0.2 context is required and validated offline", () => {
  assert.equal(sample.schemaVersion, "0.2");
  assert.equal(validateSearchJson(JSON.stringify(sample)).state, "DISPLAYABLE");
  const value: Record<string, unknown> = structuredClone(sample);
  delete value.constraintContext;
  assert.equal(validateSearchJson(JSON.stringify(value)).state, "INVALID");
  value.constraintContext = { ...sample.constraintContext, areaBasis: { ...sample.constraintContext.areaBasis, selectedBasis: "invented" } };
  assert.equal(validateSearchJson(JSON.stringify(value)).state, "INVALID");
});

test("P7-WEB-02 legacy v0.1 displays without inferred area basis", () => {
  const value: Record<string, unknown> = structuredClone(sample);
  value.schemaVersion = "0.1";
  delete value.constraintContext;
  const result = validateSearchJson(JSON.stringify(value));
  assert.equal(result.state, "DISPLAYABLE");
  if (result.state !== "DISPLAYABLE") return;
  const legacy = toSearchViewModel(result.value);
  assert.equal(legacy.schemaVersion, "0.1");
  assert.equal(legacy.constraintContext, undefined);
  assert.match(renderBasis(legacy), /Context unavailable in legacy Search Result v0.1/);
  assert.match(renderUsage(legacy, legacy.candidates[0]), /93.3%/);
});

test("P7-WEB-03 selected area basis follows both authoritative basis values", () => {
  for (const [basis, label] of [["declared_project_area", "Declared project area"], ["geometry_area", "Geometry area"]] as const) {
    const value = model();
    value.constraintContext!.areaBasis.selectedBasis = basis;
    assert.equal(areaBasisDisplay(value.constraintContext!.areaBasis).selected, label);
    assert.match(renderBasis(value), new RegExp(`Selected: <strong>${label}</strong>`));
  }
});

test("P7-WEB-04 signed difference and nullable declared area are rendered", () => {
  const value = model();
  const area = value.constraintContext!.areaBasis;
  Object.assign(area, { basisAreaM2: 210, declaredAreaM2: 210, geometryAreaM2: 200, differenceM2: 10 });
  assert.deepEqual(areaBasisDisplay(area), { selected: "Declared project area", basis: "210", declared: "210", geometry: "200", difference: "+10" });
  assert.match(renderBasis(value), /\+10 m²/);
  area.differenceM2 = -10;
  assert.match(renderBasis(value), /-10 m²/);
  area.selectedBasis = "geometry_area";
  area.declaredAreaM2 = area.differenceM2 = null;
  assert.match(renderBasis(value), /Declared area<\/dt><dd>Unavailable/);
  assert.match(renderBasis(value), /Difference<\/dt><dd>Unavailable/);
});

test("P7-WEB-05 each selected candidate changes actual remaining and usage", () => {
  const value = model();
  for (const [index, expected] of [[0, ["1,120", "80", "93.3%"]], [1, ["960", "240", "80.0%"]], [2, ["800", "400", "66.7%"]], [3, ["640", "560", "53.3%"]], [4, ["480", "720", "40.0%"]]] as const) {
    const selected = findCandidate(value, value.candidates[index])!;
    const row = candidateUsage(selected, selected.constraintCaps)[1];
    assert.deepEqual([row.actual, row.remaining, row.percentage], expected);
    assert.equal(row.cap, "1,200");
    const html = renderUsage(value, selected);
    for (const text of expected) assert.ok(html.includes(text));
    assert.ok(html.includes(`Rank ${selected.rank}`));
  }
});

test("P7-WEB-06 usage disclaimer is rendered and no automatic legal or tie badge is emitted", () => {
  const value = model();
  const html = renderUsage(value, value.candidates[0]);
  assert.ok(html.includes(USAGE_DISCLAIMER));
  assert.doesNotMatch(html + viewer, /Binding constraint|Governing constraint|Dominant constraint|Critical constraint|Legal maximum|TIED/);
});

test("P7-WEB-07 full deterministic ranking rule is rendered by the viewer", () => {
  assert.deepEqual(RANKING_RULES, ["GFAが大きい候補から順位が付いています。", "正本のGFAが等しい場合は、階高が低い候補が先になります。", "最後はcandidateReferenceの辞書順で順序を確定します。"]);
  assert.match(viewer, /RANKING_RULES\.map/);
});

test("P7-WEB-08 browser preserves authoritative order even when local GFA disagrees", () => {
  const value = document();
  value.rankedCandidates.reverse();
  value.rankedCandidates[0].grossFloorAreaM2 = 1;
  const before = structuredClone(value);
  assert.deepEqual(toSearchViewModel(value).candidates.map(c => c.rank), [5, 4, 3, 2, 1]);
  assert.deepEqual(value, before);
});

test("P7-WEB-09 deterministic formatting keeps canonical values unchanged", () => {
  const value = model();
  value.candidates[0].footprintAreaM2 = 763.2000000000001;
  const before = structuredClone(value);
  assert.equal(formatMeasure(value.candidates[0].footprintAreaM2), "763.2");
  assert.equal(formatMeasure(1234.56789), "1,234.568");
  assert.equal(formatMeasure(0.0001), "0");
  assert.ok(!renderUsage(value, value.candidates[0]).includes("763.2000000000001"));
  assert.deepEqual(value, before);
  for (const field of ["candidate.floorHeightM", "candidate.heightM", "candidate.footprintAreaM2", "candidate.grossFloorAreaM2", "selected.floorHeightM", "selected.grossFloorAreaM2", "rejection.floorHeightM"]) {
    assert.ok(viewer.includes(`formatMeasure(${field})`), `unformatted ${field}`);
  }
  assert.match(viewer, /\{ROUNDING_NOTICE\}/);
  assert.ok(ROUNDING_NOTICE.includes("Canonical JSONは変更しません"));
});

test("P7-WEB-10 zero accepted retains basis caps and unavailable usage", () => {
  const value = model();
  value.candidates = [];
  const html = renderBasis(value) + renderUsage(value);
  assert.match(html, /Declared project area/);
  assert.match(html, /No candidate selected \/ unavailable/);
  for (const cap of ["160", "1,200", "31"]) assert.ok(html.includes(`<dd>${cap}</dd>`));
  assert.match(html, /Actual<\/dt><dd>Unavailable/);
  assert.doesNotMatch(html, /0\.0%/);
});

test("P7-WEB-11 context panels share the clearable DISPLAYABLE result boundary", () => {
  assert.match(viewer, /function clearResult\(\)[\s\S]*?setResult\(null\)[\s\S]*?setSelection\(null\)/);
  assert.ok(viewer.indexOf('result?.state === "DISPLAYABLE" && model') < viewer.indexOf('<AreaBasisPanel'));
  assert.ok(viewer.indexOf('<ConstraintUsagePanel') < viewer.indexOf('{ROUNDING_NOTICE}'));
});

test("display arithmetic never clamps over-cap values or divides by zero", () => {
  assert.deepEqual(constraintUsage(110, 100), { actual: "110", cap: "100", remaining: "-10", percentage: "110.0%" });
  assert.equal(constraintUsage(1, 0).percentage, "Unavailable");
  assert.equal(constraintUsage(1e308, 1e-308).percentage, "Unavailable");
  assert.equal(formatMeasure(Infinity), "Unavailable");
});
