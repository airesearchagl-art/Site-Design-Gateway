import { searchTextWithinResources } from "./search-resource-preflight.ts";
import { sharedValidators } from "./schema-registry.ts";

export const MAX_SEARCH_BYTES = 8 * 1024 * 1024;
export const MAX_SEARCH_DEPTH = 64;
export const MAX_SEARCH_NODES = 250_000;

const validators = { "0.1": sharedValidators.searchLegacy, "0.2": sharedValidators.search, "0.3": sharedValidators.searchV3 };

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

export type ContextCaps = { [K in keyof ConstraintCaps]: number | null };
export type ConstraintContext = { areaBasis: AreaBasis; constraintCaps: ContextCaps };
export type FarCapEntry = {
  id: string; kind: string; input: string; reference: string;
  condition: { value: number | null; unit: "percent"; status: string }; reviewRequired: boolean;
};
export type FloorAreaRatioContext = {
  state: "COMPUTED" | "UNAVAILABLE";
  calculationId: "floor_area_cap_stack_v0.2";
  effectiveCapPercent: number | null; effectiveCapIds: string[]; maxTotalFloorAreaM2: number | null;
  capStack: FarCapEntry[]; reviewRequired: boolean;
};
export type FarConstraintContext = ConstraintContext & { floorAreaRatio: FloorAreaRatioContext };

export type SearchResultDocument = ({ schemaVersion: "0.1"; constraintContext?: never }
  | { schemaVersion: "0.2"; constraintContext: ConstraintContext }
  | { schemaVersion: "0.3"; constraintContext: FarConstraintContext }) & {
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

export function inspectResources(value: unknown): SearchValidationResult | null {
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
  if (version !== "0.1" && version !== "0.2" && version !== "0.3") {
    return failure("INVALID", "schemaVersion", "Search Result Schemaに適合しません。");
  }
  const validateSearchSchema = validators[version];
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
