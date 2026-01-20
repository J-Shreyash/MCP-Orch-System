"""
Drive MCP Client - Production Ready
Connects to Google Drive MCP Server (Port 8002)
Provides file management capabilities for the AI Agent System
"""
import requests
from typing import List, Dict, Optional
import json
import os
from pathlib import Path


class DriveMCPClient:
    """Client for Google Drive MCP Server"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8002"):
        """
        Initialize Drive MCP Client
        
        Args:
            base_url: Base URL of Drive MCP Server (default: http://localhost:8002)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = 60  # seconds (longer for file operations)
        print(f"📂 Drive MCP Client initialized")
        print(f"   Server: {self.base_url}")
    
    def health_check(self) -> Dict:
        """
        Check if Drive MCP server is running
        
        Returns:
            Health status dictionary
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "server": "Drive MCP",
                    "available": True,
                    "google_drive_connected": data.get('google_drive_connected', False),
                    "data": data
                }
            else:
                return {
                    "status": "unhealthy",
                    "server": "Drive MCP",
                    "available": False,
                    "error": f"Status code: {response.status_code}"
                }
        
        except requests.exceptions.ConnectionError:
            return {
                "status": "unavailable",
                "server": "Drive MCP",
                "available": False,
                "error": "Cannot connect to server. Is it running on port 8002?"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "server": "Drive MCP",
                "available": False,
                "error": str(e)
            }
    
    def upload_file(self, file_path: str) -> Dict:
        """
        Upload a file to Google Drive
        
        Args:
            file_path: Path to file to upload
            
        Returns:
            Upload result dictionary
            
        Example:
            >>> client = DriveMCPClient()
            >>> result = client.upload_file("document.pdf")
            >>> print(result['file_id'])
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            print(f"\n📤 Uploading: {filename}")
            print(f"   Size: {file_size:,} bytes")
            
            # Open and upload file
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f)}
                
                response = requests.post(
                    f"{self.base_url}/upload",
                    files=files,
                    timeout=self.timeout
                )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Upload successful!")
                print(f"   File ID: {data.get('file_id')}")
                print(f"   View: {data.get('web_view_link')}")
                
                return {
                    "success": True,
                    "file_id": data.get('file_id'),
                    "file_name": data.get('file_name'),
                    "size": data.get('size'),
                    "web_view_link": data.get('web_view_link'),
                    "message": data.get('message')
                }
            else:
                print(f"❌ Upload failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Upload failed with status {response.status_code}",
                    "details": response.text
                }
        
        except requests.exceptions.Timeout:
            print("❌ Upload timeout")
            return {
                "success": False,
                "error": "Upload request timed out"
            }
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_files(self, max_results: int = 10) -> Dict:
        """
        List files in Google Drive
        
        Args:
            max_results: Maximum number of files to return (default: 10)
            
        Returns:
            Dictionary with file list
        """
        try:
            print(f"\n📋 Listing files (max: {max_results})...")
            
            response = requests.get(
                f"{self.base_url}/files",
                params={"max_results": max_results},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                files = data.get('files', [])
                
                print(f"✅ Found {len(files)} files")
                
                return {
                    "success": True,
                    "files": files,
                    "total_files": data.get('total_files', 0),
                    "message": data.get('message', '')
                }
            else:
                print(f"❌ List failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"List failed with status {response.status_code}",
                    "details": response.text
                }
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_file_info(self, file_id: str) -> Dict:
        """
        Get information about a specific file
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            File information dictionary
        """
        try:
            print(f"\nℹ️ Getting file info: {file_id}")
            
            response = requests.get(
                f"{self.base_url}/files/{file_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ File: {data.get('name')}")
                
                return {
                    "success": True,
                    "file_info": data
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": "File not found"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed with status {response.status_code}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def download_file(self, file_id: str, save_path: str = None) -> Dict:
        """
        Download a file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            save_path: Where to save the file (optional, uses filename if not provided)
            
        Returns:
            Download result dictionary
        """
        try:
            print(f"\n📥 Downloading file: {file_id}")
            
            response = requests.get(
                f"{self.base_url}/download/{file_id}",
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                # Get filename from headers
                content_disposition = response.headers.get('content-disposition', '')
                filename = file_id
                
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"')
                
                if not save_path:
                    save_path = filename
                
                # Save file
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"✅ Downloaded to: {save_path}")
                
                return {
                    "success": True,
                    "file_id": file_id,
                    "saved_path": save_path,
                    "message": f"File downloaded successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Download failed with status {response.status_code}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_file(self, file_id: str) -> Dict:
        """
        Delete a file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            
        Returns:
            Delete result dictionary
        """
        try:
            print(f"\n🗑️ Deleting file: {file_id}")
            
            response = requests.delete(
                f"{self.base_url}/files/{file_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Deleted: {data.get('file_name')}")
                
                return {
                    "success": True,
                    "file_id": file_id,
                    "file_name": data.get('file_name'),
                    "message": data.get('message')
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": "File not found"
                }
            else:
                return {
                    "success": False,
                    "error": f"Delete failed with status {response.status_code}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def format_file_list(self, file_list_result: Dict, max_files: int = 10) -> str:
        """
        Format file list into readable text
        
        Args:
            file_list_result: Result from list_files() method
            max_files: Maximum files to format
            
        Returns:
            Formatted string
        """
        if not file_list_result.get('success'):
            return f"❌ Failed to list files: {file_list_result.get('error')}"
        
        files = file_list_result.get('files', [])
        
        if not files:
            return "ℹ️ No files found in Google Drive"
        
        formatted = [f"📂 Google Drive Files ({len(files)} total)\n"]
        
        for i, file in enumerate(files[:max_files], 1):
            size_mb = file.get('size', 0) / (1024 * 1024)
            formatted.append(f"{i}. **{file.get('name')}**")
            formatted.append(f"   Type: {file.get('mime_type', 'Unknown')}")
            formatted.append(f"   Size: {size_mb:.2f} MB")
            formatted.append(f"   ID: {file.get('file_id')}")
            formatted.append(f"   Modified: {file.get('modified_time', 'Unknown')}\n")
        
        return "\n".join(formatted)
    
    def is_available(self) -> bool:
        """
        Quick check if server is available
        
        Returns:
            True if server is reachable, False otherwise
        """
        health = self.health_check()
        return health.get('available', False)


# ==================== STANDALONE FUNCTIONS ====================

def quick_upload(file_path: str) -> Dict:
    """
    Convenience function for quick file upload
    
    Args:
        file_path: Path to file
        
    Returns:
        Upload result
    """
    client = DriveMCPClient()
    return client.upload_file(file_path)


def quick_list(max_results: int = 10) -> Dict:
    """
    Convenience function to list files
    
    Args:
        max_results: Max files to return
        
    Returns:
        File list result
    """
    client = DriveMCPClient()
    return client.list_files(max_results)


def test_drive_client():
    """Test Drive MCP Client"""
    print("\n" + "="*60)
    print("🧪 Testing Drive MCP Client")
    print("="*60)
    
    client = DriveMCPClient()
    
    # Test 1: Health Check
    print("\n1️⃣ Health Check")
    health = client.health_check()
    print(f"   Status: {health.get('status')}")
    print(f"   Available: {health.get('available')}")
    print(f"   Google Drive Connected: {health.get('google_drive_connected')}")
    
    if not health.get('available'):
        print("\n❌ Drive MCP server is not available!")
        print("   Make sure it's running on port 8002")
        return
    
    # Test 2: List Files
    print("\n2️⃣ List Files Test")
    files_result = client.list_files(max_results=5)
    
    if files_result.get('success'):
        print(f"✅ List successful!")
        print(f"   Total files: {files_result.get('total_files')}")
        
        # Display formatted list
        formatted = client.format_file_list(files_result, max_files=3)
        print(f"\n{formatted}")
    else:
        print(f"❌ List failed: {files_result.get('error')}")
    
    print("\n" + "="*60)
    print("✅ Drive MCP Client Test Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run tests
    test_drive_client()