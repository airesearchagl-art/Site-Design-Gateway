import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const guard = readFileSync(join(dirname(fileURLToPath(import.meta.url)), "search-ui-contract.test.ts"), "utf8");

test("privacy guard explicitly covers every prohibited browser capability", () => {
  for (const token of [
    "fetch",
    "XMLHttpRequest",
    "sendBeacon",
    "localStorage",
    "sessionStorage",
    "indexedDB",
    "caches",
    "CacheStorage",
    "WebSocket",
    "EventSource",
    "console",
    "showSaveFilePicker",
    "createWritable",
    "serviceWorker",
  ]) {
    assert.ok(guard.includes(token), `privacy guard missing ${token}`);
  }
});
