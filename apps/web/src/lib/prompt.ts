import schema from "../../../../schemas/sdg-project-v0.1.schema.json" with { type: "json" };
import sample from "../../../../cases/example-urban-office/project.json" with { type: "json" };

export const PROJECT_PROMPT = `Site Design Gateway用のProject JSONを1つ生成してください。
Markdownや解説は含めず、次のJSON Schemaに適合するJSONだけを返してください。
まず以下の架空のsynthetic sampleを使って形式を確認します。実案件の名称・住所・図面は使いません。
数値の単位と出典statusを保持してください。LLMが調べた値はllm_researched、仮定はassumedです。
根拠がない値をofficial_verifiedにしないでください。unknownの値はnullで表現できます。
JSON Schema適合は法規適合の確認ではありません。定義外のGeometryや条件を追加しないでください。

JSON Schema（正本）:
${JSON.stringify(schema, null, 2)}

Synthetic sample:
${JSON.stringify(sample, null, 2)}`;
