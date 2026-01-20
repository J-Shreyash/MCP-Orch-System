"""
Database MCP Client - COMPLETE PRODUCTION VERSION WITH VALIDATION
Handles MySQL and ChromaDB operations via MCP server
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav

CRITICAL FIXES:
✅ execute_sql method added (was missing!)
✅ Fixed delete_document response handling
✅ Fixed search_documents similarity calculation
✅ Fixed list_documents with validation (filters orphaned entries)
✅ Enhanced error handling throughout
✅ Better logging and debugging
✅ Prevents "Resource not found" errors by validating before display
"""

import requests
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMCPClient:
    """
    Client for Database MCP Server (MySQL + ChromaDB)
    COMPLETE VERSION - All operations + validation fixes
    """
    
    def __init__(self, base_url: str = "http://localhost:8003"):
        """
        Initialize Database MCP Client
        
        Args:
            base_url: Base URL of the Database MCP server
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.is_connected = False
        self.last_health_check = None
        
        # Retry configuration - Increased for slow server startup
        self.max_retries = 10  # More retries for startup
        self.retry_delay = 2  # Longer delay between retries
        
        print(f"📊 Database MCP Client initialized")
        print(f"   Server: {self.base_url}")
        
        # Initial health check - Non-blocking, will retry when needed
        # Don't fail initialization if server isn't ready yet
        try:
            self.health_check()
        except Exception as e:
            logger.warning(f"Initial health check failed (server may still be starting): {e}")
            print("   ⚠️  Server may still be initializing, will retry on first request...")
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict] = None,
                     params: Optional[Dict] = None,
                     timeout: int = 30) -> Optional[Dict]:
        """
        Make HTTP request with retry logic
        ENHANCED: Better error handling and logging
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint (e.g., '/documents')
            data: JSON data for POST/PUT requests
            params: Query parameters
            timeout: Request timeout in seconds
            
        Returns:
            Response JSON or None if failed
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Request: {method} {url} (attempt {attempt + 1}/{self.max_retries})")
                
                if method == "GET":
                    response = self.session.get(url, params=params, timeout=timeout)
                elif method == "POST":
                    response = self.session.post(url, json=data, timeout=timeout)
                elif method == "PUT":
                    response = self.session.put(url, json=data, timeout=timeout)
                elif method == "DELETE":
                    response = self.session.delete(url, timeout=timeout)
                else:
                    logger.error(f"Unsupported method: {method}")
                    return None
                
                # Log response
                logger.debug(f"Response: {response.status_code} - {response.text[:200]}")
                
                # Check status code
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Not found: {url}")
                    return {"success": False, "error": "Resource not found"}
                elif response.status_code == 500:
                    logger.error(f"Server error: {response.text[:200]}")
                    return {"success": False, "error": "Server error"}
                else:
                    logger.warning(f"Unexpected status {response.status_code}: {response.text[:200]}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}
            
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Max retries reached - connection failed")
                    return {"success": False, "error": "Connection failed - server not responding"}
            
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    logger.error("Max retries reached - timeout")
                    return {"success": False, "error": "Request timeout"}
            
            except Exception as e:
                logger.error(f"Request error: {e}", exc_info=True)
                return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Max retries exceeded"}
    
    def health_check(self) -> Dict:
        """
        Check database server health
        ENHANCED: Longer timeout and more retries for slow startup
        
        Returns:
            Health status with MySQL and ChromaDB info
        """
        try:
            # Use longer timeout for health check (server may be loading models)
            response = self._make_request("GET", "/health", timeout=10)
            
            if response and response.get("status") == "healthy":
                self.is_connected = True
                self.last_health_check = datetime.now()
                
                logger.info("✅ Database MCP server is healthy")
                logger.info(f"   MySQL: {response.get('mysql_status', 'unknown')}")
                logger.info(f"   ChromaDB: {response.get('chromadb_status', 'unknown')}")
                
                return {
                    "success": True,
                    "status": "healthy",
                    "mysql": response.get("mysql_status"),
                    "chromadb": response.get("chromadb_status"),
                    "timestamp": self.last_health_check.isoformat()
                }
            else:
                self.is_connected = False
                logger.warning("⚠️ Database MCP server unhealthy")
                
                return {
                    "success": False,
                    "status": "unhealthy",
                    "error": response.get("error") if response else "No response"
                }
        
        except Exception as e:
            self.is_connected = False
            logger.error(f"Health check failed: {e}")
            
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }
    
    def is_available(self) -> bool:
        """
        Quick check if server is available
        ORIGINAL FEATURE - Preserved
        
        Returns:
            True if server is responding
        """
        try:
            response = self._make_request("GET", "/health", timeout=3)
            return response is not None and response.get("status") == "healthy"
        except:
            return False
    
    def create_document(self, title: str, content: str, category: str = "general") -> Dict:
        """
        Create a new document
        ORIGINAL FEATURE - Preserved
        
        Args:
            title: Document title
            content: Document content
            category: Category (default: "general")
            
        Returns:
            {"success": bool, "document_id": int, "message": str}
        """
        if not title or not content:
            return {
                "success": False,
                "error": "Title and content are required"
            }
        
        logger.info(f"Creating document: {title} (category: {category})")
        
        try:
            data = {
                "title": title,
                "content": content,
                "category": category
            }
            
            response = self._make_request("POST", "/documents", data=data)
            
            if response and response.get("success"):
                logger.info(f"✅ Document created: {response.get('document_id')}")
                return response
            else:
                error = response.get("error", "Unknown error") if response else "No response"
                logger.error(f"Create document failed: {error}")
                return {
                    "success": False,
                    "error": error
                }
        
        except Exception as e:
            error_msg = f"Create document error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def search_documents(self, query: str, limit: int = 10, search_type: str = "hybrid") -> Dict:
        """
        Search documents using hybrid search (BM25 + Semantic + Graph)
        CRITICAL FIX: Uses hybrid search by default for better keyword matching
        Fixed similarity calculation + validation
        
        Args:
            query: Search query
            limit: Maximum results
            search_type: "semantic", "keyword", or "hybrid" (default: "hybrid" for best results)
            
        Returns:
            {"success": bool, "documents": list, "count": int}
        """
        if not query:
            return {
                "success": False,
                "error": "Query is required"
            }
        
        logger.info(f"Searching documents: '{query}' (limit: {limit}, type: {search_type})")
        
        try:
            params = {
                "query": query,
                "limit": limit,
                "search_type": search_type  # Use hybrid by default for better keyword matching
            }
            
            response = self._make_request("GET", "/documents/search", params=params)
            
            if not response:
                return {
                    "success": False,
                    "error": "No response from server",
                    "documents": []
                }
            
            # Handle both 'results' and 'documents' keys
            documents = response.get('results') or response.get('documents') or []
            
            # Convert ChromaDB distance to similarity + VALIDATE
            processed_docs = []
            for doc in documents:
                doc_id = doc.get('document_id') or doc.get('id')
                
                # CRITICAL FIX: Skip documents without valid ID
                if not doc_id or str(doc_id).lower() == 'none':
                    logger.warning("Skipping search result with invalid ID")
                    continue
                
                # Calculate similarity from distance
                distance = doc.get('distance', 1.0)
                similarity = max(0.0, min(1.0, 1 - (distance / 2)))
                
                processed_doc = {
                    'document_id': doc_id,
                    'title': doc.get('title', ''),
                    'content': doc.get('content', ''),
                    'category': doc.get('category', 'general'),
                    'similarity': similarity,
                    'distance': distance,
                    'created_at': doc.get('created_at', ''),
                    'updated_at': doc.get('updated_at', '')
                }
                processed_docs.append(processed_doc)
            
            # Sort by similarity (highest first)
            processed_docs.sort(key=lambda x: x['similarity'], reverse=True)
            
            logger.info(f"✅ Found {len(processed_docs)} valid documents")
            
            return {
                "success": True,
                "documents": processed_docs,
                "count": len(processed_docs)
            }
        
        except Exception as e:
            error_msg = f"Search error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "documents": []
            }
    
    def list_documents(self, limit: int = 100, category: Optional[str] = None, 
                      validate: bool = True) -> Dict:
        """
        List all documents
        CRITICAL FIX: Validates documents and filters orphaned entries
        
        Args:
            limit: Maximum documents to return
            category: Filter by category (optional)
            validate: Whether to validate each document exists (default: True)
            
        Returns:
            {"success": bool, "documents": list, "total_documents": int}
        """
        logger.info(f"Listing documents (limit: {limit}, category: {category}, validate: {validate})")
        
        try:
            params = {"limit": limit}
            if category:
                params["category"] = category
            
            response = self._make_request("GET", "/documents", params=params)
            
            if not response:
                return {
                    "success": False,
                    "error": "No response from server",
                    "documents": []
                }
            
            # Handle different response formats
            documents = []
            
            if isinstance(response, dict) and 'documents' in response:
                raw_docs = response.get('documents', [])
            elif isinstance(response, list):
                raw_docs = response
            else:
                logger.warning(f"Unexpected response format: {type(response)}")
                raw_docs = []
            
            # Normalize and optionally validate each document
            valid_count = 0
            invalid_count = 0
            
            for doc in raw_docs:
                if isinstance(doc, dict):
                    normalized = {
                        'document_id': doc.get('document_id') or doc.get('id') or doc.get('doc_id'),
                        'title': doc.get('title', 'Untitled'),
                        'content': doc.get('content', ''),
                        'category': doc.get('category', 'general'),
                        'created_at': doc.get('created_at', ''),
                        'updated_at': doc.get('updated_at', '')
                    }
                elif isinstance(doc, (list, tuple)):
                    normalized = {
                        'document_id': doc[0] if len(doc) > 0 else None,
                        'title': doc[1] if len(doc) > 1 else 'Untitled',
                        'content': doc[2] if len(doc) > 2 else '',
                        'category': doc[3] if len(doc) > 3 else 'general',
                        'created_at': doc[4] if len(doc) > 4 else '',
                        'updated_at': doc[5] if len(doc) > 5 else ''
                    }
                else:
                    logger.warning(f"Unexpected document format: {type(doc)}")
                    invalid_count += 1
                    continue
                
                # CRITICAL FIX: Validate document has ID
                doc_id = normalized.get('document_id')
                if not doc_id or str(doc_id).lower() == 'none':
                    logger.warning("Skipping document with invalid ID")
                    invalid_count += 1
                    continue
                
                # CRITICAL FIX: Optionally validate document actually exists
                if validate:
                    # Quick validation - try to get the document
                    verify = self.get_document(doc_id)
                    if not verify.get('success'):
                        logger.warning(f"Document {doc_id} listed but doesn't exist - skipping (orphaned entry)")
                        invalid_count += 1
                        continue
                
                documents.append(normalized)
                valid_count += 1
            
            if invalid_count > 0:
                logger.warning(f"Filtered out {invalid_count} invalid/orphaned documents")
            
            logger.info(f"✅ Listed {len(documents)} valid documents ({invalid_count} filtered)")
            
            return {
                "success": True,
                "documents": documents,
                "total_documents": len(documents),
                "filtered_count": invalid_count
            }
        
        except Exception as e:
            error_msg = f"List documents error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg,
                "documents": []
            }
    
    def get_document(self, doc_id: Any) -> Dict:
        """
        Get a specific document by ID
        ENHANCED: Better validation and error handling
        
        Args:
            doc_id: Document ID
            
        Returns:
            {"success": bool, "document": dict}
        """
        if not doc_id or str(doc_id).lower() == 'none':
            return {
                "success": False,
                "error": "Invalid document ID"
            }
        
        doc_id_str = str(doc_id).strip()
        logger.info(f"Getting document: {doc_id_str}")
        
        try:
            response = self._make_request("GET", f"/documents/{doc_id_str}", timeout=10)
            
            if response and response.get("success"):
                logger.info(f"✅ Retrieved document: {doc_id_str}")
                return response
            else:
                error = response.get("error", "Document not found") if response else "No response"
                logger.warning(f"Get document failed: {error}")
                return {
                    "success": False,
                    "error": error
                }
        
        except Exception as e:
            error_msg = f"Get document error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def update_document(self, doc_id: int, title: Optional[str] = None,
                       content: Optional[str] = None, category: Optional[str] = None) -> Dict:
        """
        Update a document
        ORIGINAL FEATURE - Preserved
        
        Args:
            doc_id: Document ID
            title: New title (optional)
            content: New content (optional)
            category: New category (optional)
            
        Returns:
            {"success": bool, "message": str}
        """
        if not doc_id:
            return {
                "success": False,
                "error": "Document ID is required"
            }
        
        if not any([title, content, category]):
            return {
                "success": False,
                "error": "At least one field must be provided for update"
            }
        
        logger.info(f"Updating document: {doc_id}")
        
        try:
            data = {}
            if title is not None:
                data["title"] = title
            if content is not None:
                data["content"] = content
            if category is not None:
                data["category"] = category
            
            response = self._make_request("PUT", f"/documents/{doc_id}", data=data)
            
            if response and response.get("success"):
                logger.info(f"✅ Document updated: {doc_id}")
                return response
            else:
                error = response.get("error", "Unknown error") if response else "No response"
                logger.error(f"Update document failed: {error}")
                return {
                    "success": False,
                    "error": error
                }
        
        except Exception as e:
            error_msg = f"Update document error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def delete_document(self, doc_id: Any) -> Dict:
        """
        Delete a document by ID
        CRITICAL FIX: Enhanced validation and error handling
        
        Args:
            doc_id: Document ID (int, str, or any type)
            
        Returns:
            {"success": bool, "message": str, "error": str}
        """
        # Validate and convert doc_id
        if doc_id is None or doc_id == '' or str(doc_id).lower() == 'none':
            logger.error(f"Invalid document ID: {doc_id} (type: {type(doc_id)})")
            return {
                "success": False,
                "error": "Invalid document ID provided"
            }
        
        doc_id_str = str(doc_id).strip()
        logger.info(f"Deleting document: {doc_id_str} (original type: {type(doc_id)})")
        
        try:
            # First verify the document exists
            verify = self.get_document(doc_id_str)
            if not verify.get('success'):
                logger.warning(f"Document {doc_id_str} doesn't exist (already deleted or orphaned entry)")
                return {
                    "success": False,
                    "error": "Document not found - may have been already deleted"
                }
            
            endpoint = f"/documents/{doc_id_str}"
            logger.debug(f"DELETE request to: {self.base_url}{endpoint}")
            
            response = self._make_request(
                method="DELETE",
                endpoint=endpoint,
                timeout=10
            )
            
            logger.debug(f"Delete response: {response}")
            
            if not response:
                logger.error("No response from delete request")
                return {
                    "success": False,
                    "error": "No response from database server - check if MCP server is running on port 8003"
                }
            
            if response.get('success'):
                logger.info(f"✅ Document deleted successfully: {doc_id_str}")
                return {
                    "success": True,
                    "message": response.get('message', 'Document deleted successfully'),
                    "document_id": doc_id_str
                }
            else:
                error = response.get('error', 'Unknown error during deletion')
                logger.error(f"Delete failed: {error}")
                return {
                    "success": False,
                    "error": error
                }
        
        except requests.exceptions.ConnectionError as e:
            error_msg = "Cannot connect to database server - ensure MCP server is running on port 8003"
            logger.error(f"{error_msg}: {e}")
            return {
                "success": False,
                "error": error_msg
            }
        
        except Exception as e:
            error_msg = f"Delete document error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def execute_sql(self, sql: str, params: Optional[Any] = None, 
                   fetch: bool = True, many: bool = False) -> Dict:
        """
        Execute raw SQL query
        CRITICAL FIX: This method was COMPLETELY MISSING!
        
        Args:
            sql: SQL query to execute
            params: Query parameters (tuple for single, list of tuples for many)
            fetch: Whether to fetch results (True for SELECT, False for INSERT/UPDATE/DELETE)
            many: Whether to execute multiple rows (executemany)
            
        Returns:
            {"success": bool, "results": list, "rows_affected": int}
        """
        if not sql or not sql.strip():
            return {
                "success": False,
                "error": "SQL query is required"
            }
        
        logger.info(f"Executing SQL: {sql[:100]}... (fetch: {fetch}, many: {many})")
        
        try:
            data = {
                "sql": sql,
                "fetch": fetch,
                "many": many
            }
            
            if params is not None:
                data["params"] = params
            
            response = self._make_request("POST", "/execute-sql", data=data, timeout=60)
            
            if not response:
                return {
                    "success": False,
                    "error": "No response from server"
                }
            
            if response.get("success"):
                result = {
                    "success": True
                }
                
                if fetch:
                    result["results"] = response.get("results", [])
                    result["row_count"] = len(result["results"])
                else:
                    result["rows_affected"] = response.get("rows_affected", 0)
                
                logger.info(f"✅ SQL executed successfully")
                return result
            else:
                error = response.get("error", "SQL execution failed")
                logger.error(f"SQL execution failed: {error}")
                return {
                    "success": False,
                    "error": error
                }
        
        except Exception as e:
            error_msg = f"Execute SQL error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": error_msg
            }
    
    def get_stats(self) -> Dict:
        """
        Get database statistics
        ORIGINAL FEATURE - Preserved
        
        Returns:
            Statistics about documents
        """
        logger.info("Getting database statistics")
        
        try:
            response = self._make_request("GET", "/stats")
            
            if response and response.get("success"):
                logger.info("✅ Statistics retrieved")
                return response
            else:
                return {
                    "success": False,
                    "error": "Failed to get statistics"
                }
        
        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup_orphaned_entries(self) -> Dict:
        """
        NEW METHOD: Clean up orphaned entries
        Identifies documents that appear in list but don't actually exist
        
        Returns:
            {"success": bool, "valid_count": int, "orphaned_count": int}
        """
        logger.info("Starting cleanup of orphaned entries...")
        
        try:
            # Get all documents without validation
            result = self.list_documents(limit=1000, validate=False)
            
            if not result.get('success'):
                return {
                    "success": False,
                    "error": "Failed to list documents"
                }
            
            all_docs = result.get('documents', [])
            valid = []
            orphaned = []
            
            for doc in all_docs:
                doc_id = doc.get('document_id')
                
                # Try to get the document
                verify = self.get_document(doc_id)
                
                if verify.get('success'):
                    valid.append(doc_id)
                else:
                    orphaned.append(doc_id)
                    logger.warning(f"Found orphaned entry: {doc_id}")
            
            logger.info(f"Cleanup complete: {len(valid)} valid, {len(orphaned)} orphaned")
            
            return {
                "success": True,
                "valid_count": len(valid),
                "orphaned_count": len(orphaned),
                "orphaned_ids": orphaned
            }
        
        except Exception as e:
            logger.error(f"Cleanup error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }


# Test function - ORIGINAL FEATURE
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 Database MCP Client - Test Mode")
    print("="*80 + "\n")
    
    # Initialize client
    client = DatabaseMCPClient()
    
    # Health check
    print("\n1️⃣ Health Check:")
    health = client.health_check()
    print(f"   Status: {health.get('status')}")
    
    if health.get("success"):
        # Test create
        print("\n2️⃣ Creating test document...")
        result = client.create_document(
            title="Test Document",
            content="This is a test document for the MCP client.",
            category="test"
        )
        print(f"   Result: {result.get('success')}")
        
        if result.get("success"):
            doc_id = result.get("document_id")
            print(f"   Document ID: {doc_id}")
            
            # Test list with validation
            print("\n3️⃣ Listing documents (with validation)...")
            list_result = client.list_documents(limit=10, validate=True)
            print(f"   Found: {list_result.get('total_documents', 0)} valid documents")
            print(f"   Filtered: {list_result.get('filtered_count', 0)} invalid")
            
            # Test search
            print("\n4️⃣ Searching documents...")
            search_result = client.search_documents("test", limit=5)
            print(f"   Found: {search_result.get('count', 0)} documents")
            
            # Test cleanup
            print("\n5️⃣ Running cleanup...")
            cleanup_result = client.cleanup_orphaned_entries()
            print(f"   Valid: {cleanup_result.get('valid_count', 0)}")
            print(f"   Orphaned: {cleanup_result.get('orphaned_count', 0)}")
            
            # Test delete
            print("\n6️⃣ Deleting test document...")
            delete_result = client.delete_document(doc_id)
            print(f"   Deleted: {delete_result.get('success')}")
    
    print("\n" + "="*80)
    print("✅ Test complete!")
    print("="*80 + "\n")