import Ajv2020 from "ajv/dist/2020.js";
import projectSchema from "../../../../schemas/sdg-project-v0.1.schema.json" with { type: "json" };
import geometrySchema from "../../../../schemas/sdg-site-geometry-v0.1.schema.json" with { type: "json" };
import constraintSchema from "../../../../schemas/sdg-constraint-result-v0.1.schema.json" with { type: "json" };
import massingSchema from "../../../../schemas/sdg-massing-candidate-v0.1.schema.json" with { type: "json" };
import searchSchema from "../../../../schemas/sdg-search-result-v0.1.schema.json" with { type: "json" };
import searchSchemaV2 from "../../../../schemas/sdg-search-result-v0.2.schema.json" with { type: "json" };
import manifestSchema from "../../../../schemas/sdg-run-manifest-v0.1.schema.json" with { type: "json" };

// Existing composition inherits object types through $ref/allOf. Preserve the
// established strict options and register canonical files offline, without copies.
const ajv = new Ajv2020({ allErrors: true, strict: true, strictTypes: false, strictTuples: false });
for (const schema of [projectSchema, geometrySchema, constraintSchema, massingSchema, searchSchema, searchSchemaV2, manifestSchema]) {
  ajv.addSchema(schema);
}

export const sharedValidators = {
  project: ajv.getSchema(projectSchema.$id)!,
  geometry: ajv.getSchema(geometrySchema.$id)!,
  constraints: ajv.getSchema(constraintSchema.$id)!,
  searchLegacy: ajv.getSchema(searchSchema.$id)!,
  search: ajv.getSchema(searchSchemaV2.$id)!,
  manifest: ajv.getSchema(manifestSchema.$id)!,
};
