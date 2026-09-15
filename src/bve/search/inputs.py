"""Bounded explicit search set, with the authoritative Phase 3 scalar parser."""
from decimal import Decimal

from bve.massing import parse_floor_height

from .errors import Code, SearchError

MAX_SEARCH_POINTS = 64


def canonical_heights(values) -> tuple[Decimal, ...]:
    if values is None:
        raise SearchError(Code.SEARCH_SPACE_REQUIRED)
    if type(values) not in (list, tuple):
        raise SearchError(Code.INVALID_ARGUMENTS)
    if not values:
        raise SearchError(Code.SEARCH_SPACE_REQUIRED)
    if len(values) > MAX_SEARCH_POINTS:
        raise SearchError(Code.SEARCH_SPACE_TOO_LARGE)
    heights = tuple(parse_floor_height(value) for value in values)
    if len(set(heights)) != len(heights):
        raise SearchError(Code.DUPLICATE_SEARCH_VALUE)
    return tuple(sorted(heights))
