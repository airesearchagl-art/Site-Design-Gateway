"""Explicit finite floor-height search; GFA order has no design-quality meaning."""
from .engine import search_massing_candidates
from .errors import Code, SearchError
from .model import SearchResult

__all__ = ["search_massing_candidates", "SearchResult", "Code", "SearchError"]
