"""Three fixed computations; exact context independent of caller settings."""
from decimal import (Context, Decimal, DivisionByZero, FloatOperation, Inexact,
                     InvalidOperation, Overflow, ROUND_HALF_EVEN, Underflow)


def _context() -> Context:
    # Inputs: <=1024 coefficient digits and |exponent|<=1024. This precision
    # covers the aligned subtraction and product without discarding any digit.
    return Context(prec=8192, Emin=-9999, Emax=9999, rounding=ROUND_HALF_EVEN,
                   capitals=1, clamp=0,
                   traps=[Inexact, InvalidOperation, DivisionByZero, Overflow, Underflow, FloatOperation])


def coverage_area_cap(area: Decimal, ratio: Decimal) -> Decimal:
    context = _context()
    return context.divide(context.multiply(area, ratio), Decimal(100))


def floor_area_cap(area: Decimal, ratio: Decimal) -> Decimal:
    context = _context()
    return context.divide(context.multiply(area, ratio), Decimal(100))


def height_cap(height: Decimal) -> Decimal:
    return height


def area_difference(declared: Decimal | None, actual: Decimal) -> Decimal | None:
    return None if declared is None else _context().subtract(declared, actual)
