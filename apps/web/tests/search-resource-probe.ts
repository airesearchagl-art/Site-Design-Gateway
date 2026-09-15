import { validateSearchJson } from "../src/lib/search-validation.ts";

const wideInput = `[${"0,".repeat(2_000_000)}0]`;
const result = validateSearchJson(wideInput);

if (result.state !== "VIEWER_LIMIT" || result.schema !== "NOT_CHECKED") {
  throw new Error("wide input did not reach the viewer resource limit");
}

process.stdout.write("PASS\n");
