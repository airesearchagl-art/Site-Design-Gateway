/** Resource screening only: JSON.parse remains responsible for JSON grammar.
 * Count value occurrences (including overwritten duplicate members), not keys.
 * The stack holds only container kinds/key context, at most maxDepth + 1 entries.
 */
export function searchTextWithinResources(text: string, maxDepth: number, maxNodes: number): boolean {
  const stack: ("array" | "key" | "value")[] = [];
  let nodes = 0;
  let quoted = false;
  let escaped = false;
  let atom = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (quoted) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === '"') quoted = false;
      continue;
    }
    if (char === " " || char === "\t" || char === "\r" || char === "\n") {
      atom = false;
      continue;
    }
    if (char === "]" || char === "}") {
      stack.pop();
      atom = false;
      continue;
    }
    if (char === "," || char === ":") {
      if (stack.length && stack[stack.length - 1] !== "array") {
        stack[stack.length - 1] = char === ":" ? "value" : "key";
      }
      atom = false;
      continue;
    }
    if (char === '"') {
      quoted = true;
      atom = false;
      if (stack[stack.length - 1] === "key") continue;
    } else if (char !== "[" && char !== "{") {
      if (atom) continue;
      atom = true;
    } else {
      atom = false;
    }

    nodes += 1;
    // Root value is depth 0; every child value adds one container level.
    if (nodes > maxNodes || stack.length > maxDepth) return false;
    if (char === "[" || char === "{") stack.push(char === "[" ? "array" : "key");
  }
  return true;
}
