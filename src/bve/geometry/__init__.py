"""Local XY geometry foundation, independent of Project JSON validation."""
from .errors import Code, GeometryError
from .model import SiteGeometry

__all__ = ["Code", "GeometryError", "SiteGeometry"]
