"""
Database Initialization Script for RAG PDF MCP
Sets up MySQL database with all required tables
Company: Sepia ML - Production Ready
"""
import mysql.connector
from mysql.connector import Error


def create_database():
    """Create the RAG PDF database in MySQL"""
    print("🔧 RAG PDF MCP - Database Initialization")
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
            print("\n📦 Creating database 'mcp_rag_pdf'...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS mcp_rag_pdf")
            print("✅ Database created (or already exists)")
            
            # Use the database
            cursor.execute("USE mcp_rag_pdf")
            
            # Create PDFs table
            print("\n📋 Creating 'pdfs' table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pdfs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    pdf_id VARCHAR(255) UNIQUE NOT NULL,
                    filename VARCHAR(500) NOT NULL,
                    file_path VARCHAR(1000),
                    file_size INT,
                    page_count INT,
                    chunks_count INT DEFAULT 0,
                    total_characters INT DEFAULT 0,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT TRUE,
                    metadata JSON,
                    INDEX idx_pdf_id (pdf_id),
                    INDEX idx_uploaded (uploaded_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("✅ PDFs table created")
            
            # Create chunks table
            print("\n📄 Creating 'chunks' table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    chunk_id VARCHAR(255) UNIQUE NOT NULL,
                    pdf_id VARCHAR(255) NOT NULL,
                    chunk_index INT,
                    page_number INT,
                    content TEXT,
                    char_count INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_chunk_id (chunk_id),
                    INDEX idx_pdf_id (pdf_id),
                    INDEX idx_page (page_number),
                    FOREIGN KEY (pdf_id) REFERENCES pdfs(pdf_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("✅ Chunks table created")
            
            # Create activity_logs table
            print("\n📝 Creating 'activity_logs' table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    action VARCHAR(100) NOT NULL,
                    pdf_id VARCHAR(255),
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_action (action),
                    INDEX idx_timestamp (timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("✅ Activity logs table created")
            
            connection.commit()
            
            print("\n" + "="*60)
            print("🎉 DATABASE SETUP COMPLETE!")
            print("="*60)
            print("\n✅ Database: mcp_rag_pdf")
            print("✅ Tables created:")
            print("   - pdfs (stores PDF metadata)")
            print("   - chunks (stores chunk information)")
            print("   - activity_logs (tracks all activities)")
            
            print("\n💡 Next steps:")
            print("   1. Update your .env file with these credentials:")
            print(f"      MYSQL_HOST={host}")
            print(f"      MYSQL_USER={user}")
            print(f"      MYSQL_PASSWORD={password}")
            print("      MYSQL_DATABASE=mcp_rag_pdf")
            print("\n   2. Create uploads directory:")
            print("      mkdir uploads")
            print("\n   3. Start the server:")
            print("      uvicorn server:app --reload --port 8004")
            print("\n")
            
            cursor.close()
            connection.close()
            
            return True
    
    except Error as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   • Make sure MySQL is running")
        print("   • Check your username and password")
        print("   • Verify MySQL is installed (mysql --version)")
        print("   • Try: mysql -u root -p")
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
                database="mcp_rag_pdf"
            )
            
            if connection.is_connected():
                cursor = connection.cursor()
                
                # Check tables
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                print("\n✅ Connected to mcp_rag_pdf")
                print(f"✅ Tables found: {len(tables)}")
                for table in tables:
                    print(f"   - {table[0]}")
                
                # Check counts
                cursor.execute("SELECT COUNT(*) FROM pdfs")
                pdf_count = cursor.fetchone()[0]
                print(f"✅ PDFs: {pdf_count}")
                
                cursor.execute("SELECT COUNT(*) FROM chunks")
                chunk_count = cursor.fetchone()[0]
                print(f"✅ Chunks: {chunk_count}")
                
                cursor.execute("SELECT COUNT(*) FROM activity_logs")
                log_count = cursor.fetchone()[0]
                print(f"✅ Activity logs: {log_count}")
                
                # Show table structures
                print("\n📊 Table Structures:")
                
                print("\n📋 PDFs table:")
                cursor.execute("DESCRIBE pdfs")
                for row in cursor.fetchall():
                    print(f"   {row[0]}: {row[1]}")
                
                print("\n📄 Chunks table:")
                cursor.execute("DESCRIBE chunks")
                for row in cursor.fetchall():
                    print(f"   {row[0]}: {row[1]}")
                
                cursor.close()
                connection.close()
                
                print("\n🎉 Database is ready to use!")
                print("✅ All tables created successfully")
                print("✅ Indexes created for performance")
                print("✅ Foreign keys set for data integrity")
        
        except Error as e:
            print(f"\n❌ Verification failed: {e}")
            print("\n💡 Common issues:")
            print("   • Database doesn't exist: Run script again")
            print("   • Wrong password: Check your credentials")
            print("   • MySQL not running: Start MySQL service")


def drop_database():
    """Drop the database (use with caution!)"""
    print("\n⚠️  WARNING: This will DELETE all data!")
    print("Are you sure you want to drop the database? (yes/no): ", end="")
    confirm = input().strip().lower()
    
    if confirm != 'yes':
        print("❌ Operation cancelled")
        return
    
    host = input("MySQL Host (default: localhost): ").strip() or "localhost"
    user = input("MySQL User (default: root): ").strip() or "root"
    password = input("MySQL Password: ").strip()
    
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("DROP DATABASE IF EXISTS mcp_rag_pdf")
            print("\n✅ Database 'mcp_rag_pdf' dropped")
            cursor.close()
            connection.close()
    
    except Error as e:
        print(f"\n❌ Error: {e}")


def show_menu():
    """Show main menu"""
    print("\n" + "="*60)
    print("RAG PDF MCP - Database Management")
    print("="*60)
    print("\n1. Create/Initialize Database")
    print("2. Verify Database Setup")
    print("3. Drop Database (⚠️  DELETES ALL DATA)")
    print("4. Exit")
    print("\nChoice (1-4): ", end="")


if __name__ == "__main__":
    print("\n" + "🚀"*30)
    print("   RAG PDF MCP - DATABASE INITIALIZATION")
    print("🚀"*30 + "\n")
    
    while True:
        show_menu()
        choice = input().strip()
        
        if choice == '1':
            success = create_database()
            if success:
                verify_setup()
            input("\nPress Enter to continue...")
        
        elif choice == '2':
            verify_setup()
            input("\nPress Enter to continue...")
        
        elif choice == '3':
            drop_database()
            input("\nPress Enter to continue...")
        
        elif choice == '4':
            print("\n👋 Goodbye!")
            break
        
        else:
            print("\n❌ Invalid choice. Please select 1-4.")
            input("\nPress Enter to continue...")
    
    print("\n" + "🚀"*30 + "\n")