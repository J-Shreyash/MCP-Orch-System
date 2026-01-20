"""
RAG PDF MCP Client - WITH DELETE FUNCTIONALITY
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""

import requests
from typing import Dict, Optional
import os
from pathlib import Path


class RAGPDFMCPClient:
    """Client for RAG PDF MCP Server - WITH DELETE"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8004"):
        """Initialize RAG PDF MCP Client"""
        self.base_url = base_url.rstrip('/')
        self.timeout = 300  # 5 minutes for large PDFs
        print(f"📚 RAG PDF MCP Client initialized")
        print(f"   Server: {self.base_url}")
    
    def health_check(self) -> Dict:
        """Check if RAG PDF MCP server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "server": "RAG PDF MCP",
                    "available": True,
                    "data": data
                }
            else:
                return {
                    "status": "unhealthy",
                    "server": "RAG PDF MCP",
                    "available": False
                }
        except:
            return {
                "status": "unavailable",
                "server": "RAG PDF MCP",
                "available": False
            }
    
    def upload_pdf(self, file_path: str) -> Dict:
        """Upload PDF for processing"""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {"success": False, "error": "File not found"}
            
            file_size = file_path.stat().st_size
            print(f"\n📤 Uploading PDF: {file_path.name}")
            print(f"   Size: {file_size:,} bytes")
            print(f"   Processing may take a minute...")
            
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_path.name, f, 'application/pdf')
                }
                
                response = requests.post(
                    f"{self.base_url}/upload",
                    files=files,
                    timeout=self.timeout
                )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ PDF processed successfully!")
                print(f"   PDF ID: {data.get('pdf_id')}")
                print(f"   Pages: {data.get('page_count')}")
                print(f"   Chunks: {data.get('chunks_created')}")
                
                return {
                    "success": True,
                    "pdf_id": data.get('pdf_id'),
                    "filename": data.get('filename'),
                    "page_count": data.get('page_count'),
                    "chunks_created": data.get('chunks_created'),
                    "processing_time": data.get('processing_time'),
                    "message": data.get('message')
                }
            else:
                error_text = response.text
                print(f"❌ Upload failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {error_text}"
                }
        
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return {"success": False, "error": str(e)}
    
    def list_pdfs(self, limit: int = 100) -> Dict:
        """List all uploaded PDFs"""
        try:
            print(f"\n📋 Listing PDFs (limit: {limit})...")
            
            response = requests.get(
                f"{self.base_url}/pdfs",
                params={"limit": limit},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                pdfs = data.get('pdfs', [])
                print(f"✅ Found {len(pdfs)} PDFs")
                
                return {
                    "success": True,
                    "pdfs": pdfs,
                    "total_pdfs": data.get('total_pdfs', len(pdfs))
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_pdf(self, pdf_id: str) -> Dict:
        """Get specific PDF details"""
        try:
            response = requests.get(
                f"{self.base_url}/pdfs/{pdf_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "pdf": response.json()}
            elif response.status_code == 404:
                return {"success": False, "error": "PDF not found"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_pdf(self, pdf_id: str) -> Dict:
        """
        DELETE PDF - Deletes PDF and all associated chunks
        """
        try:
            print(f"\n🗑️ Deleting PDF: {pdf_id}")
            
            response = requests.delete(
                f"{self.base_url}/pdfs/{pdf_id}",
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ PDF deleted successfully!")
                print(f"   Chunks removed: {data.get('chunks_deleted', 0)}")
                
                return {
                    "success": True,
                    "message": data.get('message', 'PDF deleted'),
                    "chunks_deleted": data.get('chunks_deleted', 0)
                }
            elif response.status_code == 404:
                print(f"❌ PDF not found")
                return {
                    "success": False,
                    "error": "PDF not found"
                }
            else:
                error_text = response.text
                print(f"❌ Delete failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {error_text}"
                }
        
        except Exception as e:
            print(f"❌ Delete error: {e}")
            return {"success": False, "error": str(e)}
    
    def ask_question(self, question: str, pdf_id: Optional[str] = None, 
                    max_context_chunks: int = 5) -> Dict:
        """Ask a question using RAG"""
        try:
            print(f"\n❓ Asking question: '{question}'")
            
            payload = {
                "question": question,
                "max_context_chunks": max_context_chunks
            }
            
            if pdf_id:
                payload["pdf_id"] = pdf_id
            
            response = requests.post(
                f"{self.base_url}/ask",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Answer generated!")
                print(f"   Confidence: {data.get('confidence', 0):.2%}")
                
                return {
                    "success": True,
                    "answer": data.get('answer'),
                    "sources": data.get('sources', []),
                    "confidence": data.get('confidence', 0.0)
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def summarize_pdf(self, pdf_id: str, max_length: int = 500) -> Dict:
        """Generate PDF summary"""
        try:
            print(f"\n📋 Generating summary for PDF: {pdf_id}")
            
            response = requests.post(
                f"{self.base_url}/pdfs/{pdf_id}/summarize",
                json={"max_length": max_length},
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Summary generated!")
                
                return {
                    "success": True,
                    "summary": data.get('summary'),
                    "key_points": data.get('key_points', []),
                    "word_count": data.get('word_count', 0),
                    "pdf_filename": data.get('pdf_filename')
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_stats(self) -> Dict:
        """Get RAG system statistics"""
        try:
            print(f"\n📊 Getting statistics...")
            
            response = requests.get(
                f"{self.base_url}/stats",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "stats": data.get('stats', {})
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def is_available(self) -> bool:
        """Quick check if server is available"""
        health = self.health_check()
        return health.get("available", False)