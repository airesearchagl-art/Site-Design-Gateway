import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const viewer = readFileSync(new URL("../src/components/search-result-viewer.tsx", import.meta.url), "utf8");
const summary = readFileSync(new URL("../src/components/package-check-summary.tsx", import.meta.url), "utf8");
const css = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");

test("folder progressive enhancement and standard five-file fallback are both available", () => {
  assert.ok(viewer.includes("SDG Run Packageを選択"));
  assert.ok(viewer.includes('webkitdirectory: ""'));
  assert.ok(viewer.includes("5ファイル同時選択"));
  assert.match(viewer, /id="run-package-files" type="file" multiple/);
  assert.ok(viewer.includes("Array.from(event.target.files ?? [])"));
});

test("Python remains authoritative and browser integrity claims are limited", () => {
  assert.ok(summary.includes("Package integrity and shared-schema checks passed in this browser."));
  assert.ok(summary.includes("Python <code>bve.run verify</code> remains the authoritative semantic verifier."));
  assert.ok(summary.includes("署名や作成者認証"));
  assert.ok(summary.includes("D04 OPEN"));
  assert.ok(summary.includes("local Python verifyでは有効でも、Webでは表示できない"));
});

test("P9-WEB-25 package hands the existing validation result to the same Viewer", () => {
  assert.ok(viewer.includes('if (next.state === "DISPLAYABLE") show(next.search)'));
  assert.equal((viewer.match(/<AreaBasisPanel /g) ?? []).length, 1);
  assert.equal((viewer.match(/<ConstraintUsagePanel /g) ?? []).length, 1);
  assert.ok(viewer.includes("toSearchViewModel(result.value)"));
  assert.ok(!summary.includes("toSearchViewModel"));
});

test("P9-WEB-29 Clear drops package/Search state and invalidates pending work", () => {
  const clear = viewer.slice(viewer.indexOf("function clearResult()"), viewer.indexOf("async function selectPackage"));
  for (const expression of ["request.current += 1", "resetPackage()", "setLoading(false)", "setResult(null)", "setSelection(null)", 'fileInput.current.value = ""']) {
    assert.ok(clear.includes(expression));
  }
  const reset = viewer.slice(viewer.indexOf("function resetPackage()"), viewer.indexOf("function show("));
  for (const expression of ["packageRequest.current?.abort()", "packageRequest.current = null", "setPackageResult(null)", "setPackageLoading(false)",
    'directoryInput.current.value = ""', 'packageInput.current.value = ""']) assert.ok(reset.includes(expression));
  assert.ok(viewer.includes("request.current === current && !controller.signal.aborted"));
});

test("P9-WEB-30 package controls and summary can stack without root overflow", () => {
  assert.ok(css.includes(".package-controls { flex-direction: column; }"));
  assert.ok(css.includes(".package-facts { grid-template-columns: 1fr; }"));
  assert.ok(css.includes(".package-intake p { overflow-wrap: anywhere; }"));
  assert.ok(css.includes("html, body { max-width: 100%; overflow-x: clip; }"));
});
