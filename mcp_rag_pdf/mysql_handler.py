"""
MySQL Handler - Database Operations for RAG PDF System
WITH DELETE FUNCTIONALITY + Enhanced Features
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""

import pymysql
from typing import Dict, List, Optional
from datetime import datetime
import os


class MySQLHandler:
    """Handles all MySQL database operations"""
    
    def __init__(self):
        """Initialize MySQL connection"""
        self.host = os.getenv('MYSQL_HOST', 'localhost')
        self.user = os.getenv('MYSQL_USER', 'root')
        self.password = os.getenv('MYSQL_PASSWORD', '')
        self.database = os.getenv('MYSQL_DATABASE', 'mcp_rag_pdf')
        
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Establish MySQL connection"""
        try:
            self.conn = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            print(f"✅ MySQL connected: {self.database}")
        
        except Exception as e:
            print(f"❌ MySQL connection failed: {e}")
            raise
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            cursor = self.conn.cursor()
            
            # PDFs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pdfs (
                    pdf_id VARCHAR(100) PRIMARY KEY,
                    filename VARCHAR(500) NOT NULL,
                    file_size BIGINT,
                    page_count INT,
                    chunks_count INT DEFAULT 0,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_filename (filename(255)),
                    INDEX idx_uploaded (uploaded_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # Activity log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    activity_type VARCHAR(50),
                    pdf_id VARCHAR(100),
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_pdf (pdf_id),
                    INDEX idx_type (activity_type),
                    INDEX idx_created (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            self.conn.commit()
            cursor.close()
            print("✅ MySQL tables verified/created")
        
        except Exception as e:
            print(f"❌ Table creation failed: {e}")
            raise
    
    def insert_pdf(self, pdf_id: str, filename: str, file_size: int, 
                   page_count: int, chunks_count: int) -> bool:
        """Insert new PDF record"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO pdfs (pdf_id, filename, file_size, page_count, chunks_count)
                VALUES (%s, %s, %s, %s, %s)
            """, (pdf_id, filename, file_size, page_count, chunks_count))
            
            self.conn.commit()
            cursor.close()
            
            print(f"✅ PDF metadata saved to MySQL: {filename}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to insert PDF: {e}")
            self.conn.rollback()
            return False
    
    def get_pdf(self, pdf_id: str) -> Optional[Dict]:
        """Get PDF by ID"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT * FROM pdfs WHERE pdf_id = %s
            """, (pdf_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            return result
        
        except Exception as e:
            print(f"❌ Error getting PDF: {e}")
            return None
    
    def list_pdfs(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """List all PDFs"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT * FROM pdfs 
                ORDER BY uploaded_at DESC 
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            results = cursor.fetchall()
            cursor.close()
            
            return results
        
        except Exception as e:
            print(f"❌ Error listing PDFs: {e}")
            return []
    
    def get_total_pdfs(self) -> int:
        """Get total number of PDFs"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as total FROM pdfs")
            result = cursor.fetchone()
            cursor.close()
            
            return result['total'] if result else 0
        
        except Exception as e:
            print(f"❌ Error counting PDFs: {e}")
            return 0
    
    def delete_pdf(self, pdf_id: str) -> bool:
        """
        DELETE PDF - Delete PDF record from database
        Returns True if successful
        """
        try:
            print(f"\n🗑️ Deleting PDF from MySQL: {pdf_id}")
            
            cursor = self.conn.cursor()
            
            # Delete PDF record
            cursor.execute(
                "DELETE FROM pdfs WHERE pdf_id = %s",
                (pdf_id,)
            )
            
            rows_deleted = cursor.rowcount
            
            self.conn.commit()
            cursor.close()
            
            if rows_deleted > 0:
                print(f"✅ PDF record deleted from MySQL")
                return True
            else:
                print(f"⚠️ No PDF record found to delete")
                return False
        
        except Exception as e:
            print(f"❌ Error deleting PDF from MySQL: {e}")
            self.conn.rollback()
            return False
    
    def update_chunks_count(self, pdf_id: str, chunks_count: int) -> bool:
        """Update chunks count for a PDF"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                UPDATE pdfs SET chunks_count = %s WHERE pdf_id = %s
            """, (chunks_count, pdf_id))
            
            self.conn.commit()
            cursor.close()
            
            return True
        
        except Exception as e:
            print(f"❌ Error updating chunks count: {e}")
            self.conn.rollback()
            return False
    
    def log_activity(self, activity_type: str, pdf_id: str, details: str = ""):
        """Log activity"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                INSERT INTO activity_log (activity_type, pdf_id, details)
                VALUES (%s, %s, %s)
            """, (activity_type, pdf_id, details))
            
            self.conn.commit()
            cursor.close()
        
        except Exception as e:
            print(f"⚠️ Failed to log activity: {e}")
    
    def get_recent_activity(self, limit: int = 20) -> List[Dict]:
        """Get recent activity logs"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT * FROM activity_log 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            
            results = cursor.fetchall()
            cursor.close()
            
            return results
        
        except Exception as e:
            print(f"❌ Error getting activity: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            cursor = self.conn.cursor()
            
            # Total PDFs
            cursor.execute("SELECT COUNT(*) as total FROM pdfs")
            total_pdfs = cursor.fetchone()['total']
            
            # Total chunks
            cursor.execute("SELECT SUM(chunks_count) as total FROM pdfs")
            result = cursor.fetchone()
            total_chunks = result['total'] if result['total'] else 0
            
            # Total pages
            cursor.execute("SELECT SUM(page_count) as total FROM pdfs")
            result = cursor.fetchone()
            total_pages = result['total'] if result['total'] else 0
            
            # Total storage
            cursor.execute("SELECT SUM(file_size) as total FROM pdfs")
            result = cursor.fetchone()
            total_storage = result['total'] if result['total'] else 0
            
            cursor.close()
            
            return {
                'total_pdfs': total_pdfs,
                'total_chunks': total_chunks,
                'total_pages': total_pages,
                'storage_used_mb': total_storage / (1024 * 1024)
            }
        
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {
                'total_pdfs': 0,
                'total_chunks': 0,
                'total_pages': 0,
                'storage_used_mb': 0
            }
    
    def search_pdfs(self, query: str, limit: int = 10) -> List[Dict]:
        """Search PDFs by filename"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT * FROM pdfs 
                WHERE filename LIKE %s 
                ORDER BY uploaded_at DESC 
                LIMIT %s
            """, (f"%{query}%", limit))
            
            results = cursor.fetchall()
            cursor.close()
            
            return results
        
        except Exception as e:
            print(f"❌ Error searching PDFs: {e}")
            return []
    
    def get_pdf_by_filename(self, filename: str) -> Optional[Dict]:
        """Get PDF by filename"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT * FROM pdfs WHERE filename = %s
            """, (filename,))
            
            result = cursor.fetchone()
            cursor.close()
            
            return result
        
        except Exception as e:
            print(f"❌ Error getting PDF by filename: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✅ MySQL connection closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()