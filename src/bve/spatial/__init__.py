"""Explicit supplied footprint domains; no legal geometry generation."""
from .errors import Code, SpatialError
from .inputs import load_buildable_area, read_buildable_area
from .model import ValidatedBuildableArea, buildable_bytes

__all__ = ["Code", "SpatialError", "ValidatedBuildableArea", "buildable_bytes",
           "load_buildable_area", "read_buildable_area"]
