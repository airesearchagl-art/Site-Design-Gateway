import { sharedValidators, uniqueFarCapIds, uniqueHeightCapIds } from "./schema-registry.ts";

export const MAX_JSON_BYTES = 256 * 1024;
const needsReview = new Set(["assumed", "unknown", "review_required"]);

export type SourceStatus = {
  path: string;
  value: number | null;
  unit: string;
  status: string;
};

export type ValidationResult = {
  schema: "PASS" | "FAIL";
  outcome: "VALID" | "INVALID" | "REVIEW_REQUIRED";
  issues: { path: string; message: string }[];
  sources: SourceStatus[];
};

function invalid(message: string): ValidationResult {
  return { schema: "FAIL", outcome: "INVALID", issues: [{ path: "/", message }], sources: [] };
}

function collectSources(value: unknown, path = ""): SourceStatus[] {
  if (value === null || typeof value !== "object") return [];
  const object = value as Record<string, unknown>;
  if (typeof object.status === "string" && typeof object.unit === "string" && "value" in object) {
    return [{ path, status: object.status, unit: object.unit, value: object.value as number | null }];
  }
  return Object.entries(object).flatMap(([key, child]) =>
    collectSources(child, `${path}/${key.replaceAll("~", "~0").replaceAll("/", "~1")}`),
  );
}

export function validateJson(text: string): ValidationResult {
  if (new TextEncoder().encode(text).byteLength > MAX_JSON_BYTES) {
    return invalid("JSONは256 KiB以内にしてください。");
  }
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    // Do not surface engine exceptions: some include fragments of the input.
    return invalid("JSONを解析できません。引用符・カンマ・括弧を確認してください。");
  }
  const pending: { value: unknown; depth: number }[] = [{ value, depth: 0 }];
  while (pending.length > 0) {
    const item = pending.pop()!;
    if (item.depth > 32) return invalid("JSONの入れ子は32階層以内にしてください。");
    if (typeof item.value === "string" && !item.value.isWellFormed()) {
      return invalid("JSONに不正なUnicode文字が含まれています。");
    }
    if (typeof item.value === "number" && !Number.isFinite(item.value)) {
      return invalid("数値は有限の値にしてください。");
    }
    if (item.value !== null && typeof item.value === "object") {
      for (const child of Object.values(item.value)) pending.push({ value: child, depth: item.depth + 1 });
    }
  }
  const version = value !== null && typeof value === "object" && "schemaVersion" in value ? value.schemaVersion : undefined;
  if (version !== "0.1" && version !== "0.2" && version !== "0.3" && version !== "0.4") return invalid("対応するProject schemaVersionを指定してください。");
  const validate = { "0.1": sharedValidators.project, "0.2": sharedValidators.projectV2, "0.3": sharedValidators.projectV3, "0.4": sharedValidators.projectV4 }[version];
  if (!validate(value)) {
    return {
      schema: "FAIL",
      outcome: "INVALID",
      issues: (validate.errors ?? []).map((error) => ({
        path: error.instancePath || "/",
        message: `${error.keyword}: ${error.message ?? "Schemaに適合しません。"}`,
      })),
      sources: [],
    };
  }
  if (!uniqueFarCapIds(value)) return invalid("Additional FAR capのIDが重複しています。");
  if (!uniqueHeightCapIds(value)) return invalid("Additional height capのIDが重複しています。");
  const sources = collectSources(value);
  const spatialStatus = version === "0.4"
    ? (value as { spatialConstraints: { buildableArea: { status: string } } }).spatialConstraints.buildableArea.status
    : undefined;
  const spatialReview = spatialStatus !== undefined && (needsReview.has(spatialStatus) || spatialStatus === "llm_researched");
  return {
    schema: "PASS",
    outcome: spatialReview || sources.some((source) => needsReview.has(source.status) || (version !== "0.1" && source.status === "llm_researched"
      && (source.path === "/zoning/floorAreaRatio" || source.path.startsWith("/zoning/additionalFloorAreaRatioCaps/")
        || ((version === "0.3" || version === "0.4") && (source.path === "/zoning/heightLimit" || source.path.startsWith("/zoning/additionalHeightCaps/")))))) ? "REVIEW_REQUIRED" : "VALID",
    issues: [],
    sources,
  };
}

export async function validateFile(file: Pick<File, "name" | "size" | "arrayBuffer">): Promise<ValidationResult> {
  if (!file.name.toLowerCase().endsWith(".json")) return invalid(".jsonファイルを選択してください。");
  if (file.size > MAX_JSON_BYTES) return invalid("JSONは256 KiB以内にしてください。");
  try {
    // Fatal decoding rejects malformed UTF-8; keep BOM so JSON.parse rejects it,
    // matching the Python UTF-8 JSON boundary instead of silently replacing bytes.
    const text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(await file.arrayBuffer());
    return validateJson(text);
  } catch {
    return invalid("ファイルを読み込めませんでした。もう一度選択してください。");
  }
}
