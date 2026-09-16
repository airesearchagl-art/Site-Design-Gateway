"""Repository contracts with an explicit offline Project reference registry."""
from functools import lru_cache
import json

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .validation import SCHEMA_PATH, _validator


@lru_cache(maxsize=11)
def schema_validator(kind: str) -> Draft202012Validator:
    project = _validator()
    if kind == "project":
        return project
    versioned = {
        "project_v2": ("sdg-project-v0.2.schema.json", ()),
        "constraints_v2": ("sdg-constraint-result-v0.2.schema.json", ("constraints", "project_v2")),
        "search_v3": ("sdg-search-result-v0.3.schema.json",
                      ("geometry", "constraints", "massing", "search_legacy", "project_v2", "constraints_v2")),
        "run_v2": ("sdg-run-manifest-v0.2.schema.json",
                   ("geometry", "constraints", "massing", "search_legacy", "run")),
    }
    if kind in versioned:
        filename, dependencies = versioned[kind]
        schema = json.loads((SCHEMA_PATH.parent / filename).read_bytes())
        Draft202012Validator.check_schema(schema)
        registry = Registry().with_resource(project.schema["$id"], Resource.from_contents(project.schema))
        for dependency in dependencies:
            contract = schema_validator(dependency).schema
            registry = registry.with_resource(contract["$id"], Resource.from_contents(contract))
        return Draft202012Validator(schema, registry=registry)
    filename = {"geometry": "sdg-site-geometry-v0.1.schema.json",
                "constraints": "sdg-constraint-result-v0.1.schema.json",
                "massing": "sdg-massing-candidate-v0.1.schema.json",
                "search_legacy": "sdg-search-result-v0.1.schema.json",
                "search": "sdg-search-result-v0.2.schema.json",
                "run": "sdg-run-manifest-v0.1.schema.json"}[kind]
    schema = json.loads((SCHEMA_PATH.parent / filename).read_bytes())
    Draft202012Validator.check_schema(schema)
    registry = Registry().with_resource(project.schema["$id"], Resource.from_contents(project.schema))
    if kind in ("massing", "search_legacy", "search", "run"):
        dependencies = ("geometry", "constraints")
        if kind in ("search_legacy", "search", "run"):
            dependencies += ("massing",)
        if kind in ("search", "run"):
            dependencies += ("search_legacy",)
        for dependency in dependencies:
            contract = schema_validator(dependency).schema
            registry = registry.with_resource(contract["$id"], Resource.from_contents(contract))
    return Draft202012Validator(schema, registry=registry)
