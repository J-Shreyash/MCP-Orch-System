# 🧪 Complete Testing Guide: Hybrid Search + Neo4j Integration

## 📋 Table of Contents
1. [Prerequisites Check](#prerequisites-check)
2. [Part 1: User Perspective Testing](#part-1-user-perspective-testing)
3. [Part 2: Developer/API Testing](#part-2-developerapi-testing)
4. [Part 3: Advanced Testing](#part-3-advanced-testing)
5. [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites Check

### Step 1: Verify All Services Are Running

Open your terminal and check:

```powershell
# Check if servers are running
netstat -ano | findstr "8003 8004"

# You should see:
# 0.0.0.0:8003 (Database MCP)
# 0.0.0.0:8004 (RAG PDF MCP)
```

**Expected**: Both ports should be LISTENING

### Step 2: Check Server Health

```powershell
# Test Database MCP
curl http://localhost:8003/health

# Test RAG PDF MCP
curl http://localhost:8004/health
```

**Expected**: Both should return `{"status": "healthy"}`

### Step 3: Verify Neo4j is Running (Optional)

```powershell
# If using Docker
docker ps | findstr neo4j

# Or check if port is open
netstat -ano | findstr "7687"
```

**Expected**: Neo4j should be running on port 7687

---

## 🎯 Part 1: User Perspective Testing

### Test Scenario 1: Testing via Web App (Streamlit)

#### **Test 1.1: Create a Document and Search It**

1. **Start Your Web App**:
   ```powershell
   cd "s:\Shreyash\Sepia ML intern\MCP Orch System"
   streamlit run ai_agent_system\app.py
   ```

2. **Navigate to "Create Note" Tab**:
   - Click on "Create Note" tab in your Streamlit app

3. **Create a Test Document**:
   - **Title**: `"John Smith's AI Project at Tech Corp"`
   - **Content**: 
     ```
     John Smith is the lead engineer working on an AI project at Tech Corp. 
     The project involves machine learning and neural networks. 
     Sarah Johnson is the project manager. 
     The project started in 2024 and is located in San Francisco.
     ```
   - **Category**: `"Projects"`
   - **Tags**: `["AI", "Machine Learning", "Tech Corp"]`
   - Click "Create Document"

4. **Expected Result**:
   - ✅ Success message: "Document created successfully!"
   - ✅ Document appears in "My Files" tab
   - ✅ Document should be indexed in:
     - MySQL (metadata)
     - ChromaDB (embeddings)
     - BM25 (keyword index)
     - Neo4j (entities: John Smith, Sarah Johnson, Tech Corp, San Francisco)

#### **Test 1.2: Test Different Search Types**

1. **Go to Chat Tab**

2. **Test Semantic Search**:
   - **Query**: `"Tell me about artificial intelligence projects"`
   - **Expected**: Should find your document even though it says "AI" not "artificial intelligence"
   - ✅ Semantic search finds meaning-based matches

3. **Test Keyword Search**:
   - **Query**: `"John Smith engineer"`
   - **Expected**: Should find exact keyword matches
   - ✅ Keyword search finds precise matches

4. **Test Hybrid Search** (Default):
   - **Query**: `"Who works on AI projects at Tech Corp?"`
   - **Expected**: Should find the document and show:
     - Multiple search methods combined
     - Best relevance score
     - Context about relationships (John Smith works on AI project)
   - ✅ Hybrid search combines all methods

#### **Test 1.3: Test Relationship Queries**

1. **Create Another Related Document**:
   - **Title**: `"Tech Corp Annual Report 2024"`
   - **Content**: 
     ```
     Tech Corp's AI project led by John Smith has achieved significant milestones. 
     Sarah Johnson coordinated the project timeline. 
     The company is based in San Francisco.
     ```
   - **Category**: `"Reports"`

2. **Test Relationship Search**:
   - **Query**: `"Show me all documents related to John Smith"`
   - **Expected**: Should find BOTH documents because they share entities
   - ✅ Graph search finds related documents through shared entities

3. **Test Entity-Based Query**:
   - **Query**: `"What documents mention San Francisco and Tech Corp together?"`
   - **Expected**: Should find documents with both entities
   - ✅ Graph search finds documents through entity relationships

---

### Test Scenario 2: Upload and Search PDFs

#### **Test 2.1: Upload a PDF**

1. **Go to "Upload Files" Tab**

2. **Upload a PDF** (use any PDF file):
   - Select a PDF file
   - Click "Upload"
   - Wait for processing

3. **Expected**:
   - ✅ Upload success message
   - ✅ PDF appears in "My Files" tab
   - ✅ PDF is chunked (check server logs)
   - ✅ Chunks are indexed in:
     - ChromaDB (embeddings)
     - BM25 (keywords)
     - Neo4j (entities from chunks)

#### **Test 2.2: Search PDF Content**

1. **Go to Chat Tab**

2. **Search for Content in PDF**:
   - **Query**: `"What does the PDF say about [topic in your PDF]?"`
   - **Expected**: Should find relevant chunks from the PDF
   - ✅ PDF chunks are searchable

3. **Test Hybrid Search on PDFs**:
   - **Query**: `"Summarize the key points from the uploaded PDF"`
   - **Expected**: Should retrieve best matching chunks
   - ✅ Hybrid search works on PDF chunks

---

## 🔧 Part 2: Developer/API Testing

### Test Scenario 3: Direct API Testing (Using Python)

Create a test file: `test_hybrid_search.py`

```python
import requests
import json

# Base URLs
DB_API = "http://localhost:8003"
RAG_API = "http://localhost:8004"

print("="*60)
print("🧪 Hybrid Search Testing Suite")
print("="*60)

# ============================================================
# TEST 1: Check Server Health
# ============================================================
print("\n[TEST 1] Checking Server Health...")
try:
    response = requests.get(f"{DB_API}/health")
    print(f"✅ Database MCP: {response.json()}")
except Exception as e:
    print(f"❌ Database MCP Error: {e}")

try:
    response = requests.get(f"{RAG_API}/health")
    print(f"✅ RAG PDF MCP: {response.json()}")
except Exception as e:
    print(f"❌ RAG PDF MCP Error: {e}")

# ============================================================
# TEST 2: Create a Document
# ============================================================
print("\n[TEST 2] Creating Test Document...")
doc_data = {
    "title": "AI Research Project",
    "content": "Dr. Alice Chen leads the AI research team at DataTech Inc. The project focuses on neural networks and deep learning. Dr. Bob Wilson is the co-lead researcher. The headquarters is in New York.",
    "category": "Research",
    "tags": ["AI", "Research", "Neural Networks"],
    "metadata": {
        "department": "R&D",
        "year": 2024
    }
}

try:
    response = requests.post(f"{DB_API}/documents", json=doc_data)
    result = response.json()
    if result.get("success"):
        doc_id = result.get("doc_id")
        print(f"✅ Document Created: {doc_id}")
        print(f"   Title: {result.get('title')}")
    else:
        print(f"❌ Failed: {result}")
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# TEST 3: Test Semantic Search
# ============================================================
print("\n[TEST 3] Testing Semantic Search...")
try:
    response = requests.get(
        f"{DB_API}/documents/search",
        params={
            "query": "artificial intelligence research",
            "search_type": "semantic",
            "limit": 5
        }
    )
    result = response.json()
    if result.get("success"):
        docs = result.get("documents", [])
        print(f"✅ Found {len(docs)} documents")
        for doc in docs[:2]:  # Show first 2
            print(f"   - {doc.get('title')} (Score: {doc.get('similarity_score', 0):.3f})")
    else:
        print(f"❌ Failed: {result}")
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# TEST 4: Test Keyword Search (BM25)
# ============================================================
print("\n[TEST 4] Testing Keyword Search (BM25)...")
try:
    response = requests.get(
        f"{DB_API}/documents/search",
        params={
            "query": "Alice Chen DataTech",
            "search_type": "keyword",
            "limit": 5
        }
    )
    result = response.json()
    if result.get("success"):
        docs = result.get("documents", [])
        print(f"✅ Found {len(docs)} documents")
        for doc in docs[:2]:
            print(f"   - {doc.get('title')} (Score: {doc.get('similarity_score', 0):.3f})")
    else:
        print(f"❌ Failed: {result}")
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# TEST 5: Test Hybrid Search
# ============================================================
print("\n[TEST 5] Testing Hybrid Search...")
try:
    response = requests.get(
        f"{DB_API}/documents/search",
        params={
            "query": "Who works on AI research at DataTech?",
            "search_type": "hybrid",
            "limit": 5
        }
    )
    result = response.json()
    if result.get("success"):
        docs = result.get("documents", [])
        print(f"✅ Found {len(docs)} documents")
        for doc in docs:
            print(f"   - {doc.get('title')}")
            print(f"     Final Score: {doc.get('similarity_score', 0):.3f}")
            if 'bm25_score' in doc:
                print(f"     BM25: {doc.get('bm25_score', 0):.3f}, "
                      f"Semantic: {doc.get('semantic_score', 0):.3f}, "
                      f"Graph: {doc.get('graph_score', 0):.3f}")
    else:
        print(f"❌ Failed: {result}")
except Exception as e:
    print(f"❌ Error: {e}")

# ============================================================
# TEST 6: Test Graph Search (if Neo4j available)
# ============================================================
print("\n[TEST 6] Testing Graph-Based Search...")
try:
    # Create another related document
    doc2 = {
        "title": "DataTech Annual Report",
        "content": "DataTech Inc's AI research led by Dr. Alice Chen has achieved breakthrough results. The company is based in New York.",
        "category": "Reports"
    }
    response = requests.post(f"{DB_API}/documents", json=doc2)
    
    # Search for related documents
    response = requests.get(
        f"{DB_API}/documents/search",
        params={
            "query": "Alice Chen",
            "search_type": "hybrid",
            "limit": 5
        }
    )
    result = response.json()
    if result.get("success"):
        docs = result.get("documents", [])
        print(f"✅ Found {len(docs)} documents related to 'Alice Chen'")
        print("   (Graph search should find documents sharing the entity)")
        for doc in docs:
            print(f"   - {doc.get('title')}")
except Exception as e:
    print(f"⚠️ Graph search test skipped: {e}")

# ============================================================
# TEST 7: Test RAG PDF Search
# ============================================================
print("\n[TEST 7] Testing RAG PDF Hybrid Search...")
try:
    # First, check if PDFs exist
    response = requests.get(f"{RAG_API}/pdfs?limit=1")
    pdfs = response.json().get("pdfs", [])
    
    if pdfs:
        pdf_id = pdfs[0].get("pdf_id")
        print(f"✅ Found PDF: {pdf_id}")
        
        # Test search
        search_data = {
            "query": "test query",
            "search_type": "hybrid",
            "limit": 5,
            "pdf_id": pdf_id
        }
        response = requests.post(f"{RAG_API}/search", json=search_data)
        result = response.json()
        if result.get("success"):
            chunks = result.get("chunks", [])
            print(f"✅ Found {len(chunks)} chunks")
            for chunk in chunks[:2]:
                print(f"   - Chunk {chunk.get('chunk_id')[:8]}... "
                      f"(Score: {chunk.get('similarity_score', 0):.3f})")
        else:
            print(f"❌ Search failed: {result}")
    else:
        print("ℹ️ No PDFs uploaded yet. Upload a PDF first.")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("✅ Testing Complete!")
print("="*60)
```

#### **How to Run API Tests**:

```powershell
cd "s:\Shreyash\Sepia ML intern\MCP Orch System"
python test_hybrid_search.py
```

**Expected Output**: You should see all tests passing with ✅ marks

---

### Test Scenario 4: Using Postman/Thunder Client (VS Code)

#### **Test 4.1: Create Document**

**Request**:
- **Method**: `POST`
- **URL**: `http://localhost:8003/documents`
- **Headers**: `Content-Type: application/json`
- **Body** (JSON):
```json
{
  "title": "Test Document",
  "content": "This is a test document with keywords like AI, machine learning, and data science.",
  "category": "test",
  "tags": ["test", "demo"],
  "metadata": {"test": true}
}
```

**Expected Response**:
```json
{
  "success": true,
  "doc_id": "uuid-here",
  "title": "Test Document",
  "message": "Document created successfully"
}
```

#### **Test 4.2: Test Hybrid Search**

**Request**:
- **Method**: `GET`
- **URL**: `http://localhost:8003/documents/search?query=machine%20learning&search_type=hybrid&limit=5`

**Expected Response**:
```json
{
  "success": true,
  "documents": [
    {
      "doc_id": "...",
      "title": "Test Document",
      "similarity_score": 0.85,
      "bm25_score": 0.8,
      "semantic_score": 0.9,
      "graph_score": 0.7
    }
  ],
  "count": 1,
  "search_type": "hybrid"
}
```

---

## 🔬 Part 3: Advanced Testing

### Test Scenario 5: Performance Testing

#### **Test 5.1: Search Speed Test**

```python
import time
import requests

def test_search_speed():
    query = "test query"
    search_types = ["semantic", "keyword", "hybrid"]
    
    for search_type in search_types:
        start = time.time()
        response = requests.get(
            "http://localhost:8003/documents/search",
            params={"query": query, "search_type": search_type, "limit": 10}
        )
        elapsed = (time.time() - start) * 1000  # Convert to ms
        print(f"{search_type:10s}: {elapsed:.2f}ms")
```

**Expected**:
- Keyword: ~10-50ms
- Semantic: ~50-200ms
- Hybrid: ~100-350ms

### Test Scenario 6: Edge Cases

#### **Test 6.1: Empty Query**
```python
response = requests.get(
    "http://localhost:8003/documents/search",
    params={"query": "", "limit": 10}
)
# Should handle gracefully (return empty or error)
```

#### **Test 6.2: Very Long Query**
```python
long_query = "test " * 1000  # 5000 character query
response = requests.get(
    "http://localhost:8003/documents/search",
    params={"query": long_query, "limit": 10}
)
# Should handle without crashing
```

#### **Test 6.3: Special Characters**
```python
special_query = "test@#$%^&*()[]{}|\\/:;\"'<>?,."
response = requests.get(
    "http://localhost:8003/documents/search",
    params={"query": special_query, "limit": 10}
)
# Should handle special characters
```

#### **Test 6.4: Non-Existent Category**
```python
response = requests.get(
    "http://localhost:8003/documents/search",
    params={"query": "test", "category": "nonexistent", "limit": 10}
)
# Should return empty results, not crash
```

---

## 🐛 Troubleshooting

### Problem 1: Search Returns No Results

**Check**:
1. Is the document actually created? Check MySQL:
   ```powershell
   # Check if document exists in database
   ```
2. Is BM25 index built? Check server logs for "BM25 index rebuilt"
3. Is ChromaDB working? Check server logs for ChromaDB errors

### Problem 2: Neo4j Search Not Working

**Check**:
1. Is Neo4j running?
   ```powershell
   docker ps | findstr neo4j
   ```
2. Check connection in server logs:
   ```
   ✅ Neo4j connected successfully!
   ```
3. Check if entities were extracted:
   - Look for "Extracting entities" in logs
   - Check if entities appear in Neo4j browser

### Problem 3: Slow Search Performance

**Solutions**:
1. Check document count (too many documents = slower)
2. Check if BM25 index is built (should see "BM25 index built" in logs)
3. Check Neo4j query performance (if using graph search)

### Problem 4: Entity Extraction Not Working

**Check**:
1. Is OpenAI API key set?
   ```powershell
   # Check .env file
   cat .env | findstr OPENAI
   ```
2. Check server logs for entity extraction errors
3. Check if spaCy model is installed:
   ```powershell
   python -m spacy download en_core_web_sm
   ```

---

## ✅ Testing Checklist

### User Perspective:
- [ ] Can create documents via web app
- [ ] Can search documents via chat
- [ ] Semantic search finds meaning-based matches
- [ ] Keyword search finds exact matches
- [ ] Hybrid search combines both methods
- [ ] Can upload PDFs
- [ ] Can search PDF content
- [ ] Relationship queries work (entities connected)

### Developer/API Perspective:
- [ ] `/health` endpoints work
- [ ] Can create documents via API
- [ ] `search_type=semantic` works
- [ ] `search_type=keyword` works
- [ ] `search_type=hybrid` works
- [ ] Search returns correct scores
- [ ] BM25 scores are included
- [ ] Semantic scores are included
- [ ] Graph scores are included (if Neo4j enabled)
- [ ] Results are sorted by relevance
- [ ] Pagination works (`limit` parameter)

### Performance:
- [ ] Search completes in < 500ms
- [ ] No memory leaks during multiple searches
- [ ] Can handle concurrent requests

### Error Handling:
- [ ] Empty queries handled gracefully
- [ ] Invalid search_type returns error
- [ ] Missing parameters handled
- [ ] Server continues working if Neo4j unavailable
- [ ] Server continues working if OpenAI unavailable

---

## 📊 Expected Test Results Summary

| Test | Expected Result | Status |
|------|----------------|--------|
| Health Check | Both servers return "healthy" | ✅ |
| Create Document | Document created in all systems | ✅ |
| Semantic Search | Finds meaning-based matches | ✅ |
| Keyword Search | Finds exact keyword matches | ✅ |
| Hybrid Search | Combines all methods with scores | ✅ |
| Graph Search | Finds related documents via entities | ✅ |
| PDF Upload | PDF processed and searchable | ✅ |
| PDF Search | Can search PDF chunks | ✅ |
| Performance | Search < 500ms | ✅ |
| Error Handling | Graceful degradation | ✅ |

---

## 🎯 Next Steps After Testing

1. **If All Tests Pass**: ✅ Your system is ready!
2. **If Some Fail**: Check the Troubleshooting section
3. **Performance Issues**: Consider caching or optimization
4. **Want More Features**: Check the "Next Steps" in implementation summary

---

**Happy Testing! 🚀**
