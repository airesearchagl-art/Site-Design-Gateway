"""Local XY geometry foundation, independent of Project JSON validation."""
from .errors import Code, GeometryError
from .model import SiteGeometry
from .geojson import read_geojson
from .dxf import read_dxf
from .normalized import load_normalized_geometry

__all__ = ["Code", "GeometryError", "SiteGeometry", "read_geojson", "read_dxf", "load_normalized_geometry"]
