"""Repository contracts with an explicit offline Project reference registry."""
from functools import lru_cache
import json

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .validation import SCHEMA_PATH, _validator


@lru_cache(maxsize=6)
def schema_validator(kind: str) -> Draft202012Validator:
    project = _validator()
    if kind == "project":
        return project
    filename = {"geometry": "sdg-site-geometry-v0.1.schema.json",
                "constraints": "sdg-constraint-result-v0.1.schema.json",
                "massing": "sdg-massing-candidate-v0.1.schema.json",
                "search_legacy": "sdg-search-result-v0.1.schema.json",
                "search": "sdg-search-result-v0.2.schema.json"}[kind]
    schema = json.loads((SCHEMA_PATH.parent / filename).read_bytes())
    Draft202012Validator.check_schema(schema)
    registry = Registry().with_resource(project.schema["$id"], Resource.from_contents(project.schema))
    if kind in ("massing", "search_legacy", "search"):
        dependencies = ("geometry", "constraints")
        if kind in ("search_legacy", "search"):
            dependencies += ("massing",)
        if kind == "search":
            dependencies += ("search_legacy",)
        for dependency in dependencies:
            contract = schema_validator(dependency).schema
            registry = registry.with_resource(contract["$id"], Resource.from_contents(contract))
    return Draft202012Validator(schema, registry=registry)
