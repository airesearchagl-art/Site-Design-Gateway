"""Constraint-bounded conceptual massing; independent of Web and legal rules."""
from .engine import generate_massing_candidate, parse_floor_height
from .errors import Code, MassingError
from .model import MassingCandidate

__all__ = ["generate_massing_candidate", "parse_floor_height", "MassingCandidate", "Code", "MassingError"]
