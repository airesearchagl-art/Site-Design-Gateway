/** Test-only canonical packages from the public fixture and unchanged Python CLI.
 * No production browser code imports this module. Nothing is persisted in Git.
 */
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { PACKAGE_FILES, type PackageFilename, type SelectedPackageFile } from "../src/lib/run-package-validation.ts";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
export type PackageBytes = Record<PackageFilename, Uint8Array<ArrayBuffer>>;
export const artifactNames = ["project.json", "site.geojson", "constraints.json", "search-result.json"] as const;
const kind = { "project.json": "project", "site.geojson": "geometry", "constraints.json": "constraints", "search-result.json": "search" } as const;

function canonicalPackage(heights: string[]): PackageBytes {
  const temporary = mkdtempSync(join(tmpdir(), "sdg-p9-synthetic-"));
  const output = join(temporary, "package");
  try {
    const python = process.env.SDG_TEST_PYTHON ?? (process.platform === "win32" ? join(ROOT, ".venv/Scripts/python.exe") : "python");
    execFileSync(python, ["-m", "bve.run", "create", "--project", "cases/example-urban-office/project.json",
      "--geometry", "cases/example-urban-office/site.geojson", "--format", "geojson", "--area-basis", "declared_project_area",
      ...heights.flatMap((height) => ["--floor-height-m", height]), "--output", output],
    { cwd: ROOT, env: { ...process.env, PYTHONPATH: join(ROOT, "src"), PYTHONDONTWRITEBYTECODE: "1" }, stdio: "pipe", timeout: 30_000 });
    return Object.fromEntries(PACKAGE_FILES.map((name) => [name, new Uint8Array(readFileSync(join(output, name)))])) as PackageBytes;
  } catch {
    throw new Error("Public synthetic package preparation failed.");
  } finally {
    // Cleanup is restricted to the freshly owned, direct temporary child.
    if (dirname(resolve(temporary)) !== resolve(tmpdir()) || !basename(temporary).startsWith("sdg-p9-synthetic-")) {
      throw new Error("Synthetic temporary boundary failed.");
    }
    rmSync(temporary, { recursive: true, force: true });
  }
}

const canonical = canonicalPackage(["4", "5", "6", "7", "8"]);
const zero = canonicalPackage(["32", "40"]);
export function packageBytes(zeroAccepted = false): PackageBytes { return structuredClone(zeroAccepted ? zero : canonical); }
export function files(bytes: PackageBytes, root?: string): SelectedPackageFile[] {
  return PACKAGE_FILES.map((name) => {
    const file = new File([bytes[name]], name);
    if (root !== undefined) Object.defineProperty(file, "webkitRelativePath", { value: `${root}/${name}` });
    return file;
  });
}
export function document(bytes: PackageBytes, name: PackageFilename) { return JSON.parse(new TextDecoder().decode(bytes[name])); }
export function setDocument(bytes: PackageBytes, name: PackageFilename, value: unknown) {
  bytes[name] = new TextEncoder().encode(JSON.stringify(value));
}
export function sha(bytes: Uint8Array): string { return "sha256:" + createHash("sha256").update(bytes).digest("hex"); }
export function rehash(bytes: PackageBytes, name: typeof artifactNames[number], rebindSearch = false) {
  const manifest = document(bytes, "manifest.json");
  manifest.artifacts[kind[name]].reference = sha(bytes[name]);
  if (name === "constraints.json" && rebindSearch) {
    const search = document(bytes, "search-result.json");
    search.inputReferences.constraints = manifest.artifacts.constraints.reference;
    setDocument(bytes, "search-result.json", search);
    manifest.artifacts.search.reference = sha(bytes["search-result.json"]);
  }
  setDocument(bytes, "manifest.json", manifest);
}
