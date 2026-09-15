"""Actual floating geometry, convex-only support and strict postconditions."""
from decimal import Decimal, localcontext
import math

import pytest
from shapely import Polygon
from shapely.affinity import translate

from bve.massing import engine
from bve.massing.errors import MassingError


@pytest.mark.parametrize("points", [
    [(0, 0), (10, 0), (10, 20), (0, 20)],
    [(0, 0), (20, 0), (10, 20)],
    [(-7, 0), (0, -4), (9, 0), (4, 12), (-4, 8)],
    [(0, 0), (5, 0), (10, 0), (10, 20), (0, 20)],
])
@pytest.mark.parametrize("target", ["0.1", "13.33333333333333", "160", "1000"])
def test_convex_generated_footprint(points, target):
    site = Polygon(points)
    target = min(Decimal(target), Decimal(str(site.area)))
    footprint = engine._generate_footprint(site, target)
    assert site.covers(footprint)
    assert footprint.is_valid and not footprint.interiors and footprint.equals(footprint.convex_hull)
    assert 0 < Decimal(str(footprint.area)) <= target
    if target == Decimal(str(site.area)):
        assert footprint.equals(site)


@pytest.mark.parametrize("polygon", [Polygon([(0, 0), (10, 0), (4, 4), (10, 10), (0, 10)]),
    Polygon([(0, 0), (10, 0), (10, 10), (0, 10)], holes=[[(2, 2), (3, 2), (3, 3), (2, 3)]])],
    ids=["concave", "hole"])
def test_unsupported_site_is_never_converted(polygon):
    before = polygon.wkb
    with pytest.raises(MassingError, match="^UNSUPPORTED_MASSING_SITE_GEOMETRY$"):
        engine._generate_footprint(polygon, Decimal(20))
    assert polygon.wkb == before


def test_containment_postcondition_rejects_small_outside_footprint():
    site = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    outside = translate(Polygon([(0, 0), (1, 0), (0, 1)]), xoff=20)
    with pytest.raises(MassingError, match="^GEOMETRY_GENERATION_FAILED$"):
        engine._check_footprint(site, outside, Decimal(100))


def test_containment_rejects_partial_overlap_despite_intersection():
    site = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    partial_outside = Polygon([(9, 1), (11, 1), (11, 3), (9, 3)])
    target = Decimal(100)
    assert site.intersects(partial_outside)
    assert not site.covers(partial_outside)
    assert partial_outside.is_valid and not partial_outside.interiors
    assert partial_outside.equals(partial_outside.convex_hull)
    assert math.isfinite(partial_outside.area) and 0 < Decimal(str(partial_outside.area)) < target
    assert all(len(point) == 2 and all(math.isfinite(value) for value in point)
               for point in partial_outside.exterior.coords)
    with pytest.raises(MassingError, match="^GEOMETRY_GENERATION_FAILED$"):
        engine._check_footprint(site, partial_outside, target)


def test_strict_cap_no_epsilon():
    site = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    with pytest.raises(MassingError, match="^GEOMETRY_GENERATION_FAILED$"):
        engine._check_footprint(site, site, Decimal("99.999999999999999999999999999999"))


def test_shrink_is_bounded_and_only_towards_zero(monkeypatch):
    site = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    factors = []
    def stuck(*args, **kwargs):
        factors.append((kwargs["xfact"], kwargs["yfact"]))
        return site
    monkeypatch.setattr(engine, "affine_scale", stuck)
    with pytest.raises(MassingError, match="^GEOMETRY_GENERATION_FAILED$"):
        engine._generate_footprint(site, Decimal(80))
    assert len(factors) == 65
    assert all(x == y for x, y in factors)
    assert all(b[0] == math.nextafter(a[0], 0.0) for a, b in zip(factors, factors[1:]))


def test_extreme_underflow_fails_without_fake_area():
    site = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    with pytest.raises(MassingError, match="^GEOMETRY_GENERATION_FAILED$"):
        engine._generate_footprint(site, Decimal("1e-2050"))


def test_geometry_ratio_independent_of_decimal_context():
    site = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    expected = engine._generate_footprint(site, Decimal("79.987654321"))
    with localcontext() as context:
        context.prec, context.Emin, context.Emax = 1, -1, 1
        assert engine._generate_footprint(site, Decimal("79.987654321")).wkb == expected.wkb
