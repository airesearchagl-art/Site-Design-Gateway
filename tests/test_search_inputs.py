"""Boundary cases use the same scalar contract as Phase 3."""
from decimal import Decimal

import pytest

from bve.massing import MassingError, parse_floor_height
from bve.search.errors import SearchError
from bve.search.inputs import canonical_heights


@pytest.mark.parametrize('values,code', [
    (None, 'SEARCH_SPACE_REQUIRED'), ([], 'SEARCH_SPACE_REQUIRED'), ((), 'SEARCH_SPACE_REQUIRED'),
    (list(range(1, 66)), 'SEARCH_SPACE_TOO_LARGE'), ('4', 'INVALID_ARGUMENTS'),
    ({4, 5}, 'INVALID_ARGUMENTS'), ({'height': 4}, 'INVALID_ARGUMENTS'),
    ([4, 4.0], 'DUPLICATE_SEARCH_VALUE'), (['4e0', Decimal('4.000')], 'DUPLICATE_SEARCH_VALUE'),
    ([4, 4.0, '4e0', Decimal('4.000')], 'DUPLICATE_SEARCH_VALUE')])
def test_search_space_rejects(values, code):
    with pytest.raises(SearchError, match=f'^{code}$'):
        canonical_heights(values)


@pytest.mark.parametrize('value', [0, -1, 'NaN', 'Infinity', float('nan'), float('inf'), True, False,
    'invalid', '4m', '', ' 4', '4 ', '4_0', '1e1025', '1e-1025', [], {}, None])
def test_invalid_scalars_preserve_phase3_code(value):
    with pytest.raises(MassingError) as expected:
        parse_floor_height(value)
    with pytest.raises(MassingError) as actual:
        canonical_heights([value])
    assert actual.value.code == expected.value.code


@pytest.mark.parametrize('values', [[8, 6, 4, 7, 5], ['8.0', Decimal('6.000'), '4e0', 7.0, 5]])
def test_numeric_order(values):
    assert canonical_heights(values) == tuple(map(Decimal, [4, 5, 6, 7, 8]))


def test_minimum_and_maximum():
    assert canonical_heights([4]) == (Decimal(4),)
    assert canonical_heights(list(range(64, 0, -1))) == tuple(map(Decimal, range(1, 65)))
