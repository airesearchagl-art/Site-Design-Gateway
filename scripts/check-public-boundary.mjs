// Public release gate: report categories/counts only, never matching input values.
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";

const files = [...new Set(execFileSync("git", ["ls-files", "-z", "--cached", "--others", "--exclude-standard"], { encoding: "utf8" }).split("\0").filter(Boolean))];
const caseMarkers = [
  ["Kita", "-Aoyama"].join(""), ["Kita", "aoyama"].join(""),
  ["北", "青山"].join(""), ["Minato", "-ku"].join(""), ["港", "区"].join(""),
];
const patterns = [
  ["identifying-local-path", /[A-Za-z]:[\\/]Users[\\/][^\s/\\]+|\/(?:Users|home)\/[A-Za-z0-9_.-]+/],
  ["private-key", /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/],
  ["credential-shape", /\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b/],
  ["signed-url", /[?&](?:X-Amz-Signature|X-Goog-Signature|sig)=[A-Za-z0-9%+/]{12,}/i],
];
const failures = new Map();
const fail = (category) => failures.set(category, (failures.get(category) ?? 0) + 1);
const syntheticGeometry = new Set([
  "cases/example-urban-office/site.dxf", "cases/example-urban-office/site.geojson",
]);

for (const file of files) {
  if (/(^|\/)(runtime-data|uploads|private-data|\.venv|node_modules|\.next|\.cache|local)(\/|$)/.test(file) ||
      /\.(dwg|rvt|ifc|pdf|log)$/i.test(file) ||
      /\.(dxf|geojson)$/i.test(file) && !syntheticGeometry.has(file) || file.endsWith("TASK_PACKET_SNAPSHOT.md") ||
      /(^|\/)\.env(?:\.|$)/.test(file) && !file.endsWith(".env.example")) fail("forbidden-file");
  if (file.startsWith("cases/") && !/^cases\/example-urban-office\/(project\.json|project-far-stack\.json|site\.geojson|site\.dxf|search-result\.json|README\.md)$/.test(file)) fail("non-synthetic-fixture-path");
  const text = readFileSync(file, "utf8");
  if (file.endsWith(".env.example") && text.split(/\r?\n/).some((line) => line.trim() && !line.trimStart().startsWith("#"))) fail("env-example-value");
  for (const [name, pattern] of patterns) if (pattern.test(text)) fail(name);
  if (caseMarkers.some((marker) => text.toLowerCase().includes(marker.toLowerCase()))) fail("project-specific-marker");
}

if (failures.size) {
  for (const [category, count] of failures) console.error(`FAIL ${category}: ${count}`);
  process.exitCode = 1;
} else {
  console.log(`PASS public boundary scan: ${files.length} tracked/public-candidate files; no flagged content.`);
}
