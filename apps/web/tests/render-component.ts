/** Render real UI modules using the repository's existing React/TypeScript tooling. */
import { existsSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { createElement, type ComponentType } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";

const require = createRequire(import.meta.url);
const modules = new Map<string,string>();
function moduleUrl(file: string): string {
  const cached = modules.get(file); if (cached) return cached;
  if (!file.endsWith(".tsx")) return pathToFileURL(file).href;
  const compiled = ts.transpileModule(readFileSync(file,"utf8"), { compilerOptions: { module: ts.ModuleKind.ESNext, jsx: ts.JsxEmit.ReactJSX } }).outputText
    .replace(/from "([^"]+)"/g, (_,specifier:string) => {
      let target = specifier.startsWith(".") ? resolve(dirname(file),specifier) : require.resolve(specifier);
      if (!existsSync(target)) target = [target+".tsx",target+".ts",target+".js"].find(existsSync) ?? target;
      return `from ${JSON.stringify(moduleUrl(target))}`;
    });
  const url = `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`;
  modules.set(file,url); return url;
}
export async function renderComponent<P extends object>(file: string, name: string, props: P): Promise<string> {
  const imported = await import(moduleUrl(resolve(file)));
  return renderToStaticMarkup(createElement(imported[name] as ComponentType<P>,props));
}
/** Remove collapsed disclosures, including nested ones, from server-rendered HTML. */
export function primaryMarkup(html: string): string {
  let depth=0, cursor=0, output="";
  for (const match of html.matchAll(/<\/?details\b[^>]*>/g)) {
    if(depth===0) output+=html.slice(cursor,match.index);
    depth+=match[0].startsWith("</")?-1:1;
    cursor=match.index!+match[0].length;
  }
  return output+html.slice(cursor);
}
