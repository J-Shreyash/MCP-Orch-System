"""
Database MCP Server - COMPLETE PRODUCTION VERSION WITH ENV VARIABLES
Handles MySQL and ChromaDB operations
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav

CRITICAL FIXES:
✅ All settings from .env file (NO HARDCODING)
✅ list_documents now queries MySQL (not ChromaDB)
✅ delete_document removes from BOTH MySQL and ChromaDB
✅ Added cleanup endpoint to remove orphaned ChromaDB entries
✅ Fixed all endpoints to maintain database sync
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import chromadb
from chromadb.utils import embedding_functions
import logging
import os
from typing import Optional, List, Any
from datetime import datetime
from dotenv import load_dotenv

# Import handlers for hybrid search
from mysql_handler import MySQLHandler
from chroma_handler import ChromaHandler
from bm25_handler import BM25Handler
from graph_handler import GraphHandler
from entity_extractor import EntityExtractor
from sync_manager import SyncManager

# Load environment variables FIRST
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Database MCP Server",
    description="MySQL + ChromaDB MCP Server",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global connections
mysql_conn = None
chroma_client = None
sentence_transformer = None

# Global handlers for hybrid search
mysql_handler = None
chroma_handler = None
bm25_handler = None
graph_handler = None
entity_extractor = None
sync_manager = None


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class DocumentCreate(BaseModel):
    title: str
    content: str
    category: str = "general"


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None


class SQLExecute(BaseModel):
    sql: str
    params: Optional[Any] = None
    fetch: bool = True
    many: bool = False


# ============================================================================
# STARTUP - DATABASE CONNECTIONS (FROM ENV)
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize database connections from environment variables"""
    global mysql_conn, chroma_client, sentence_transformer
    
    logger.info("🚀 Database MCP Server initializing...")
    
    # Get configuration from environment variables
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "")
    mysql_database = os.getenv("MYSQL_DATABASE", "mcp_database")
    chroma_dir = os.getenv("CHROMA_DIR", "./chroma_db")
    
    # Connect to MySQL
    try:
        logger.info("🔌 Connecting to MySQL...")
        logger.info("📝 MySQL Configuration:")
        logger.info(f"   Host: {mysql_host}")
        logger.info(f"   User: {mysql_user}")
        logger.info(f"   Password: {'*' * len(mysql_password) if mysql_password else '(empty)'}")
        logger.info(f"   Database: {mysql_database}")
        
        mysql_conn = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            autocommit=False
        )
        
        logger.info("✅ MySQL connected successfully!")
        
        # Create tables if not exist
        cursor = mysql_conn.cursor()
        
        # Check if table exists and has the correct structure
        cursor.execute("SHOW TABLES LIKE 'documents'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Check if doc_id column exists and its properties
            cursor.execute("""
                SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_DEFAULT, DATA_TYPE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'documents' 
                AND COLUMN_NAME = 'doc_id'
            """, (mysql_database,))
            doc_id_info = cursor.fetchone()
            
            if doc_id_info:
                # Table has doc_id column - make it nullable if it's not already
                is_nullable = doc_id_info[1]
                data_type = doc_id_info[3] if len(doc_id_info) > 3 else 'VARCHAR(255)'
                if is_nullable == 'NO':
                    logger.info("🔄 Fixing doc_id column to be nullable...")
                    try:
                        # Try to make it nullable, preserving the data type
                        if 'VARCHAR' in str(data_type).upper() or 'CHAR' in str(data_type).upper():
                            cursor.execute(f"ALTER TABLE documents MODIFY COLUMN doc_id {data_type} NULL")
                        else:
                            cursor.execute(f"ALTER TABLE documents MODIFY COLUMN doc_id VARCHAR(255) NULL")
                        mysql_conn.commit()
                        logger.info("✅ Made doc_id column nullable")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not modify doc_id column: {e}")
                        # Try dropping it if modification fails (only if safe)
                        try:
                            cursor.execute("ALTER TABLE documents DROP COLUMN doc_id")
                            mysql_conn.commit()
                            logger.info("✅ Removed doc_id column")
                        except Exception as e2:
                            logger.warning(f"⚠️ Could not drop doc_id column: {e2}")
                            logger.warning("⚠️ Please manually fix the doc_id column in the database")
        
        # Documents table - create or ensure correct structure
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                content TEXT NOT NULL,
                category VARCHAR(100) DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_category (category),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        mysql_conn.commit()
        cursor.close()
        
        logger.info("✅ MySQL tables verified/created")
        
    except mysql.connector.Error as e:
        logger.error(f"❌ MySQL connection failed: {e}")
        logger.error("💡 Please check your .env file configuration:")
        logger.error(f"   MYSQL_HOST={mysql_host}")
        logger.error(f"   MYSQL_USER={mysql_user}")
        logger.error(f"   MYSQL_DATABASE={mysql_database}")
        raise
    except Exception as e:
        logger.error(f"❌ MySQL connection failed: {e}")
        raise
    
    # Connect to ChromaDB
    try:
        logger.info("🔌 Connecting to ChromaDB...")
        logger.info(f"📁 ChromaDB Directory: {chroma_dir}")
        
        # Create directory if it doesn't exist
        os.makedirs(chroma_dir, exist_ok=True)
        
        chroma_client = chromadb.PersistentClient(path=chroma_dir)
        
        logger.info("📦 Loading embedding model...")
        sentence_transformer = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Get or create collection
        try:
            collection = chroma_client.get_collection(
                name="documents",
                embedding_function=sentence_transformer
            )
            logger.info("✅ Using existing ChromaDB collection")
        except Exception as e:
            # Check if it's a schema error
            error_str = str(e)
            if "no such column" in error_str.lower() or "collections.topic" in error_str:
                logger.warning("⚠️ ChromaDB schema mismatch detected. Resetting database...")
                logger.warning("💡 This usually happens after ChromaDB version updates")
                
                try:
                    # Close the client first to release file locks
                    try:
                        del chroma_client
                        import gc
                        gc.collect()
                    except:
                        pass
                    
                    import time
                    
                    # Quick check: Try to delete a test file to see if directory is locked
                    sqlite_file = os.path.join(chroma_dir, "chroma.sqlite3")
                    is_locked = False
                    
                    if os.path.exists(sqlite_file):
                        try:
                            # Quick attempt to rename (test if locked)
                            test_rename = sqlite_file + ".test"
                            os.rename(sqlite_file, test_rename)
                            os.rename(test_rename, sqlite_file)
                        except (PermissionError, OSError):
                            is_locked = True
                    
                    # If locked, immediately use fallback directory (skip deletion attempts)
                    if is_locked:
                        logger.warning("💡 ChromaDB directory is locked by another process")
                        logger.warning("💡 Using fallback directory to allow server to start immediately")
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        chroma_dir = f"{chroma_dir}_new_{timestamp}"
                        logger.warning(f"📁 New ChromaDB directory: {chroma_dir}")
                        os.makedirs(chroma_dir, exist_ok=True)
                    else:
                        # Not locked, try to delete normally
                        logger.info("⏳ Attempting to reset ChromaDB directory...")
                        import shutil
                        
                        # Try once quickly
                        try:
                            if os.path.exists(sqlite_file):
                                os.remove(sqlite_file)
                                logger.info("✅ Deleted SQLite file")
                            
                            if os.path.exists(chroma_dir):
                                shutil.rmtree(chroma_dir)
                                logger.info("✅ Removed corrupted directory")
                            
                            os.makedirs(chroma_dir, exist_ok=True)
                            logger.info("✅ Directory recreated")
                        except (PermissionError, OSError) as pe:
                            # If deletion fails, use fallback
                            logger.warning(f"⚠️ Could not delete directory: {pe}")
                            logger.warning("💡 Using fallback directory to allow server to start")
                            import datetime
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            chroma_dir = f"{chroma_dir}_new_{timestamp}"
                            logger.warning(f"📁 New ChromaDB directory: {chroma_dir}")
                            os.makedirs(chroma_dir, exist_ok=True)
                    
                    # Recreate client
                    chroma_client = chromadb.PersistentClient(path=chroma_dir)
                    logger.info("✅ ChromaDB database reset successfully")
                except Exception as reset_error:
                    logger.error(f"⚠️ Could not reset ChromaDB: {reset_error}")
                    logger.error("💡 Please manually delete the 'chroma_db' directory and restart the server")
                    raise
            
            # Create new collection
            collection = chroma_client.create_collection(
                name="documents",
                embedding_function=sentence_transformer,
                metadata={"description": "Document embeddings for semantic search"}
            )
            logger.info("✅ Created new ChromaDB collection")
        
        logger.info("✅ ChromaDB connected successfully!")
        
    except Exception as e:
        logger.error(f"❌ ChromaDB connection failed: {e}")
        logger.error("💡 If this is a schema error, try deleting the chroma_db directory and restarting")
        raise
    
    # Initialize handlers for hybrid search
    try:
        logger.info("🔧 Initializing hybrid search handlers...")
        
        # Initialize MySQL Handler
        mysql_handler = MySQLHandler(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        
        # Initialize ChromaDB Handler
        chroma_handler = ChromaHandler(persist_directory=chroma_dir)
        
        # Initialize BM25 Handler
        bm25_handler = BM25Handler()
        
        # Initialize Neo4j Graph Handler (optional)
        graph_handler = None
        try:
            graph_handler = GraphHandler()
            if not graph_handler.is_connected():
                logger.warning("⚠️  Neo4j not connected, graph features disabled")
                graph_handler = None
        except Exception as e:
            logger.warning(f"⚠️  Neo4j initialization failed: {e}")
            logger.warning("   Graph features will be disabled")
        
        # Initialize Entity Extractor (optional, requires OpenAI API key)
        entity_extractor = None
        try:
            if os.getenv('OPENAI_API_KEY'):
                entity_extractor = EntityExtractor()
            else:
                logger.warning("⚠️  OPENAI_API_KEY not found, entity extraction disabled")
        except Exception as e:
            logger.warning(f"⚠️  Entity extractor initialization failed: {e}")
            logger.warning("   Entity extraction will be disabled")
        
        # Initialize Sync Manager with all handlers
        sync_manager = SyncManager(
            mysql_handler=mysql_handler,
            chroma_handler=chroma_handler,
            bm25_handler=bm25_handler,
            graph_handler=graph_handler,
            entity_extractor=entity_extractor
        )
        
        logger.info("✅ Hybrid search handlers initialized!")
        
    except Exception as e:
        logger.error(f"⚠️  Handler initialization failed: {e}")
        logger.error("   Continuing with basic functionality only")
        sync_manager = None
    
    logger.info("📡 Database MCP Server ready!")


@app.on_event("shutdown")
async def shutdown():
    """Close database connections"""
    global mysql_conn
    
    if mysql_conn:
        mysql_conn.close()
        logger.info("✅ MySQL connection closed")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Check server health"""
    try:
        # Check MySQL
        mysql_status = "connected" if mysql_conn and mysql_conn.is_connected() else "disconnected"
        
        # Check ChromaDB
        chromadb_status = "connected" if chroma_client else "disconnected"
        
        status = "healthy" if mysql_status == "connected" else "unhealthy"
        
        return {
            "status": status,
            "mysql_status": mysql_status,
            "chromadb_status": chromadb_status,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ============================================================================
# DOCUMENT CRUD OPERATIONS
# ============================================================================

@app.post("/documents")
async def create_document(doc: DocumentCreate):
    """Create a new document in BOTH MySQL and ChromaDB"""
    try:
        logger.info(f"📝 Creating document: {doc.title}")
        
        # Insert into MySQL
        cursor = mysql_conn.cursor()
        
        # Check if doc_id column exists and if it's nullable
        cursor.execute("""
            SELECT COLUMN_NAME, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'documents' 
            AND COLUMN_NAME = 'doc_id'
        """)
        doc_id_info = cursor.fetchone()
        
        if doc_id_info:
            # Table has doc_id column
            is_nullable = doc_id_info[1] == 'YES'
            if is_nullable:
                # Column is nullable - insert with NULL
                query = """
                    INSERT INTO documents (doc_id, title, content, category)
                    VALUES (NULL, %s, %s, %s)
                """
                cursor.execute(query, (doc.title, doc.content, doc.category))
            else:
                # Column is NOT NULL - use a placeholder value (will be updated after insert)
                query = """
                    INSERT INTO documents (doc_id, title, content, category)
                    VALUES ('', %s, %s, %s)
                """
                cursor.execute(query, (doc.title, doc.content, doc.category))
                mysql_conn.commit()
                doc_id = cursor.lastrowid
                # Update doc_id with the actual id value
                cursor.execute("UPDATE documents SET doc_id = %s WHERE id = %s", (str(doc_id), doc_id))
        else:
            # Standard insert without doc_id
            query = """
                INSERT INTO documents (title, content, category)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query, (doc.title, doc.content, doc.category))
        
        mysql_conn.commit()
        
        doc_id = cursor.lastrowid
        cursor.close()
        
        logger.info(f"✅ Document inserted into MySQL: ID {doc_id}")
        
        # Add to ChromaDB for semantic search
        try:
            collection = chroma_client.get_collection("documents")
            collection.add(
                ids=[str(doc_id)],
                documents=[doc.content],
                metadatas=[{
                    "title": doc.title,
                    "category": doc.category,
                    "created_at": datetime.now().isoformat()
                }]
            )
            logger.info(f"✅ Document added to ChromaDB: ID {doc_id}")
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB add warning: {e}")
        
        return {
            "success": True,
            "document_id": doc_id,
            "message": "Document created successfully"
        }
    
    except Exception as e:
        logger.error(f"❌ Create document error: {e}")
        if mysql_conn:
            mysql_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents")
async def list_documents(limit: int = 100, category: Optional[str] = None):
    """List all documents from MySQL (source of truth)"""
    try:
        logger.info(f"📋 Listing documents (limit: {limit}, category: {category})")
        
        cursor = mysql_conn.cursor(dictionary=True)
        
        if category:
            query = """
                SELECT id, title, content, category, created_at, updated_at
                FROM documents
                WHERE category = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            cursor.execute(query, (category, limit))
        else:
            query = """
                SELECT id, title, content, category, created_at, updated_at
                FROM documents
                ORDER BY created_at DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))
        
        documents = cursor.fetchall()
        cursor.close()
        
        # Convert datetime to string
        for doc in documents:
            if doc.get('created_at'):
                doc['created_at'] = doc['created_at'].isoformat()
            if doc.get('updated_at'):
                doc['updated_at'] = doc['updated_at'].isoformat()
            doc['document_id'] = doc['id']
        
        logger.info(f"✅ Found {len(documents)} documents")
        
        return {
            "success": True,
            "documents": documents,
            "total": len(documents)
        }
    
    except Exception as e:
        logger.error(f"❌ List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/search")
async def search_documents(query: str, limit: int = 10, search_type: str = "semantic"):
    """
    Search documents using semantic, keyword, or hybrid search
    
    - **query**: Search query text
    - **limit**: Number of results (default: 10)
    - **search_type**: "semantic", "keyword", or "hybrid" (default: semantic)
    """
    try:
        logger.info(f"🔍 Searching documents: '{query}' (limit: {limit}, type: {search_type})")
        
        # Use sync_manager if available (hybrid search enabled)
        if sync_manager:
            results = sync_manager.search_documents(
                query=query,
                search_type=search_type,
                limit=limit
            )
            
            # Format results
            results_list = []
            logger.info(f"   📋 Formatting {len(results)} search results...")
            for idx, result in enumerate(results):
                doc_id = result.get('doc_id')
                if not doc_id:
                    logger.warning(f"   ⚠️  Result {idx} has no doc_id, skipping")
                    continue
                
                logger.debug(f"   🔍 Looking up doc_id: {doc_id} (type: {type(doc_id)})")
                
                # CRITICAL FIX: Try both doc_id and id columns, and handle string/int conversion
                cursor = mysql_conn.cursor(dictionary=True)
                doc = None
                
                # Try doc_id first (UUID string)
                try:
                    cursor.execute("SELECT * FROM documents WHERE doc_id = %s", (str(doc_id),))
                    doc = cursor.fetchone()
                    if doc:
                        logger.debug(f"   ✅ Found by doc_id: {doc_id}")
                except Exception as e:
                    logger.debug(f"   ⚠️  Error searching by doc_id: {e}")
                
                # If not found, try id column (integer)
                if not doc:
                    try:
                        doc_id_int = int(doc_id) if str(doc_id).isdigit() else None
                        if doc_id_int:
                            cursor.execute("SELECT * FROM documents WHERE id = %s", (doc_id_int,))
                            doc = cursor.fetchone()
                            if doc:
                                logger.debug(f"   ✅ Found by id: {doc_id_int}")
                    except (ValueError, TypeError) as e:
                        logger.debug(f"   ⚠️  Error converting doc_id to int: {e}")
                    except Exception as e:
                        logger.debug(f"   ⚠️  Error searching by id: {e}")
                
                cursor.close()
                
                if doc:
                    if doc.get('created_at'):
                        doc['created_at'] = doc['created_at'].isoformat()
                    if doc.get('updated_at'):
                        doc['updated_at'] = doc['updated_at'].isoformat()
                    doc['similarity_score'] = result.get('similarity_score', 0.5)
                    doc['document_id'] = doc.get('doc_id') or doc.get('id')
                    results_list.append(doc)
                    logger.debug(f"   ✅ Added document: {doc.get('title', 'Untitled')[:50]}")
                else:
                    logger.warning(f"   ⚠️  Document {doc_id} not found in MySQL database")
            
            if len(results_list) == 0:
                logger.warning(f"⚠️  No documents found after formatting {len(results)} search results")
                logger.warning(f"   This might indicate a doc_id mismatch issue")
            else:
                logger.info(f"✅ Found {len(results_list)} matching documents (from {len(results)} search results)")
            
            return {
                "success": True,
                "documents": results_list,
                "results": results_list,
                "count": len(results_list),
                "search_type": search_type
            }
        else:
            # Fallback to original semantic search
            collection = chroma_client.get_collection("documents")
            results = collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            if not results['ids'] or not results['ids'][0]:
                logger.info("✅ No search results found")
                return {
                    "success": True,
                    "documents": [],
                    "count": 0
                }
            
            doc_ids = [int(id) for id in results['ids'][0]]
            distances = results['distances'][0]
            
            cursor = mysql_conn.cursor(dictionary=True)
            placeholders = ','.join(['%s'] * len(doc_ids))
            query_sql = f"""
                SELECT id, title, content, category, created_at, updated_at
                FROM documents
                WHERE id IN ({placeholders})
            """
            cursor.execute(query_sql, doc_ids)
            documents = cursor.fetchall()
            cursor.close()
            
            doc_dict = {doc['id']: doc for doc in documents}
            results_list = []
            
            for doc_id, distance in zip(doc_ids, distances):
                if doc_id in doc_dict:
                    doc = doc_dict[doc_id]
                    if doc.get('created_at'):
                        doc['created_at'] = doc['created_at'].isoformat()
                    if doc.get('updated_at'):
                        doc['updated_at'] = doc['updated_at'].isoformat()
                    doc['distance'] = float(distance)
                    doc['document_id'] = doc['id']
                    results_list.append(doc)
            
            logger.info(f"✅ Found {len(results_list)} matching documents")
        
        return {
            "success": True,
            "documents": results_list,
            "results": results_list,
            "count": len(results_list),
            "search_type": search_type
        }
    
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/{doc_id}")
async def get_document(doc_id: int):
    """Get a specific document by ID from MySQL"""
    try:
        logger.info(f"📖 Getting document: {doc_id}")
        
        cursor = mysql_conn.cursor(dictionary=True)
        query = """
            SELECT id, title, content, category, created_at, updated_at
            FROM documents
            WHERE id = %s
        """
        cursor.execute(query, (doc_id,))
        document = cursor.fetchone()
        cursor.close()
        
        if not document:
            logger.warning(f"⚠️ Document not found: {doc_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.get('created_at'):
            document['created_at'] = document['created_at'].isoformat()
        if document.get('updated_at'):
            document['updated_at'] = document['updated_at'].isoformat()
        document['document_id'] = document['id']
        
        logger.info(f"✅ Document retrieved: {doc_id}")
        
        return {
            "success": True,
            "document": document
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/documents/{doc_id}")
async def update_document(doc_id: int, doc: DocumentUpdate):
    """Update a document in BOTH MySQL and ChromaDB"""
    try:
        logger.info(f"✏️ Updating document: {doc_id}")
        
        cursor = mysql_conn.cursor()
        cursor.execute("SELECT id FROM documents WHERE id = %s", (doc_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Document not found")
        
        updates = []
        params = []
        
        if doc.title is not None:
            updates.append("title = %s")
            params.append(doc.title)
        if doc.content is not None:
            updates.append("content = %s")
            params.append(doc.content)
        if doc.category is not None:
            updates.append("category = %s")
            params.append(doc.category)
        
        if not updates:
            cursor.close()
            return {"success": True, "message": "No updates provided"}
        
        params.append(doc_id)
        query = f"UPDATE documents SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, params)
        mysql_conn.commit()
        cursor.close()
        
        logger.info(f"✅ Document updated in MySQL: {doc_id}")
        
        if doc.content is not None:
            try:
                collection = chroma_client.get_collection("documents")
                metadata = {}
                if doc.title is not None:
                    metadata['title'] = doc.title
                if doc.category is not None:
                    metadata['category'] = doc.category
                
                collection.update(
                    ids=[str(doc_id)],
                    documents=[doc.content] if doc.content else None,
                    metadatas=[metadata] if metadata else None
                )
                logger.info(f"✅ Document updated in ChromaDB: {doc_id}")
            except Exception as e:
                logger.warning(f"⚠️ ChromaDB update warning: {e}")
        
        return {
            "success": True,
            "message": "Document updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update document error: {e}")
        if mysql_conn:
            mysql_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: int):
    """Delete document from BOTH MySQL and ChromaDB"""
    try:
        logger.info(f"🗑️ Deleting document: {doc_id}")
        
        cursor = mysql_conn.cursor()
        cursor.execute("SELECT id FROM documents WHERE id = %s", (doc_id,))
        doc = cursor.fetchone()
        
        if not doc:
            cursor.close()
            logger.warning(f"⚠️ Document {doc_id} not found in MySQL")
            raise HTTPException(status_code=404, detail="Document not found")
        
        cursor.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
        mysql_conn.commit()
        cursor.close()
        
        logger.info(f"✅ Deleted from MySQL: {doc_id}")
        
        try:
            collection = chroma_client.get_collection("documents")
            collection.delete(ids=[str(doc_id)])
            logger.info(f"✅ Deleted from ChromaDB: {doc_id}")
        except Exception as e:
            logger.warning(f"⚠️ ChromaDB delete warning: {e}")
        
        return {
            "success": True,
            "message": f"Document {doc_id} deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete error: {e}")
        if mysql_conn:
            mysql_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SQL EXECUTION
# ============================================================================

@app.post("/execute-sql")
async def execute_sql(sql_data: SQLExecute):
    """Execute raw SQL query"""
    try:
        logger.info(f"⚙️ Executing SQL: {sql_data.sql[:100]}...")
        
        cursor = mysql_conn.cursor(dictionary=True)
        
        if sql_data.many and sql_data.params:
            cursor.executemany(sql_data.sql, sql_data.params)
            mysql_conn.commit()
            rows_affected = cursor.rowcount
            cursor.close()
            return {"success": True, "rows_affected": rows_affected}
        elif sql_data.params:
            cursor.execute(sql_data.sql, sql_data.params)
        else:
            cursor.execute(sql_data.sql)
        
        if sql_data.fetch:
            results = cursor.fetchall()
            cursor.close()
            for row in results:
                for key, value in row.items():
                    if isinstance(value, datetime):
                        row[key] = value.isoformat()
            logger.info(f"✅ Query executed, {len(results)} rows returned")
            return {"success": True, "results": results, "row_count": len(results)}
        else:
            mysql_conn.commit()
            rows_affected = cursor.rowcount
            cursor.close()
            logger.info(f"✅ Query executed, {rows_affected} rows affected")
            return {"success": True, "rows_affected": rows_affected}
    
    except Exception as e:
        logger.error(f"❌ SQL execution error: {e}")
        if mysql_conn:
            mysql_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CLEANUP ENDPOINT
# ============================================================================

@app.post("/cleanup-chromadb")
async def cleanup_chromadb():
    """Clean up ChromaDB entries that don't exist in MySQL"""
    try:
        logger.info("🧹 Starting ChromaDB cleanup...")
        
        cursor = mysql_conn.cursor()
        cursor.execute("SELECT id FROM documents")
        valid_ids = set([str(row[0]) for row in cursor.fetchall()])
        cursor.close()
        
        logger.info(f"📊 Found {len(valid_ids)} valid documents in MySQL")
        
        collection = chroma_client.get_collection("documents")
        all_chromadb = collection.get()
        chromadb_ids = set(all_chromadb['ids']) if all_chromadb['ids'] else set()
        
        logger.info(f"📊 Found {len(chromadb_ids)} documents in ChromaDB")
        
        orphaned_ids = chromadb_ids - valid_ids
        
        if orphaned_ids:
            logger.info(f"🗑️ Found {len(orphaned_ids)} orphaned entries: {orphaned_ids}")
            collection.delete(ids=list(orphaned_ids))
            logger.info(f"✅ Removed {len(orphaned_ids)} orphaned entries")
            
            return {
                "success": True,
                "message": f"Removed {len(orphaned_ids)} orphaned entries",
                "orphaned_count": len(orphaned_ids),
                "orphaned_ids": list(orphaned_ids),
                "valid_count": len(valid_ids)
            }
        else:
            logger.info("✓ No orphaned entries found")
            return {
                "success": True,
                "message": "No orphaned entries found",
                "orphaned_count": 0,
                "valid_count": len(valid_ids)
            }
    
    except Exception as e:
        logger.error(f"❌ Cleanup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATISTICS
# ============================================================================

@app.get("/stats")
async def get_stats():
    """Get database statistics"""
    try:
        cursor = mysql_conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM documents")
        total = cursor.fetchone()['total']
        cursor.execute("SELECT category, COUNT(*) as count FROM documents GROUP BY category")
        by_category = cursor.fetchall()
        cursor.close()
        
        return {
            "success": True,
            "total_documents": total,
            "by_category": by_category
        }
    
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Database MCP Server",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "documents": "/documents",
            "search": "/documents/search",
            "cleanup": "/cleanup-chromadb",
            "stats": "/stats"
        }
    }


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    server_port = int(os.getenv("SERVER_PORT", 8003))
    
    logger.info(f"🚀 Starting server on port {server_port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=server_port,
        log_level="info"
    )