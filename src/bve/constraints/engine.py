"""Convert existing input conditions; no legal rules, formulas or shape generation."""
from decimal import DecimalException

from bve.geometry import SiteGeometry

from .arithmetic import area_difference, coverage_area_cap, floor_area_cap, height_cap
from .errors import Code, ConstraintError
from .inputs import Condition, ValidatedProject, select_area
from .model import Constraint, ConstraintResult, Provenance


def compute_constraints(project: ValidatedProject, geometry: SiteGeometry, *,
                        area_basis: str | None = None) -> ConstraintResult:
    area = select_area(project, geometry, area_basis)
    declared = Provenance("site.area", project.reference, project.area)
    actual = Provenance("geometry.areaM2", geometry.source_reference,
                        Condition(area.geometry_area_m2, "m2", geometry.source_status))
    selected = declared if area.selected_basis == "declared_project_area" else actual
    coverage_source = Provenance("zoning.buildingCoverageRatio", project.reference, project.coverage)
    far_source = Provenance("zoning.floorAreaRatio", project.reference, project.far)
    try:
        coverage_value = (None if project.coverage.value is None else
                          coverage_area_cap(area.basis_area_m2, project.coverage.value))
        far_value = (None if project.far.value is None else
                    floor_area_cap(area.basis_area_m2, project.far.value))
        coverage = Constraint("UNAVAILABLE" if coverage_value is None else "COMPUTED",
                              "coverage_area_cap_v0.1", coverage_value, (selected, coverage_source))
        far = Constraint("UNAVAILABLE" if far_value is None else "COMPUTED",
                         "floor_area_cap_v0.1", far_value, (selected, far_source))
        if project.height is None:
            height = Constraint("ABSENT", "height_cap_v0.1", None, ())
        else:
            value = None if project.height.value is None else height_cap(project.height.value)
            height = Constraint("UNAVAILABLE" if value is None else "COMPUTED", "height_cap_v0.1", value,
                                (Provenance("zoning.heightLimit", project.reference, project.height),))
        difference = area_difference(area.declared_area_m2, area.geometry_area_m2)
    except DecimalException:
        raise ConstraintError(Code.NUMERIC_RANGE) from None
    return ConstraintResult(project.reference, geometry.source_reference, area, difference,
                            (declared, actual), coverage, far, height)
