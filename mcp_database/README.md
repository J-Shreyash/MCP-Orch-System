# Database MCP Server - MySQL + ChromaDB

A unified Model Context Protocol (MCP) server that integrates MySQL (relational database) and ChromaDB (vector database) with automatic synchronization.

## 🎯 Features

- ✅ **MySQL Integration**: Store structured data, metadata, and activity logs
- ✅ **ChromaDB Integration**: Store vector embeddings for semantic search
- ✅ **Automatic Sync**: Keep both databases coordinated
- ✅ **Semantic Search**: Find documents by meaning, not just keywords
- ✅ **Keyword Search**: Traditional text-based search
- ✅ **Hybrid Search**: Combine semantic and keyword approaches
- ✅ **RESTful API**: Complete CRUD operations
- ✅ **Activity Logging**: Track all database operations
- ✅ **Health Monitoring**: Real-time status of both databases

## 📋 Prerequisites

- Python 3.10 or higher
- MySQL Server 8.0 or higher
- 4GB RAM minimum (for embedding model)

## 🚀 Quick Start

### Step 1: Install MySQL

**Windows:**
1. Download MySQL Installer: https://dev.mysql.com/downloads/installer/
2. Run installer and select "Developer Default"
3. Set root password during installation
4. Complete installation

**Verify MySQL is running:**
```bash
mysql --version
```

### Step 2: Setup Project

```bash
# Navigate to MCP Orch System
cd "S:\Shreyash\Sepia ML intern\MCP Orch System"

# Create project folder
mkdir mcp_database
cd mcp_database

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Initialize Database

```bash
python init_database.py
```

Follow the prompts to create the MySQL database.

### Step 4: Configure Environment

Edit `.env` file with your MySQL credentials:
```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=mcp_database
```

### Step 5: Run Server

```bash
uvicorn server:app --reload --port 8003
```

Server starts on: http://localhost:8003

## 📡 API Endpoints

### Document Management

#### Create Document
```
POST /documents
```
**Body:**
```json
{
  "title": "My Document",
  "content": "Document content here",
  "category": "general",
  "tags": ["tag1", "tag2"],
  "metadata": {"author": "John"}
}
```

#### Get Document
```
GET /documents/{doc_id}
```

#### Update Document
```
PUT /documents/{doc_id}
```
**Body:**
```json
{
  "title": "Updated Title",
  "content": "Updated content"
}
```

#### Delete Document
```
DELETE /documents/{doc_id}
```

#### List All Documents
```
GET /documents?limit=100
```

### Search Operations

#### Semantic Search
```
POST /search
```
**Body:**
```json
{
  "query": "machine learning algorithms",
  "limit": 10,
  "search_type": "semantic"
}
```

**Search Types:**
- `semantic`: AI-powered meaning-based search (uses ChromaDB)
- `keyword`: Traditional text search (uses MySQL)
- `hybrid`: Combines both approaches

### System Operations

#### Health Check
```
GET /health
```

#### Database Statistics
```
GET /stats
```

#### Activity Logs
```
GET /logs?limit=50&action=insert
```

#### Verify Sync
```
GET /sync/verify
```

## 🏗️ Architecture

```
Database MCP (Port 8003)
│
├── MySQL Handler
│   ├── Stores: Documents, metadata, logs
│   ├── Operations: CRUD, search, logs
│   └── Tables: documents, activity_logs
│
├── ChromaDB Handler
│   ├── Stores: Vector embeddings
│   ├── Operations: Semantic search
│   └── Model: all-MiniLM-L6-v2
│
├── Sync Manager
│   ├── Coordinates operations
│   ├── Ensures consistency
│   └── Manages both databases
│
└── FastAPI Server
    ├── REST API
    ├── Auto documentation
    └── Health monitoring
```

## 🧪 Testing

### Run Test Suite
```bash
python test_database.py
```

### Manual Testing via API Docs
1. Open: http://localhost:8003/docs
2. Try any endpoint interactively
3. View responses in real-time

### Test with curl

**Create document:**
```bash
curl -X POST "http://localhost:8003/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Doc",
    "content": "This is a test document"
  }'
```

**Search:**
```bash
curl -X POST "http://localhost:8003/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test document",
    "search_type": "semantic"
  }'
```

## 📊 Database Schema

### MySQL - documents table
```sql
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
    chroma_id VARCHAR(255)
)
```

### MySQL - activity_logs table
```sql
CREATE TABLE activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    doc_id VARCHAR(255),
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### ChromaDB - documents collection
- Stores vector embeddings of document content
- Enables semantic similarity search
- Automatically synced with MySQL

## 🔧 Configuration

### Environment Variables (.env)
```env
MYSQL_HOST=localhost          # MySQL server host
MYSQL_USER=root              # MySQL username
MYSQL_PASSWORD=              # MySQL password
MYSQL_DATABASE=mcp_database  # Database name
CHROMA_DIR=./chroma_db       # ChromaDB storage directory
SERVER_PORT=8003             # Server port
```

## 🔍 How It Works

### Document Creation Flow:
1. User sends POST request with document data
2. Sync Manager generates unique ID
3. **ChromaDB**: Generates embedding, stores vector
4. **MySQL**: Stores document with metadata
5. Both operations succeed or rollback
6. Activity logged in MySQL

### Search Flow (Semantic):
1. User sends search query
2. Query converted to embedding (same model)
3. **ChromaDB**: Finds similar vectors
4. **MySQL**: Enriches results with metadata
5. Results ranked by similarity score
6. Response sent to user

### Sync Verification:
1. Lists all document IDs from MySQL
2. Lists all document IDs from ChromaDB
3. Compares sets to find differences
4. Reports sync status

## 🎓 Use Cases

1. **Knowledge Base**: Store and semantically search documentation
2. **Content Management**: Manage articles with AI-powered search
3. **Document Repository**: Organize files with intelligent retrieval
4. **Research Database**: Store papers with similarity search
5. **Customer Support**: FAQ database with semantic matching

## 🔒 Security Best Practices

1. **MySQL Security:**
   - Use strong passwords
   - Create dedicated MySQL user (not root)
   - Limit network access
   - Enable SSL for production

2. **API Security:**
   - Add authentication middleware
   - Implement rate limiting
   - Use HTTPS in production
   - Validate all inputs

3. **Data Security:**
   - Backup databases regularly
   - Encrypt sensitive data
   - Implement access controls
   - Monitor activity logs

## 🐛 Troubleshooting

### MySQL Connection Failed
**Solution:**
1. Check MySQL is running: `mysql --version`
2. Verify credentials in `.env`
3. Test connection: `mysql -u root -p`
4. Check firewall settings

### ChromaDB Errors
**Solution:**
1. Delete `chroma_db` folder
2. Restart server (will recreate)
3. Check disk space
4. Verify Python version (3.10+)

### Embedding Model Issues
**Solution:**
1. First run downloads 90MB model
2. Requires internet connection
3. Check antivirus isn't blocking
4. Model cached in ~/.cache/torch

### Sync Out of Sync
**Solution:**
1. Run: GET `/sync/verify`
2. Check which database has missing docs
3. Re-create missing documents
4. Or delete and recreate all

## 📈 Performance Tips

1. **Large Documents:**
   - Keep content under 10,000 characters
   - Store large files separately
   - Reference via metadata

2. **Many Documents:**
   - Use pagination (limit parameter)
   - Index frequently searched fields
   - Regular database maintenance

3. **Search Speed:**
   - Semantic search: ~100ms per query
   - Keyword search: ~10ms per query
   - Use hybrid for best results

## 🔄 Integration with Other MCPs

This server runs on port 8003:
- Google Search MCP: Port 8001 ✅
- Google Drive MCP: Port 8002 ✅
- **Database MCP: Port 8003** ✅ (you're here!)
- RAG PDF MCP: Port 8004 (upcoming)

All servers can run simultaneously!

## 📝 Example Usage

### Python Client
```python
import requests

BASE_URL = "http://localhost:8003"

# Create document
doc = {
    "title": "Machine Learning Basics",
    "content": "ML is a subset of AI...",
    "category": "education",
    "tags": ["ml", "ai"]
}
response = requests.post(f"{BASE_URL}/documents", json=doc)
doc_id = response.json()['doc_id']

# Semantic search
search = {
    "query": "artificial intelligence fundamentals",
    "search_type": "semantic",
    "limit": 5
}
results = requests.post(f"{BASE_URL}/search", json=search)
print(results.json())
```

## 🆘 Need Help?

1. Check the troubleshooting section
2. Review API docs: http://localhost:8003/docs
3. Run test script: `python test_database.py`
4. Check server logs in terminal

## 📜 License

MIT License - Free to use and modify

## 👤 Author

Shreyash Shankarrao Jadhav

---
