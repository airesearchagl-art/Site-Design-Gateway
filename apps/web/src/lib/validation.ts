import Ajv2020 from "ajv/dist/2020.js";
import schema from "../../../../schemas/sdg-project-v0.1.schema.json" with { type: "json" };

export const MAX_JSON_BYTES = 256 * 1024;
const validate = new Ajv2020({ allErrors: true, strict: true }).compile(schema);
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
    if (typeof item.value === "number" && !Number.isFinite(item.value)) {
      return invalid("数値は有限の値にしてください。");
    }
    if (item.value !== null && typeof item.value === "object") {
      for (const child of Object.values(item.value)) pending.push({ value: child, depth: item.depth + 1 });
    }
  }
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
  const sources = collectSources(value);
  return {
    schema: "PASS",
    outcome: sources.some((source) => needsReview.has(source.status)) ? "REVIEW_REQUIRED" : "VALID",
    issues: [],
    sources,
  };
}

export async function validateFile(file: Pick<File, "name" | "size" | "text">): Promise<ValidationResult> {
  if (!file.name.toLowerCase().endsWith(".json")) return invalid(".jsonファイルを選択してください。");
  if (file.size > MAX_JSON_BYTES) return invalid("JSONは256 KiB以内にしてください。");
  try {
    return validateJson(await file.text());
  } catch {
    return invalid("ファイルを読み込めませんでした。もう一度選択してください。");
  }
}
