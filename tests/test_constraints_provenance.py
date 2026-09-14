"""Every declared source status survives each applicable dependency trace."""
import json

import pytest

from bve._schemas import schema_validator
from bve.constraints import compute_constraints, load_project
from bve.geometry import load_normalized_geometry

STATUSES = ["official_verified", "user_provided", "drawing_derived", "llm_researched",
            "assumed", "unknown", "review_required"]


@pytest.mark.parametrize("status", STATUSES)
@pytest.mark.parametrize("field", ["site.area", "geometry.areaM2", "zoning.buildingCoverageRatio",
                                  "zoning.floorAreaRatio", "zoning.heightLimit"])
def test_all_statuses_retained_without_promotion(project_document, normalized_document, status, field):
    project_document["site"]["area"]["status"] = "official_verified"
    for condition in project_document["zoning"].values():
        condition["status"] = "official_verified"
    normalized_document["properties"]["sourceStatus"] = "official_verified"
    if field == "geometry.areaM2":
        normalized_document["properties"]["sourceStatus"] = status
    else:
        parent, key = field.split(".")
        project_document[parent][key]["status"] = status
    basis = "geometry_area" if field == "geometry.areaM2" else "declared_project_area"
    result = compute_constraints(load_project(json.dumps(project_document)),
        load_normalized_geometry(json.dumps(normalized_document)), area_basis=basis)
    sources = [*result.area_provenance, *result.building_coverage.provenance,
               *result.floor_area_ratio.provenance, *result.height.provenance]
    matched = [source for source in sources if source.input == field]
    assert matched and all(source.condition.status == status for source in matched)
    assert result.review_required == (status in {"assumed", "unknown", "review_required"})
    output = result.to_dict()
    exported = [*output["areaBasis"]["provenance"],
                *(source for item in output["constraints"].values() for source in item["provenance"])]
    assert all(source["condition"]["status"] == status for source in exported if source["input"] == field)
    schema_validator("constraints").validate(output)


def test_dependencies_and_review_are_specific_to_each_constraint(project_document, normalized_document):
    project_document["site"]["area"]["status"] = "assumed"
    for condition in project_document["zoning"].values():
        condition["status"] = "official_verified"
    normalized_document["properties"]["sourceStatus"] = "official_verified"
    project = load_project(json.dumps(project_document))
    geometry = load_normalized_geometry(json.dumps(normalized_document))
    declared = compute_constraints(project, geometry, area_basis="declared_project_area")
    measured = compute_constraints(project, geometry, area_basis="geometry_area")
    assert declared.building_coverage.review_required and declared.floor_area_ratio.review_required
    assert not declared.height.review_required
    assert not measured.building_coverage.review_required and not measured.floor_area_ratio.review_required
    assert measured.review_required  # Unselected declared area remains in comparison evidence.
    for result, key, reference in ((declared, "site.area", project.reference),
                                   (measured, "geometry.areaM2", geometry.source_reference)):
        assert result.building_coverage.provenance[0].input == result.floor_area_ratio.provenance[0].input == key
        assert result.building_coverage.provenance[0].reference == reference
        assert result.building_coverage.provenance[1].input == "zoning.buildingCoverageRatio"
        assert result.floor_area_ratio.provenance[1].input == "zoning.floorAreaRatio"
        assert [item.input for item in result.height.provenance] == ["zoning.heightLimit"]
