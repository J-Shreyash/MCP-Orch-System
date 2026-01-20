"""
Data models for RAG PDF MCP
Defines request/response structures for PDF processing and RAG operations
Company: Sepia ML - Production Ready
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


# ==================== PDF MODELS ====================

class PDFUploadResponse(BaseModel):
    """Response after uploading a PDF"""
    pdf_id: str
    filename: str
    file_size: int
    page_count: int
    chunks_created: int
    processed_at: str
    message: str


class PDFInfo(BaseModel):
    """PDF metadata information"""
    pdf_id: str
    filename: str
    file_size: int
    page_count: int
    chunks_count: int
    uploaded_at: str
    processed: bool


class PDFListResponse(BaseModel):
    """Response for listing PDFs"""
    pdfs: List[PDFInfo]
    total_pdfs: int


# ==================== CHUNK MODELS ====================

class ChunkInfo(BaseModel):
    """Information about a text chunk"""
    chunk_id: str
    pdf_id: str
    pdf_filename: str
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = {}


class ChunkListResponse(BaseModel):
    """Response for listing chunks"""
    chunks: List[ChunkInfo]
    total_chunks: int
    pdf_id: Optional[str] = None


# ==================== SEARCH MODELS ====================

class SearchQuery(BaseModel):
    """Search request for PDFs"""
    query: str
    limit: Optional[int] = 5
    pdf_id: Optional[str] = None
    include_context: Optional[bool] = True
    search_type: Optional[str] = "hybrid"  # semantic, keyword, or hybrid


class SearchResult(BaseModel):
    """Single search result from PDF"""
    chunk_id: str
    pdf_id: str
    pdf_filename: str
    content: str
    page_number: Optional[int] = None
    similarity_score: float
    context: Optional[str] = None


class SearchResponse(BaseModel):
    """Search results response"""
    query: str
    results: List[SearchResult]
    total_results: int
    search_type: str


# ==================== RAG MODELS ====================

class RAGQuery(BaseModel):
    """RAG query request"""
    question: str
    pdf_id: Optional[str] = None
    max_context_chunks: Optional[int] = 5
    include_sources: Optional[bool] = True


class RAGAnswer(BaseModel):
    """RAG answer response"""
    question: str
    answer: str
    sources: List[SearchResult]
    confidence: float
    pdf_ids: List[str]


# ==================== SUMMARY MODELS ====================

class SummaryRequest(BaseModel):
    """Request to summarize a PDF"""
    pdf_id: str
    summary_type: Optional[str] = "extractive"
    max_length: Optional[int] = 500


class SummaryResponse(BaseModel):
    """Summary response"""
    pdf_id: str
    pdf_filename: str
    summary: str
    summary_type: str
    key_points: List[str]
    word_count: int


# ==================== SYSTEM MODELS ====================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    mysql_status: str
    chroma_status: str
    total_pdfs: int
    total_chunks: int
    timestamp: str


class StatsResponse(BaseModel):
    """Statistics response"""
    total_pdfs: int
    total_chunks: int
    total_pages: int
    mysql_connected: bool
    chroma_connected: bool
    storage_used_mb: float


class DeleteResponse(BaseModel):
    """Delete operation response"""
    pdf_id: str
    filename: str
    chunks_deleted: int
    message: str
    success: bool