"""Constraint-bounded conceptual massing; independent of Web and legal rules."""
from .engine import generate_massing_candidate
from .errors import Code, MassingError
from .model import MassingCandidate

__all__ = ["generate_massing_candidate", "MassingCandidate", "Code", "MassingError"]
