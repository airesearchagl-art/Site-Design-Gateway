"""Fixed v0.1 artifact names and a small non-disclosing execution summary."""
from dataclasses import dataclass
from types import MappingProxyType

PACKAGE_VERSION = "sdg-run-package-v0.1"
ARTIFACTS = MappingProxyType({"project": "project.json", "geometry": "site.geojson",
                             "constraints": "constraints.json", "search": "search-result.json"})
FILE_SET = frozenset(("manifest.json", *ARTIFACTS.values()))


@dataclass(frozen=True)
class RunSummary:
    review_required: bool
    evaluated: int
    accepted: int
    rejected: int

    def console(self) -> str:
        return (f"PASS packageVersion={PACKAGE_VERSION} artifacts=4 "
                f"reviewRequired={str(self.review_required).lower()} "
                f"evaluated={self.evaluated} accepted={self.accepted} rejected={self.rejected}")
