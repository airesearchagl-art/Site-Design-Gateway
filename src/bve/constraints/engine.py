"""Convert existing input conditions; no legal rules, formulas or shape generation."""
from decimal import DecimalException

from bve.geometry import SiteGeometry

from .arithmetic import area_difference, coverage_area_cap, floor_area_cap, height_cap
from .errors import Code, ConstraintError
from .inputs import AdditionalHeightCap, AdditionalFarCap, AreaSelection, Condition, ValidatedProject, select_area
from .far_stack import compute_far_stack
from .height_stack import compute_height_stack
from .model import Constraint, ConstraintResult, Provenance


def compute_constraints(project: ValidatedProject, geometry: SiteGeometry, *,
                        area_basis: str | None = None) -> ConstraintResult:
    area = select_area(project, geometry, area_basis)
    return _compute_result(project.reference, geometry.source_reference, area, project.area,
                           Condition(area.geometry_area_m2, "m2", geometry.source_status),
                           project.coverage, project.far, project.height,
                           schema_version=project.schema_version, additional_caps=project.additional_far_caps, additional_height_caps=project.additional_height_caps)


def _compute_result(project_reference: str, geometry_reference: str, area: AreaSelection,
                    declared_condition: Condition, actual_condition: Condition,
                    coverage_condition: Condition, far_condition: Condition,
                    height_condition: Condition | None, *, schema_version: str = "0.1",
                    additional_caps: tuple[AdditionalFarCap, ...] = (),
                    additional_height_caps: tuple[AdditionalHeightCap, ...] = ()) -> ConstraintResult:
    """Shared calculation path; callers validate conditions before entry."""
    declared = Provenance("site.area", project_reference, declared_condition)
    actual = Provenance("geometry.areaM2", geometry_reference, actual_condition)
    selected = declared if area.selected_basis == "declared_project_area" else actual
    coverage_source = Provenance("zoning.buildingCoverageRatio", project_reference, coverage_condition)
    far_source = Provenance("zoning.floorAreaRatio", project_reference, far_condition)
    try:
        coverage_value = (None if coverage_condition.value is None else
                          coverage_area_cap(area.basis_area_m2, coverage_condition.value))
        coverage = Constraint("UNAVAILABLE" if coverage_value is None else "COMPUTED",
                              "coverage_area_cap_v0.1", coverage_value, (selected, coverage_source))
        if schema_version == "0.1":
            far_value = (None if far_condition.value is None else
                         floor_area_cap(area.basis_area_m2, far_condition.value))
            far = Constraint("UNAVAILABLE" if far_value is None else "COMPUTED",
                             "floor_area_cap_v0.1", far_value, (selected, far_source))
        elif schema_version in ("0.2", "0.3", "0.4"):
            far = compute_far_stack(area.basis_area_m2, selected, project_reference, far_condition, additional_caps)
        else:
            raise ConstraintError(Code.INVALID_ARGUMENTS)
        if schema_version in ("0.3", "0.4"):
            height = compute_height_stack(project_reference, height_condition, additional_height_caps)
        elif height_condition is None:
            height = Constraint("ABSENT", "height_cap_v0.1", None, ())
        else:
            value = None if height_condition.value is None else height_cap(height_condition.value)
            height = Constraint("UNAVAILABLE" if value is None else "COMPUTED", "height_cap_v0.1", value,
                                (Provenance("zoning.heightLimit", project_reference, height_condition),))
        difference = area_difference(area.declared_area_m2, area.geometry_area_m2)
    except DecimalException:
        raise ConstraintError(Code.NUMERIC_RANGE) from None
    return ConstraintResult(project_reference, geometry_reference, area, difference,
                            (declared, actual), coverage, far, height, schema_version)
