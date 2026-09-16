"""Serial Phase 3 calls; only explicit per-point failures are recoverable."""
from hashlib import sha256
from dataclasses import replace

from bve.massing import MassingError, generate_massing_candidate
from bve.massing.engine import _require_supported_site, _validate_inputs
from bve.massing.export import candidate_bytes

from .errors import Code, SearchError
from .inputs import canonical_heights
from .model import RankedCandidate, Rejection, SearchResult

POINT_REJECTIONS = frozenset(("NO_FEASIBLE_MASSING", "RESOURCE_LIMIT"))


def _validate_shared(site, constraints, height) -> None:
    # Shared structural resource failures must not become per-height rejections.
    _validate_inputs(site, constraints, height)
    _require_supported_site(site.polygon)


def _sweep(site, constraints, heights):
    _validate_shared(site, constraints, heights[0])
    if constraints.result.schema_version == "0.2" and constraints.result.floor_area_ratio.value == 0:
        # A known zero FAR has no feasible positive candidate. Keep Phase 3 and
        # legacy fatal-error behavior unchanged; use the existing rejection code.
        return (), tuple(Rejection(height, "NO_FEASIBLE_MASSING") for height in heights)
    accepted, rejected, references = [], [], set()
    for height in heights:
        try:
            candidate = generate_massing_candidate(site, constraints, floor_height_m=height)
        except MassingError as error:
            if error.code.value not in POINT_REJECTIONS:
                raise
            rejected.append(Rejection(height, error.code.value))
            continue
        # Export/schema/hash failures are outside the recoverable generator call.
        reference = "sha256:" + sha256(candidate_bytes(candidate)).hexdigest()
        if reference in references:
            raise SearchError(Code.DUPLICATE_CANDIDATE)
        references.add(reference)
        accepted.append(RankedCandidate(0, reference, candidate.gross_floor_area_m2, candidate))
    return tuple(accepted), tuple(rejected)


def _ranking_key(entry):
    # copy_negate is exact even under a small ambient Decimal context.
    return (entry.gross_floor_area_m2.copy_negate(), entry.candidate.floor_height_m,
            entry.candidate_reference)


def search_massing_candidates(site_geometry, constraint_result, *, floor_heights_m=None) -> SearchResult:
    """Execute the explicit set; zero accepted candidates is a completed search."""
    from .export import search_bytes

    heights = canonical_heights(floor_heights_m)
    accepted, rejected = _sweep(site_geometry, constraint_result, heights)
    ranked = tuple(replace(entry, rank=rank) for rank, entry in enumerate(sorted(accepted, key=_ranking_key), 1))
    result = SearchResult(site_geometry, constraint_result, heights, ranked, rejected)
    search_bytes(result)
    return result
