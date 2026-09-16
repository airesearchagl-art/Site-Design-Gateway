import { sharedValidators, uniqueFarCapIds } from "./schema-registry.ts";
import { searchTextWithinResources } from "./search-resource-preflight.ts";
import {
  inspectResources, MAX_SEARCH_BYTES, MAX_SEARCH_DEPTH, MAX_SEARCH_NODES,
  validateSearchJson, type SearchValidationResult,
} from "./search-validation.ts";

export const PACKAGE_FILES = ["manifest.json", "project.json", "site.geojson", "constraints.json", "search-result.json"] as const;
export type PackageFilename = typeof PACKAGE_FILES[number];
export const PACKAGE_LIMITS: Readonly<Record<PackageFilename, number>> = Object.freeze({
  "manifest.json": 256 * 1024,
  "project.json": 256 * 1024,
  "site.geojson": 4 * 1024 * 1024,
  "constraints.json": 4 * 1024 * 1024,
  "search-result.json": MAX_SEARCH_BYTES,
});
const ARTIFACTS = [
  ["project", "project.json"], ["geometry", "site.geojson"],
  ["constraints", "constraints.json"], ["search", "search-result.json"],
] as const;
type ArtifactKind = typeof ARTIFACTS[number][0];
type PackageVersion = "sdg-run-package-v0.1" | "sdg-run-package-v0.2";
const packageValidators = {
  "sdg-run-package-v0.1": { project: sharedValidators.project, geometry: sharedValidators.geometry,
    constraints: sharedValidators.constraints, search: sharedValidators.search, manifest: sharedValidators.manifest },
  "sdg-run-package-v0.2": { project: sharedValidators.projectV2, geometry: sharedValidators.geometry,
    constraints: sharedValidators.constraintsV2, search: sharedValidators.searchV3, manifest: sharedValidators.manifestV2 },
};
export type SelectedPackageFile = Pick<File, "name" | "size" | "arrayBuffer"> & { webkitRelativePath?: string };
type Manifest = {
  packageVersion: PackageVersion;
  configuration: { areaBasis: "declared_project_area" | "geometry_area"; floorHeightsM: number[] };
  artifacts: Record<ArtifactKind, { path: string; reference: string }>;
};
type ConstraintLinks = { inputReferences: { project: string; geometry: string }; areaBasis: { selectedBasis: string } };
type DisplayableSearch = Extract<SearchValidationResult, { state: "DISPLAYABLE" }>;

const messages = {
  fileSet: "指定された5ファイルだけを、重複なく選択してください。隠しファイルも追加できません。",
  relativePath: "同じfolderの直下にある5ファイルを選択してください。入れ子や複数rootは受け付けません。",
  maxBytes: "このファイルはブラウザの読込上限を超えています。",
  viewerResource: "JSONの入れ子または要素数がブラウザの上限を超えています。",
  read: "ファイルを読み込めませんでした。",
  utf8: "UTF-8のJSONを選択してください。",
  syntax: "JSONを解析できません。",
  value: "JSONに扱えない数値またはUnicode文字が含まれています。",
  schema: "共有Schemaに適合しません。",
  hashMismatch: "ArtifactのSHA-256がmanifestと一致しません。",
  referenceMismatch: "Artifact間の入力参照が一致しません。",
  configurationMismatch: "Area basisまたは階高の設定が一致しません。",
  crypto: "このブラウザではSHA-256の確認を完了できません。",
  cancelled: "読込を取り消しました。",
} as const;
export type PackageIssueCode = keyof typeof messages;
export type PackageIssue = { file: PackageFilename | "package"; code: PackageIssueCode; message: string };
export type PackageValidationResult =
  | { state: "DISPLAYABLE"; packageVersion: PackageVersion; artifactCount: 4; issues: []; search: DisplayableSearch }
  | { state: "INVALID" | "VIEWER_LIMIT"; issues: [PackageIssue] };
type Failure = Exclude<PackageValidationResult, { state: "DISPLAYABLE" }>;

function failure(code: PackageIssueCode, file: PackageIssue["file"] = "package", state: Failure["state"] = "INVALID"): Failure {
  return { state, issues: [{ file, code, message: messages[code] }] };
}

function selectedFileMap(files: readonly SelectedPackageFile[]): Map<PackageFilename, SelectedPackageFile> | Failure {
  const selected = new Map<PackageFilename, SelectedPackageFile>();
  if (files.length !== PACKAGE_FILES.length) return failure("fileSet");
  let root: string | undefined;
  const directoryMode = files.some((file) => Boolean(file.webkitRelativePath));
  for (const file of files) {
    if (!PACKAGE_FILES.includes(file.name as PackageFilename) || selected.has(file.name as PackageFilename)) {
      return failure("fileSet");
    }
    if (directoryMode) {
      const parts = (file.webkitRelativePath ?? "").split("/");
      if (parts.length !== 2 || parts[1] !== file.name || !parts[0] || parts[0] === "." || parts[0] === ".."
          || /[\\:\u0000-\u001f]/.test(parts[0]) || (root !== undefined && root !== parts[0])) {
        return failure("relativePath");
      }
      root = parts[0];
    }
    selected.set(file.name as PackageFilename, file);
  }
  return selected;
}

async function read(file: SelectedPackageFile, name: PackageFilename, signal?: AbortSignal): Promise<
  { bytes: ArrayBuffer; text: string } | Failure
> {
  if (signal?.aborted) return failure("cancelled");
  let bytes: ArrayBuffer;
  try {
    bytes = await file.arrayBuffer();
  } catch {
    return failure("read", name);
  }
  if (signal?.aborted) return failure("cancelled");
  if (bytes.byteLength > PACKAGE_LIMITS[name]) return failure("maxBytes", name, "VIEWER_LIMIT");
  try {
    return { bytes, text: new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes) };
  } catch {
    return failure("utf8", name);
  }
}

function parseArtifact(text: string, name: PackageFilename): { value: unknown } | Failure {
  if (!searchTextWithinResources(text, MAX_SEARCH_DEPTH, MAX_SEARCH_NODES)) {
    return failure("viewerResource", name, "VIEWER_LIMIT");
  }
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    return failure("syntax", name);
  }
  const resource = inspectResources(value);
  if (resource) return resource.state === "VIEWER_LIMIT"
    ? failure("viewerResource", name, "VIEWER_LIMIT") : failure("value", name);
  return { value };
}

export async function validateRunPackage(
  files: readonly SelectedPackageFile[], signal?: AbortSignal,
): Promise<PackageValidationResult> {
  // No selected file, root, raw buffer or parsed non-Search artifact escapes this
  // function. Clear aborts between asynchronous boundaries; pending File reads
  // cannot be synchronously erased, but are discarded without a later handoff.
  try {
    if (signal?.aborted) return failure("cancelled");
    const selected = selectedFileMap(files);
    if (!(selected instanceof Map)) return selected;
    // Preflight every file before reading even the manifest.
    for (const name of PACKAGE_FILES) {
      const size = selected.get(name)!.size;
      if (!Number.isSafeInteger(size) || size < 0) return failure("read", name);
      if (size > PACKAGE_LIMITS[name]) return failure("maxBytes", name, "VIEWER_LIMIT");
    }
    const manifestInput = await read(selected.get("manifest.json")!, "manifest.json", signal);
    if ("state" in manifestInput) return manifestInput;
    const parsed = parseArtifact(manifestInput.text, "manifest.json");
    if ("state" in parsed) return parsed;
    const version = parsed.value !== null && typeof parsed.value === "object" && "packageVersion" in parsed.value
      ? parsed.value.packageVersion : undefined;
    if (version !== "sdg-run-package-v0.1" && version !== "sdg-run-package-v0.2") return failure("schema", "manifest.json");
    const validators = packageValidators[version];
    if (!validators.manifest(parsed.value)) return failure("schema", "manifest.json");
    const manifest = parsed.value as Manifest;
    let constraints: ConstraintLinks | undefined;
    let search: DisplayableSearch | undefined;
    for (const [kind, name] of ARTIFACTS) {
      // Fixed names only: never interpret the manifest path as a traversal target.
      const input = await read(selected.get(name)!, name, signal);
      if ("state" in input) return input;
      if (kind === "search") {
        // This is the existing resource/schema boundary, not a parallel parser.
        const result = validateSearchJson(input.text);
        if (result.state !== "DISPLAYABLE") {
          return result.state === "VIEWER_LIMIT" ? failure("viewerResource", name, "VIEWER_LIMIT") : failure("schema", name);
        }
        if (!validators.search(result.value)) return failure("schema", name);
        search = result;
      } else {
        const artifact = parseArtifact(input.text, name);
        if ("state" in artifact) return artifact;
        if (!validators[kind](artifact.value)) return failure("schema", name);
        if (kind === "project" && !uniqueFarCapIds(artifact.value)) return failure("schema", name);
        if (kind === "constraints") constraints = artifact.value as ConstraintLinks;
      }
      let hash: string;
      try {
        const digest = await globalThis.crypto.subtle.digest("SHA-256", input.bytes);
        hash = "sha256:" + Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
      } catch {
        return failure("crypto", name);
      }
      if (signal?.aborted) return failure("cancelled");
      if (hash !== manifest.artifacts[kind].reference) return failure("hashMismatch", name);
    }
    if (!constraints || !search) return failure("fileSet");
    const refs = manifest.artifacts;
    if (constraints.inputReferences.project !== refs.project.reference
        || constraints.inputReferences.geometry !== refs.geometry.reference) return failure("referenceMismatch", "constraints.json");
    if (search.value.inputReferences.project !== refs.project.reference
        || search.value.inputReferences.geometry !== refs.geometry.reference
        || search.value.inputReferences.constraints !== refs.constraints.reference) return failure("referenceMismatch", "search-result.json");
    if (manifest.configuration.areaBasis !== constraints.areaBasis.selectedBasis) return failure("configurationMismatch");
    const heights = search.value.search.floorHeightsM;
    if (manifest.configuration.floorHeightsM.length !== heights.length
        || !manifest.configuration.floorHeightsM.every((height, index) => height === heights[index])) {
      return failure("configurationMismatch");
    }
    return { state: "DISPLAYABLE", packageVersion: manifest.packageVersion, artifactCount: 4, issues: [], search };
  } catch {
    return failure("read");
  }
}
