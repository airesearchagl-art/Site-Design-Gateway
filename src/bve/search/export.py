"""Recheck the complete partition and Phase 3 invariants before canonical output."""
from decimal import Decimal, DecimalException
from hashlib import sha256
import json
from pathlib import Path
import warnings

from shapely.errors import GEOSException

from bve._schemas import schema_validator
from bve.constraints.export import _encode, result_bytes
from bve.massing.export import candidate_bytes

from .engine import POINT_REJECTIONS, _validate_shared
from .errors import Code, SearchError
from .inputs import canonical_heights
from .model import RankedCandidate, Rejection, SearchResult


def _require(condition) -> None:
    if not condition:
        raise SearchError(Code.OUTPUT_SEMANTIC_INVALID)


def _validate_context(data: dict, authoritative: dict) -> None:
    """Bind the serialized context and each candidate to the same Constraint Result."""
    context = data["constraintContext"]
    _require(_encode(context["areaBasis"]) == _encode(authoritative["areaBasis"]))
    constraints = authoritative["constraints"]
    caps = {"maxFootprintAreaM2": constraints["buildingCoverage"]["maxFootprintAreaM2"],
            "maxTotalFloorAreaM2": constraints["floorAreaRatio"]["maxTotalFloorAreaM2"],
            "maxHeightM": constraints["height"]["maxHeightM"]}
    _require(_encode(context["constraintCaps"]) == _encode(caps))
    if authoritative["schemaVersion"] == "0.2":
        _require(_encode(context["floorAreaRatio"]) == _encode(constraints["floorAreaRatio"]))
    for entry in data["rankedCandidates"]:
        _require(_encode(entry["candidate"]["constraintCaps"]) == _encode(context["constraintCaps"]))


def _validate_result(result: SearchResult, data: dict) -> None:
    heights = result.floor_heights_m
    _require(type(heights) is tuple and all(type(h) is Decimal for h in heights))
    _require(canonical_heights(heights) == heights)
    _validate_shared(result.site, result.constraints, heights[0])
    canonical_constraints = result_bytes(result.constraints.result)
    _require(result.constraints.reference == "sha256:" + sha256(canonical_constraints).hexdigest())
    authoritative = json.loads(canonical_constraints, parse_float=Decimal, parse_int=Decimal)
    _validate_context(data, authoritative)
    refs = {"project": result.constraints.result.project_reference, "geometry": result.site.source_reference,
            "constraints": result.constraints.reference}
    review = result.constraints.result.review_required
    _require(type(result.ranked_candidates) is tuple and type(result.rejections) is tuple)
    seen_heights, seen_refs, expected_entries = [], set(), []
    previous = None
    for rank, entry in enumerate(result.ranked_candidates, 1):
        _require(type(entry) is RankedCandidate and type(entry.rank) is int and entry.rank == rank)
        candidate = entry.candidate
        _require(candidate.site is result.site and candidate.constraints is result.constraints)
        canonical = candidate_bytes(candidate)  # Reuses all Phase 3 cap and containment guards.
        reference = "sha256:" + sha256(canonical).hexdigest()
        if reference in seen_refs:
            raise SearchError(Code.DUPLICATE_CANDIDATE)
        seen_refs.add(reference)
        _require(entry.candidate_reference == reference)
        gfa, height = candidate.gross_floor_area_m2, candidate.floor_height_m
        _require(type(entry.gross_floor_area_m2) is Decimal and entry.gross_floor_area_m2 == gfa)
        _require(height in heights and candidate.review_required == review)
        # Adjacent order checks are independent of the engine's sort key.
        if previous is not None:
            old_gfa, old_height, old_reference = previous
            _require(old_gfa > gfa or (old_gfa == gfa and (old_height < height or
                     (old_height == height and old_reference <= reference))))
        previous = (gfa, height, reference)
        seen_heights.append(height)
        body = json.loads(canonical, parse_float=Decimal, parse_int=Decimal)
        _require(body["inputReferences"] == refs and body["generator"]["floorHeightM"] == height)
        _require(body["candidate"]["grossFloorAreaM2"] == gfa and body["candidate"]["reviewRequired"] == review)
        expected_entries.append({"rank": rank, "candidateReference": reference,
                                 "grossFloorAreaM2": gfa, "candidate": body})
    rejected_heights, expected_rejections = [], []
    for rejection in result.rejections:
        _require(type(rejection) is Rejection and type(rejection.floor_height_m) is Decimal)
        _require(rejection.code in POINT_REJECTIONS)
        rejected_heights.append(rejection.floor_height_m)
        expected_rejections.append({"floorHeightM": rejection.floor_height_m, "code": rejection.code})
    _require(rejected_heights == sorted(rejected_heights))
    _require(sorted(seen_heights + rejected_heights) == list(heights))
    accepted_count, rejected_count = len(expected_entries), len(expected_rejections)
    expected = {"schemaVersion": result.schema_version, "inputReferences": refs,
                "constraintContext": data["constraintContext"],  # Independently bound above.
                "search": {"strategy": "floor_height_sweep_v0.1", "ranking": "maximize_gross_floor_area_v0.1",
                           "floorHeightsM": list(heights), "floorHeightStatus": "user_provided"},
                "summary": {"evaluated": accepted_count + rejected_count, "accepted": accepted_count,
                            "rejected": rejected_count, "hasFeasibleCandidate": accepted_count > 0,
                            "reviewRequired": review},
                "rankedCandidates": expected_entries, "rejections": expected_rejections}
    # Compare the actual serialized model too: schema alone cannot bind metadata.
    _require(_encode(data) == _encode(expected))


def search_bytes(result: SearchResult) -> bytes:
    if type(result) is not SearchResult:
        raise SearchError(Code.INVALID_ARGUMENTS)
    try:
        validator = schema_validator({"0.2": "search", "0.3": "search_v3"}[result.schema_version])
    except Exception:
        raise SearchError(Code.SCHEMA_UNAVAILABLE) from None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", RuntimeWarning)
            data = result.to_dict()
            if not validator.is_valid(data):
                raise SearchError(Code.OUTPUT_SCHEMA_INVALID)
            _validate_result(result, data)
            return (_encode(data) + "\n").encode("utf-8")
    except (TypeError, KeyError, AttributeError, IndexError, DecimalException, GEOSException, RuntimeWarning, OverflowError):
        raise SearchError(Code.OUTPUT_SEMANTIC_INVALID) from None


def write_output(result: SearchResult, output: Path) -> None:
    data = search_bytes(result)
    try:
        path = Path(output)
        if path.exists() or path.is_symlink():
            raise SearchError(Code.OUTPUT_EXISTS)
        if not path.parent.is_dir():
            raise SearchError(Code.IO_ERROR)
        with path.open("xb") as target:
            target.write(data)
    except SearchError:
        raise
    except FileExistsError:
        raise SearchError(Code.OUTPUT_EXISTS) from None
    except (OSError, ValueError):
        raise SearchError(Code.IO_ERROR) from None
