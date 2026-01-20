"""
MySQL Handler - Manages relational database operations
Stores document metadata, logs, and structured data
"""
import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MySQLHandler:
    """Handles all MySQL database operations"""
    
    def __init__(self, host=None, user=None, password=None, database=None):
        """
        Initialize MySQL Handler
        
        Args:
            host: MySQL server host (default from env: MYSQL_HOST)
            user: MySQL username (default from env: MYSQL_USER)
            password: MySQL password (default from env: MYSQL_PASSWORD)
            database: Database name (default from env: MYSQL_DATABASE)
        """
        # Load from environment variables with fallbacks
        self.host = host or os.getenv('MYSQL_HOST', 'localhost')
        self.user = user or os.getenv('MYSQL_USER', 'root')
        self.password = password or os.getenv('MYSQL_PASSWORD', '')
        self.database = database or os.getenv('MYSQL_DATABASE', 'mcp_database')
        
        self.connection = None
        
        # Debug: Print configuration (hide password)
        print(f"📝 MySQL Configuration:")
        print(f"   Host: {self.host}")
        print(f"   User: {self.user}")
        print(f"   Password: {'*' * len(self.password) if self.password else '(empty)'}")
        print(f"   Database: {self.database}")
        
        self.connect()
    
    @property
    def conn(self):
        """Property to access connection as 'conn' for compatibility"""
        return self.connection
    
    def connect(self):
        """Connect to MySQL database"""
        try:
            print("🔌 Connecting to MySQL...")
            
            # Build connection config
            config = {
                'host': self.host,
                'user': self.user,
                'database': self.database
            }
            
            # Only add password if it's not empty
            if self.password:
                config['password'] = self.password
            
            self.connection = mysql.connector.connect(**config)
            
            if self.connection.is_connected():
                print("✅ MySQL connected successfully!")
                self._create_tables()
                return True
        
        except Error as e:
            print(f"❌ MySQL connection failed: {e}")
            print(f"   Attempted connection to: {self.user}@{self.host}/{self.database}")
            self.connection = None
            return False
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            cursor = self.connection.cursor()
            
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    doc_id VARCHAR(255) UNIQUE NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSON,
                    category VARCHAR(100) DEFAULT 'general',
                    tags JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    chroma_id VARCHAR(255),
                    INDEX idx_doc_id (doc_id),
                    INDEX idx_category (category),
                    INDEX idx_created (created_at)
                )
            """)
            
            # Activity logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    action VARCHAR(100) NOT NULL,
                    doc_id VARCHAR(255),
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_action (action),
                    INDEX idx_timestamp (timestamp)
                )
            """)
            
            self.connection.commit()
            print("✅ MySQL tables verified/created")
        
        except Error as e:
            print(f"❌ Error creating tables: {e}")
    
    def insert_document(self, doc_id: str, title: str, content: str, 
                       metadata: Dict = None, category: str = "general", 
                       tags: List[str] = None, chroma_id: str = None) -> bool:
        """Insert a new document"""
        try:
            cursor = self.connection.cursor()
            
            query = """
                INSERT INTO documents (doc_id, title, content, metadata, category, tags, chroma_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                doc_id,
                title,
                content,
                json.dumps(metadata or {}),
                category,
                json.dumps(tags or []),
                chroma_id
            )
            
            cursor.execute(query, values)
            self.connection.commit()
            
            # Log the action
            self.log_activity("insert", doc_id, f"Inserted document: {title}")
            
            print(f"✅ Document inserted: {doc_id}")
            return True
        
        except Error as e:
            print(f"❌ Insert failed: {e}")
            return False
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieve a document by ID (tries both doc_id and id columns)"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # CRITICAL FIX: Try doc_id first (UUID string), then id (integer)
            # This handles both new documents (with doc_id) and legacy documents (with id only)
            query = "SELECT * FROM documents WHERE doc_id = %s OR id = %s"
            
            # Try as string first
            cursor.execute(query, (str(doc_id), str(doc_id)))
            result = cursor.fetchone()
            
            # If not found and doc_id looks like an integer, try as integer
            if not result:
                try:
                    doc_id_int = int(doc_id) if str(doc_id).isdigit() else None
                    if doc_id_int:
                        cursor.execute("SELECT * FROM documents WHERE id = %s", (doc_id_int,))
                        result = cursor.fetchone()
                except (ValueError, TypeError):
                    pass
            
            if result:
                # Parse JSON fields
                result['metadata'] = json.loads(result['metadata']) if result['metadata'] else {}
                result['tags'] = json.loads(result['tags']) if result['tags'] else []
                # Convert datetime to string
                result['created_at'] = result['created_at'].isoformat()
                result['updated_at'] = result['updated_at'].isoformat()
            
            cursor.close()
            return result
        
        except Error as e:
            print(f"❌ Get document failed: {e}")
            return None
    
    def update_document(self, doc_id: str, **kwargs) -> bool:
        """Update a document"""
        try:
            cursor = self.connection.cursor()
            
            # Build dynamic update query
            update_fields = []
            values = []
            
            for key, value in kwargs.items():
                if value is not None:
                    if key in ['metadata', 'tags']:
                        update_fields.append(f"{key} = %s")
                        values.append(json.dumps(value))
                    else:
                        update_fields.append(f"{key} = %s")
                        values.append(value)
            
            if not update_fields:
                return False
            
            values.append(doc_id)
            query = f"UPDATE documents SET {', '.join(update_fields)} WHERE doc_id = %s"
            
            cursor.execute(query, values)
            self.connection.commit()
            
            # Log the action
            self.log_activity("update", doc_id, "Document updated")
            
            print(f"✅ Document updated: {doc_id}")
            return True
        
        except Error as e:
            print(f"❌ Update failed: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        try:
            cursor = self.connection.cursor()
            
            query = "DELETE FROM documents WHERE doc_id = %s"
            cursor.execute(query, (doc_id,))
            self.connection.commit()
            
            # Log the action
            self.log_activity("delete", doc_id, "Document deleted")
            
            print(f"✅ Document deleted: {doc_id}")
            return True
        
        except Error as e:
            print(f"❌ Delete failed: {e}")
            return False
    
    def search_documents(self, keyword: str = None, category: str = None, 
                        limit: int = 10) -> List[Dict]:
        """Search documents by keyword or category"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = "SELECT * FROM documents WHERE 1=1"
            params = []
            
            if keyword:
                query += " AND (title LIKE %s OR content LIKE %s)"
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            
            if category:
                query += " AND category = %s"
                params.append(category)
            
            query += f" ORDER BY created_at DESC LIMIT {limit}"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Parse JSON fields
            for result in results:
                result['metadata'] = json.loads(result['metadata']) if result['metadata'] else {}
                result['tags'] = json.loads(result['tags']) if result['tags'] else []
                result['created_at'] = result['created_at'].isoformat()
                result['updated_at'] = result['updated_at'].isoformat()
            
            return results
        
        except Error as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def get_all_documents(self, limit: int = 100) -> List[Dict]:
        """Get all documents"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = f"SELECT * FROM documents ORDER BY created_at DESC LIMIT {limit}"
            cursor.execute(query)
            
            results = cursor.fetchall()
            
            # Parse JSON fields
            for result in results:
                result['metadata'] = json.loads(result['metadata']) if result['metadata'] else {}
                result['tags'] = json.loads(result['tags']) if result['tags'] else []
                result['created_at'] = result['created_at'].isoformat()
                result['updated_at'] = result['updated_at'].isoformat()
            
            return results
        
        except Error as e:
            print(f"❌ Get all failed: {e}")
            return []
    
    def get_document_count(self) -> int:
        """Get total document count"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            count = cursor.fetchone()[0]
            return count
        except Error as e:
            print(f"❌ Count failed: {e}")
            return 0
    
    def log_activity(self, action: str, doc_id: str = None, details: str = None):
        """Log an activity"""
        try:
            cursor = self.connection.cursor()
            
            query = """
                INSERT INTO activity_logs (action, doc_id, details)
                VALUES (%s, %s, %s)
            """
            
            cursor.execute(query, (action, doc_id, details))
            self.connection.commit()
        
        except Error as e:
            print(f"⚠️  Log failed: {e}")
    
    def get_logs(self, limit: int = 50, action: str = None) -> List[Dict]:
        """Retrieve activity logs"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = "SELECT * FROM activity_logs"
            params = []
            
            if action:
                query += " WHERE action = %s"
                params.append(action)
            
            query += f" ORDER BY timestamp DESC LIMIT {limit}"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Convert datetime to string
            for result in results:
                result['timestamp'] = result['timestamp'].isoformat()
            
            return results
        
        except Error as e:
            print(f"❌ Get logs failed: {e}")
            return []
    
    def is_connected(self) -> bool:
        """Check if connected to MySQL"""
        try:
            return self.connection is not None and self.connection.is_connected()
        except:
            return False
    
    def close(self):
        """Close MySQL connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔌 MySQL connection closed")