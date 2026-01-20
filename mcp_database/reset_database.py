"""
Complete Database Reset Script
Resets both MySQL and ChromaDB to clean state
"""
import mysql.connector
import os
import shutil
from pathlib import Path

print("\n" + "🚀"*30)
print("   COMPLETE DATABASE RESET")
print("🚀"*30 + "\n")

# Configuration
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "mcp2025"
DATABASE_NAME = "mcp_database"
CHROMA_DIR = "./chroma_db"

# Step 1: Reset MySQL
print("="*60)
print("STEP 1: MySQL Reset")
print("="*60)

try:
    # Connect to MySQL server (not database)
    print("\n🔌 Connecting to MySQL...")
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )
    
    if connection.is_connected():
        cursor = connection.cursor()
        print("✅ Connected to MySQL server")
        
        # Drop database completely
        print("\n🗑️  Dropping database completely...")
        cursor.execute(f"DROP DATABASE IF EXISTS {DATABASE_NAME}")
        print(f"✅ Database '{DATABASE_NAME}' dropped")
        
        # Create fresh database
        print("\n📦 Creating fresh database...")
        cursor.execute(f"CREATE DATABASE {DATABASE_NAME}")
        print(f"✅ Database '{DATABASE_NAME}' created")
        
        # Use the new database
        cursor.execute(f"USE {DATABASE_NAME}")
        
        # Create documents table with AUTO_INCREMENT starting at 1
        print("\n📋 Creating 'documents' table...")
        cursor.execute("""
            CREATE TABLE documents (
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
            ) AUTO_INCREMENT = 1
        """)
        print("✅ Documents table created (AUTO_INCREMENT starts at 1)")
        
        # Create activity_logs table
        print("\n📝 Creating 'activity_logs' table...")
        cursor.execute("""
            CREATE TABLE activity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                action VARCHAR(100) NOT NULL,
                doc_id VARCHAR(255),
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_action (action),
                INDEX idx_timestamp (timestamp)
            ) AUTO_INCREMENT = 1
        """)
        print("✅ Activity logs table created (AUTO_INCREMENT starts at 1)")
        
        connection.commit()
        
        # Verify tables are empty
        print("\n🔍 Verifying tables...")
        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM activity_logs")
        log_count = cursor.fetchone()[0]
        
        cursor.execute("SHOW TABLE STATUS LIKE 'documents'")
        table_status = cursor.fetchone()
        auto_increment = table_status[10]  # Auto_increment column
        
        print(f"   Documents: {doc_count}")
        print(f"   Activity logs: {log_count}")
        print(f"   Next AUTO_INCREMENT ID: {auto_increment}")
        
        if doc_count == 0 and log_count == 0 and auto_increment == 1:
            print("✅ MySQL is clean and ready!")
        else:
            print("⚠️  Warning: Tables not completely clean")
        
        cursor.close()
        connection.close()
        
        print("\n✅ MySQL reset complete!")
        
except Exception as e:
    print(f"❌ MySQL Error: {e}")
    exit(1)

# Step 2: Reset ChromaDB
print("\n" + "="*60)
print("STEP 2: ChromaDB Reset")
print("="*60)

try:
    chroma_path = Path(CHROMA_DIR)
    
    if chroma_path.exists():
        print(f"\n🗑️  Deleting ChromaDB folder: {CHROMA_DIR}")
        shutil.rmtree(chroma_path)
        print("✅ ChromaDB folder deleted")
    else:
        print(f"\n✅ ChromaDB folder doesn't exist (already clean)")
    
    # Verify deletion
    if not chroma_path.exists():
        print("✅ ChromaDB is clean and ready!")
    else:
        print("⚠️  Warning: ChromaDB folder still exists")
        
except Exception as e:
    print(f"❌ ChromaDB Error: {e}")
    print("   You may need to delete it manually or close any programs using it")

# Step 3: Summary
print("\n" + "="*60)
print("🎉 RESET COMPLETE!")
print("="*60)

print("\n✅ MySQL Database: Clean (AUTO_INCREMENT = 1)")
print("✅ ChromaDB: Clean")
print("\n📋 Summary:")
print("   • Database 'mcp_database' recreated")
print("   • Tables 'documents' and 'activity_logs' created")
print("   • AUTO_INCREMENT counters reset to 1")
print("   • ChromaDB folder deleted")

print("\n💡 Next steps:")
print("   1. Start the server:")
print("      uvicorn server:app --reload --port 8003")
print("   2. Check stats:")
print("      http://localhost:8003/stats")
print("   3. Create a document - should get mysql_id: 1")

print("\n" + "🚀"*30 + "\n")