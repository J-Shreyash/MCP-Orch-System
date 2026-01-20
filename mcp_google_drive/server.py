"""
Google Drive MCP Server
Provides REST API for Google Drive operations
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
from datetime import datetime
import tempfile

# Import from current directory
from models import (
    FileUploadResponse, FileInfo, ListFilesResponse,
    DeleteFileResponse, DownloadFileResponse, HealthResponse
)
from drive_handler import DriveHandler

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Google Drive MCP Server",
    description="MCP server for Google Drive operations - upload, list, download, delete files",
    version="1.0.0"
)

# Initialize Drive handler (will authenticate on startup)
print("🚀 Google Drive MCP Server initializing...")
drive_handler = DriveHandler(credentials_file='credentials.json')
print("📡 Drive handler ready!")


@app.get("/")
async def root():
    """Root endpoint - server information"""
    return {
        "message": "🎉 Google Drive MCP Server is running!",
        "service": "Google Drive MCP",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload - Upload a file to Google Drive",
            "list": "GET /files - List files in Google Drive",
            "download": "GET /download/{file_id} - Download a file",
            "delete": "DELETE /files/{file_id} - Delete a file",
            "info": "GET /files/{file_id} - Get file information",
            "health": "GET /health - Check server health"
        },
        "status": "operational"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="Google Drive MCP",
        google_drive_connected=drive_handler.is_connected(),
        timestamp=datetime.now().isoformat()
    )


@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to Google Drive
    
    - **file**: File to upload (multipart/form-data)
    """
    print(f"\n{'='*60}")
    print(f"📨 Received upload request")
    print(f"   Filename: {file.filename}")
    print(f"   Content-Type: {file.content_type}")
    print(f"{'='*60}")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Upload to Google Drive
        result = drive_handler.upload_file(temp_path)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to upload file to Google Drive")
        
        response = FileUploadResponse(
            file_id=result.get('id'),
            file_name=result.get('name'),
            size=int(result.get('size', 0)),
            mime_type=result.get('mimeType'),
            web_view_link=result.get('webViewLink', ''),
            message="File uploaded successfully"
        )
        
        print(f"✅ Upload complete!\n")
        return response
    
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/files", response_model=ListFilesResponse)
async def list_files(max_results: int = 10):
    """
    List files in Google Drive
    
    - **max_results**: Maximum number of files to return (default: 10)
    """
    print(f"\n{'='*60}")
    print(f"📨 Received list files request")
    print(f"   Max results: {max_results}")
    print(f"{'='*60}")
    
    try:
        files = drive_handler.list_files(max_results=max_results)
        
        file_infos = []
        for file in files:
            file_info = FileInfo(
                file_id=file.get('id'),
                name=file.get('name'),
                mime_type=file.get('mimeType'),
                size=int(file.get('size', 0)) if file.get('size') else 0,
                created_time=file.get('createdTime', ''),
                modified_time=file.get('modifiedTime', ''),
                web_view_link=file.get('webViewLink')
            )
            file_infos.append(file_info)
        
        response = ListFilesResponse(
            files=file_infos,
            total_files=len(file_infos),
            message=f"Found {len(file_infos)} files"
        )
        
        print(f"✅ List complete!\n")
        return response
    
    except Exception as e:
        print(f"❌ List error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@app.get("/files/{file_id}", response_model=FileInfo)
async def get_file_info(file_id: str):
    """
    Get information about a specific file
    
    - **file_id**: Google Drive file ID
    """
    print(f"\n{'='*60}")
    print(f"📨 Received file info request")
    print(f"   File ID: {file_id}")
    print(f"{'='*60}")
    
    try:
        file = drive_handler.get_file_info(file_id)
        
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = FileInfo(
            file_id=file.get('id'),
            name=file.get('name'),
            mime_type=file.get('mimeType'),
            size=int(file.get('size', 0)) if file.get('size') else 0,
            created_time=file.get('createdTime', ''),
            modified_time=file.get('modifiedTime', ''),
            web_view_link=file.get('webViewLink')
        )
        
        print(f"✅ Info retrieved!\n")
        return file_info
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Info error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")


@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """
    Download a file from Google Drive
    
    - **file_id**: Google Drive file ID
    """
    print(f"\n{'='*60}")
    print(f"📨 Received download request")
    print(f"   File ID: {file_id}")
    print(f"{'='*60}")
    
    try:
        # Get file info first
        file_info = drive_handler.get_file_info(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_name = file_info.get('name')
        
        # Download to temp location
        temp_path = os.path.join(tempfile.gettempdir(), file_name)
        result = drive_handler.download_file(file_id, temp_path)
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to download file")
        
        print(f"✅ Download ready!\n")
        
        # Return file
        return FileResponse(
            path=temp_path,
            filename=file_name,
            media_type=file_info.get('mimeType', 'application/octet-stream')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Download error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.delete("/files/{file_id}", response_model=DeleteFileResponse)
async def delete_file(file_id: str):
    """
    Delete a file from Google Drive
    
    - **file_id**: Google Drive file ID
    """
    print(f"\n{'='*60}")
    print(f"📨 Received delete request")
    print(f"   File ID: {file_id}")
    print(f"{'='*60}")
    
    try:
        # Get file name first
        file_info = drive_handler.get_file_info(file_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_name = file_info.get('name')
        
        # Delete the file
        success = drive_handler.delete_file(file_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete file")
        
        response = DeleteFileResponse(
            file_id=file_id,
            file_name=file_name,
            message=f"File '{file_name}' deleted successfully",
            success=True
        )
        
        print(f"✅ Delete complete!\n")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Delete error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


# This runs when you start the server directly
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting Google Drive MCP Server...")
    print("📍 Server will run on: http://localhost:8002")
    print("📚 API Docs available at: http://localhost:8002/docs")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)