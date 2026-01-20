"""
Data models for our Search MCP
These define what our requests and responses look like
"""
from pydantic import BaseModel
from typing import List, Optional


class SearchRequest(BaseModel):
    """When someone wants to search, they send this"""
    query: str  # The search term (e.g., "Python tutorials")
    num_results: Optional[int] = 5  # How many results (default: 5)


class SearchResult(BaseModel):
    """One search result"""
    title: str  # Page title
    url: str  # Web address
    snippet: str  # Description/preview
    rank: int  # Position in results (1, 2, 3...)


class SearchResponse(BaseModel):
    """What we send back after searching"""
    query: str  # What they searched for
    results: List[SearchResult]  # List of results
    total_results: int  # How many results found
    search_engine: str  # Which search engine we used