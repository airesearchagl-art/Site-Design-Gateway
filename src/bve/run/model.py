"""Fixed v0.1 artifact names and a small non-disclosing execution summary."""
from dataclasses import dataclass
from types import MappingProxyType

PACKAGE_VERSION = "sdg-run-package-v0.1"
PACKAGE_VERSION_V2 = "sdg-run-package-v0.2"
PACKAGE_VERSION_V3 = "sdg-run-package-v0.3"
PACKAGE_VERSION_V4 = "sdg-run-package-v0.4"
VERSION_MATRIX = MappingProxyType({
    PACKAGE_VERSION_V4: MappingProxyType({"project":"0.4", "geometry":"0.1", "buildableArea":"0.1", "constraints":"0.4", "search":"0.5"}),
    PACKAGE_VERSION_V3: MappingProxyType({"project":"0.3", "geometry":"0.1", "constraints":"0.3", "search":"0.4"}),
    PACKAGE_VERSION: MappingProxyType({"project": "0.1", "geometry": "0.1", "constraints": "0.1", "search": "0.2"}),
    PACKAGE_VERSION_V2: MappingProxyType({"project": "0.2", "geometry": "0.1", "constraints": "0.2", "search": "0.3"}),
})
ARTIFACTS = MappingProxyType({"project": "project.json", "geometry": "site.geojson",
                             "constraints": "constraints.json", "search": "search-result.json"})
FILE_SET = frozenset(("manifest.json", *ARTIFACTS.values()))
ARTIFACTS_V4 = MappingProxyType({**ARTIFACTS, "buildableArea": "buildable-area.geojson"})
ARTIFACT_SETS = MappingProxyType({PACKAGE_VERSION: ARTIFACTS, PACKAGE_VERSION_V2: ARTIFACTS,
                                 PACKAGE_VERSION_V3: ARTIFACTS, PACKAGE_VERSION_V4: ARTIFACTS_V4})
FILE_SETS = MappingProxyType({version: frozenset(("manifest.json", *artifacts.values()))
                             for version, artifacts in ARTIFACT_SETS.items()})


def package_version_for_project(version: str) -> str:
    from .errors import Code, RunError, Stage
    if version == "0.1":
        return PACKAGE_VERSION
    if version == "0.2":
        return PACKAGE_VERSION_V2
    if version == "0.3":
        return PACKAGE_VERSION_V3
    if version == "0.4":
        return PACKAGE_VERSION_V4
    raise RunError(Stage.PROJECT, Code.ARTIFACT_VERSION_MISMATCH)


@dataclass(frozen=True)
class RunSummary:
    review_required: bool
    evaluated: int
    accepted: int
    rejected: int
    package_version: str = PACKAGE_VERSION

    def console(self) -> str:
        return (f"PASS packageVersion={self.package_version} artifacts={len(ARTIFACT_SETS[self.package_version])} "
                f"reviewRequired={str(self.review_required).lower()} "
                f"evaluated={self.evaluated} accepted={self.accepted} rejected={self.rejected}")
