"""
Data models for Database MCP
Defines request/response structures for both MySQL and ChromaDB
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== DOCUMENT MODELS ====================

class DocumentCreate(BaseModel):
    """Request to create a new document"""
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = {}
    category: Optional[str] = "general"
    tags: Optional[List[str]] = []


class DocumentResponse(BaseModel):
    """Response after creating/retrieving a document"""
    doc_id: str
    title: str
    content: str
    metadata: Dict[str, Any]
    category: str
    tags: List[str]
    created_at: str
    updated_at: str
    mysql_id: Optional[int] = None
    chroma_id: Optional[str] = None


class DocumentUpdate(BaseModel):
    """Request to update a document"""
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


# ==================== SEARCH MODELS ====================

class SearchQuery(BaseModel):
    """Search request"""
    query: str
    limit: Optional[int] = 10
    category: Optional[str] = None
    search_type: Optional[str] = "semantic"  # semantic, keyword, or hybrid


class SearchResult(BaseModel):
    """Single search result"""
    doc_id: str
    title: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]
    category: str


class SearchResponse(BaseModel):
    """Search results response"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_type: str


# ==================== DATABASE STATS MODELS ====================

class DatabaseStats(BaseModel):
    """Database statistics"""
    mysql_connected: bool
    chroma_connected: bool
    total_documents: int
    mysql_documents: int
    chroma_documents: int
    collections: List[str]
    sync_status: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    mysql_status: str
    chroma_status: str
    sync_status: str
    timestamp: str


# ==================== SYNC MODELS ====================

class SyncStatus(BaseModel):
    """Sync operation status"""
    synced: int
    failed: int
    total: int
    status: str
    message: str


class BatchOperation(BaseModel):
    """Batch operation response"""
    operation: str
    successful: int
    failed: int
    total: int
    details: List[Dict[str, Any]]


# ==================== LOG MODELS ====================

class ActivityLog(BaseModel):
    """Activity log entry"""
    log_id: int
    action: str
    doc_id: Optional[str]
    details: Optional[str]
    timestamp: str


class LogQuery(BaseModel):
    """Query for activity logs"""
    limit: Optional[int] = 50
    action: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None