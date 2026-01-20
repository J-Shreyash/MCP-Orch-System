"""
Database Initialization Script
Sets up MySQL database for Database MCP
"""
import mysql.connector
from mysql.connector import Error


def create_database():
    """Create the MCP database in MySQL"""
    print("🔧 Database Initialization Script")
    print("="*60)
    
    # Get MySQL credentials
    print("\n📝 MySQL Configuration")
    host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    user = input("MySQL User (default: root): ").strip() or "root"
    password = input("MySQL Password (press Enter if none): ").strip()
    
    print(f"\n🔌 Connecting to MySQL at {host}...")
    
    try:
        # Connect to MySQL server (without database)
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            print("✅ Connected to MySQL!")
            
            cursor = connection.cursor()
            
            # Create database
            print("\n📦 Creating database 'mcp_database'...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS mcp_database")
            print("✅ Database created (or already exists)")
            
            # Use the database
            cursor.execute("USE mcp_database")
            
            # Create documents table
            print("\n📋 Creating 'documents' table...")
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
            print("✅ Documents table created")
            
            # Create activity_logs table
            print("\n📝 Creating 'activity_logs' table...")
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
            print("✅ Activity logs table created")
            
            connection.commit()
            
            print("\n" + "="*60)
            print("🎉 DATABASE SETUP COMPLETE!")
            print("="*60)
            print("\n✅ Database: mcp_database")
            print("✅ Tables: documents, activity_logs")
            print("\n💡 Next steps:")
            print("   1. Update your .env file with these credentials:")
            print(f"      MYSQL_HOST={host}")
            print(f"      MYSQL_USER={user}")
            print(f"      MYSQL_PASSWORD={password}")
            print("      MYSQL_DATABASE=mcp_database")
            print("   2. Start the server:")
            print("      uvicorn server:app --reload --port 8003")
            print("\n")
            
            cursor.close()
            connection.close()
            
            return True
    
    except Error as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   • Make sure MySQL is running")
        print("   • Check your username and password")
        print("   • Verify MySQL is installed")
        print("   • Try running MySQL Workbench to test connection")
        return False


def verify_setup():
    """Verify the database setup"""
    print("\n🔍 Would you like to verify the setup? (y/n): ", end="")
    choice = input().strip().lower()
    
    if choice == 'y':
        host = input("MySQL Host (default: localhost): ").strip() or "localhost"
        user = input("MySQL User (default: root): ").strip() or "root"
        password = input("MySQL Password: ").strip()
        
        try:
            connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database="mcp_database"
            )
            
            if connection.is_connected():
                cursor = connection.cursor()
                
                # Check tables
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                print("\n✅ Connected to mcp_database")
                print(f"✅ Tables found: {len(tables)}")
                for table in tables:
                    print(f"   - {table[0]}")
                
                # Check documents count
                cursor.execute("SELECT COUNT(*) FROM documents")
                doc_count = cursor.fetchone()[0]
                print(f"✅ Documents: {doc_count}")
                
                # Check logs count
                cursor.execute("SELECT COUNT(*) FROM activity_logs")
                log_count = cursor.fetchone()[0]
                print(f"✅ Activity logs: {log_count}")
                
                cursor.close()
                connection.close()
                
                print("\n🎉 Database is ready to use!")
        
        except Error as e:
            print(f"\n❌ Verification failed: {e}")


if __name__ == "__main__":
    print("\n" + "🚀"*30)
    print("   DATABASE MCP - INITIALIZATION")
    print("🚀"*30 + "\n")
    
    success = create_database()
    
    if success:
        verify_setup()
    
    print("\n" + "🚀"*30 + "\n")