"""Serial Phase 3 calls; only explicit per-point failures are recoverable."""
from hashlib import sha256

from bve.massing import MassingError, generate_massing_candidate
from bve.massing.engine import _require_supported_site, _validate_inputs
from bve.massing.export import candidate_bytes

from .errors import Code, SearchError
from .model import RankedCandidate, Rejection

POINT_REJECTIONS = frozenset(("NO_FEASIBLE_MASSING", "RESOURCE_LIMIT"))


def _validate_shared(site, constraints, height) -> None:
    # Shared structural resource failures must not become per-height rejections.
    _validate_inputs(site, constraints, height)
    _require_supported_site(site.polygon)


def _sweep(site, constraints, heights):
    _validate_shared(site, constraints, heights[0])
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
