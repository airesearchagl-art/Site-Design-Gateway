import Ajv2020 from "ajv/dist/2020.js";
import { searchTextWithinResources } from "./search-resource-preflight.ts";
import projectSchema from "../../../../schemas/sdg-project-v0.1.schema.json" with { type: "json" };
import geometrySchema from "../../../../schemas/sdg-site-geometry-v0.1.schema.json" with { type: "json" };
import constraintSchema from "../../../../schemas/sdg-constraint-result-v0.1.schema.json" with { type: "json" };
import massingSchema from "../../../../schemas/sdg-massing-candidate-v0.1.schema.json" with { type: "json" };
import searchSchema from "../../../../schemas/sdg-search-result-v0.1.schema.json" with { type: "json" };
import searchSchemaV2 from "../../../../schemas/sdg-search-result-v0.2.schema.json" with { type: "json" };

export const MAX_SEARCH_BYTES = 8 * 1024 * 1024;
export const MAX_SEARCH_DEPTH = 64;
export const MAX_SEARCH_NODES = 250_000;

// Existing canonical schemas use JSON Schema composition where `properties`
// inherits its object type through $ref/allOf. Keep every other strict check.
const ajv = new Ajv2020({
  allErrors: true,
  strict: true,
  strictTypes: false,
  strictTuples: false,
});
for (const schema of [projectSchema, geometrySchema, constraintSchema, massingSchema, searchSchema, searchSchemaV2]) {
  ajv.addSchema(schema);
}
const validators = { "0.1": ajv.getSchema(searchSchema.$id)!, "0.2": ajv.getSchema(searchSchemaV2.$id)! };

export type SearchIssue = {
  path: string;
  keyword: string;
  message: string;
};

export type ConstraintCaps = {
  maxFootprintAreaM2: number;
  maxTotalFloorAreaM2: number;
  maxHeightM: number;
};

export type AreaBasis = {
  selectedBasis: "declared_project_area" | "geometry_area";
  declaredAreaM2: number | null;
  geometryAreaM2: number;
  differenceM2: number | null;
  basisAreaM2: number;
  provenance: { input: string; reference: string; condition: { value: number | null; unit: "m2"; status: string } }[];
};

export type ConstraintContext = { areaBasis: AreaBasis; constraintCaps: ConstraintCaps };

export type SearchResultDocument = ({ schemaVersion: "0.1"; constraintContext?: never }
  | { schemaVersion: "0.2"; constraintContext: ConstraintContext }) & {
  inputReferences: { project: string; geometry: string; constraints: string };
  search: {
    strategy: "floor_height_sweep_v0.1";
    ranking: "maximize_gross_floor_area_v0.1";
    floorHeightsM: number[];
    floorHeightStatus: "user_provided";
  };
  summary: {
    evaluated: number;
    accepted: number;
    rejected: number;
    hasFeasibleCandidate: boolean;
    reviewRequired: boolean;
  };
  rankedCandidates: RankedCandidateDocument[];
  rejections: { floorHeightM: number; code: "NO_FEASIBLE_MASSING" | "RESOURCE_LIMIT" }[];
};

export type RankedCandidateDocument = {
  rank: number;
  candidateReference: string;
  grossFloorAreaM2: number;
  candidate: {
    constraintCaps: ConstraintCaps;
    generator: { floorHeightM: number };
    candidate: {
      footprint: { type: "Polygon"; coordinates: number[][][] };
      footprintAreaM2: number;
      floorCount: number;
      heightM: number;
      grossFloorAreaM2: number;
      reviewRequired: boolean;
    };
  };
};

export type SearchValidationResult =
  | { state: "DISPLAYABLE"; schema: "PASS"; issues: []; value: SearchResultDocument }
  | { state: "INVALID"; schema: "FAIL"; issues: SearchIssue[] }
  | { state: "VIEWER_LIMIT"; schema: "NOT_CHECKED"; issues: SearchIssue[] };

function failure(state: "INVALID" | "VIEWER_LIMIT", keyword: string, message: string): SearchValidationResult {
  const issues = [{ path: "/", keyword, message }];
  if (state === "INVALID") return { state, schema: "FAIL", issues };
  return { state, schema: "NOT_CHECKED", issues };
}

function inspectResources(value: unknown): SearchValidationResult | null {
  let nodes = 0;

  function visit(item: unknown, depth: number): SearchValidationResult | null {
    nodes += 1;
    if (depth > MAX_SEARCH_DEPTH || nodes > MAX_SEARCH_NODES) {
      return failure("VIEWER_LIMIT", "viewerResource", "表示用JSONの入れ子または要素数が上限を超えています。");
    }
    if (typeof item === "string" && !item.isWellFormed()) {
      return failure("INVALID", "unicode", "JSONに不正なUnicode文字が含まれています。");
    }
    if (typeof item === "number" && !Number.isFinite(item)) {
      return failure("INVALID", "number", "数値は有限の値にしてください。");
    }
    if (Array.isArray(item)) {
      for (let index = 0; index < item.length; index += 1) {
        const childFailure = visit(item[index], depth + 1);
        if (childFailure) return childFailure;
      }
    } else if (item !== null && typeof item === "object") {
      for (const key in item) {
        if (!Object.hasOwn(item, key)) continue;
        const child = (item as Record<string, unknown>)[key];
        const childFailure = visit(child, depth + 1);
        if (childFailure) return childFailure;
      }
    }
    return null;
  }

  return visit(value, 0);
}

export function validateSearchJson(text: string): SearchValidationResult {
  if (new TextEncoder().encode(text).byteLength > MAX_SEARCH_BYTES) {
    return failure("VIEWER_LIMIT", "maxBytes", "このファイルは8 MiBのviewer上限を超えています。");
  }
  if (!searchTextWithinResources(text, MAX_SEARCH_DEPTH, MAX_SEARCH_NODES)) {
    return failure("VIEWER_LIMIT", "viewerResource", "表示用JSONの入れ子または要素数が上限を超えています。");
  }
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    return failure("INVALID", "syntax", "JSONを解析できません。引用符・カンマ・括弧を確認してください。");
  }
  const resourceFailure = inspectResources(value);
  if (resourceFailure) return resourceFailure;
  const version = value !== null && typeof value === "object" && "schemaVersion" in value
    ? value.schemaVersion : undefined;
  // Unsupported versions still receive generic schema diagnostics from the legacy contract.
  const validateSearchSchema = version === "0.2" ? validators["0.2"] : validators["0.1"];
  if (!validateSearchSchema(value)) {
    return {
      state: "INVALID",
      schema: "FAIL",
      issues: (validateSearchSchema.errors ?? []).map((error) => ({
        path: error.instancePath || "/",
        keyword: error.keyword,
        message: "Search Result Schemaに適合しません。",
      })),
    };
  }
  return { state: "DISPLAYABLE", schema: "PASS", issues: [], value: value as SearchResultDocument };
}

export async function validateSearchFile(
  file: Pick<File, "name" | "size" | "arrayBuffer">,
): Promise<SearchValidationResult> {
  if (!file.name.toLowerCase().endsWith(".json")) {
    return failure("INVALID", "extension", ".jsonファイルを選択してください。");
  }
  if (file.size > MAX_SEARCH_BYTES) {
    return failure("VIEWER_LIMIT", "maxBytes", "このファイルは8 MiBのviewer上限を超えています。");
  }
  try {
    const bytes = await file.arrayBuffer();
    if (bytes.byteLength > MAX_SEARCH_BYTES) {
      return failure("VIEWER_LIMIT", "maxBytes", "このファイルは8 MiBのviewer上限を超えています。");
    }
    const text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
    return validateSearchJson(text);
  } catch {
    return failure("INVALID", "read", "ファイルを読み込めませんでした。UTF-8のJSONを選択してください。");
  }
}
