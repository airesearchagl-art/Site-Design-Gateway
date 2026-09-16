"""Fixed v0.1 artifact names and a small non-disclosing execution summary."""
from dataclasses import dataclass
from types import MappingProxyType

PACKAGE_VERSION = "sdg-run-package-v0.1"
PACKAGE_VERSION_V2 = "sdg-run-package-v0.2"
VERSION_MATRIX = MappingProxyType({
    PACKAGE_VERSION: MappingProxyType({"project": "0.1", "geometry": "0.1", "constraints": "0.1", "search": "0.2"}),
    PACKAGE_VERSION_V2: MappingProxyType({"project": "0.2", "geometry": "0.1", "constraints": "0.2", "search": "0.3"}),
})
ARTIFACTS = MappingProxyType({"project": "project.json", "geometry": "site.geojson",
                             "constraints": "constraints.json", "search": "search-result.json"})
FILE_SET = frozenset(("manifest.json", *ARTIFACTS.values()))


def package_version_for_project(version: str) -> str:
    from .errors import Code, RunError, Stage
    if version == "0.1":
        return PACKAGE_VERSION
    if version == "0.2":
        return PACKAGE_VERSION_V2
    raise RunError(Stage.PROJECT, Code.ARTIFACT_VERSION_MISMATCH)


@dataclass(frozen=True)
class RunSummary:
    review_required: bool
    evaluated: int
    accepted: int
    rejected: int
    package_version: str = PACKAGE_VERSION

    def console(self) -> str:
        return (f"PASS packageVersion={self.package_version} artifacts=4 "
                f"reviewRequired={str(self.review_required).lower()} "
                f"evaluated={self.evaluated} accepted={self.accepted} rejected={self.rejected}")
