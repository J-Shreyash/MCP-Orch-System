"""
Data models for Google Drive MCP
These define what our requests and responses look like
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class FileUploadResponse(BaseModel):
    """Response after uploading a file"""
    file_id: str  # Google Drive file ID
    file_name: str  # Name of the file
    size: int  # File size in bytes
    mime_type: str  # File type (e.g., 'image/png')
    web_view_link: str  # Link to view file in browser
    message: str  # Success message


class FileInfo(BaseModel):
    """Information about a file in Google Drive"""
    file_id: str
    name: str
    mime_type: str
    size: Optional[int] = 0
    created_time: str
    modified_time: str
    web_view_link: Optional[str] = None


class ListFilesResponse(BaseModel):
    """Response when listing files"""
    files: List[FileInfo]
    total_files: int
    message: str


class DeleteFileResponse(BaseModel):
    """Response after deleting a file"""
    file_id: str
    file_name: str
    message: str
    success: bool


class DownloadFileResponse(BaseModel):
    """Response after downloading a file"""
    file_id: str
    file_name: str
    size: int
    mime_type: str
    message: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    google_drive_connected: bool
    timestamp: str