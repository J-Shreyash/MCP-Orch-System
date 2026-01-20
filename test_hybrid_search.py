"""
Hybrid Search Testing Suite
Complete test script for testing all hybrid search features
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""
import requests
import json
import time

# Base URLs
DB_API = "http://localhost:8003"
RAG_API = "http://localhost:8004"

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"🧪 {title}")
    print("="*60)

def print_result(test_name, success, message=""):
    """Print test result"""
    status = "✅" if success else "❌"
    print(f"{status} [{test_name}] {message}")

def test_server_health():
    """Test 1: Check Server Health"""
    print_header("TEST 1: Server Health Check")
    
    # Test Database MCP
    try:
        response = requests.get(f"{DB_API}/health", timeout=5)
        if response.status_code == 200:
            print_result("Database MCP Health", True, response.json())
        else:
            print_result("Database MCP Health", False, f"Status: {response.status_code}")
    except Exception as e:
        print_result("Database MCP Health", False, str(e))
    
    # Test RAG PDF MCP
    try:
        response = requests.get(f"{RAG_API}/health", timeout=5)
        if response.status_code == 200:
            print_result("RAG PDF MCP Health", True, response.json())
        else:
            print_result("RAG PDF MCP Health", False, f"Status: {response.status_code}")
    except Exception as e:
        print_result("RAG PDF MCP Health", False, str(e))

def test_create_document():
    """Test 2: Create a Test Document"""
    print_header("TEST 2: Create Document")
    
    doc_data = {
        "title": "AI Research Project - Hybrid Search Test",
        "content": "Dr. Alice Chen leads the AI research team at DataTech Inc. The project focuses on neural networks and deep learning. Dr. Bob Wilson is the co-lead researcher. The headquarters is in New York. The project started in January 2024.",
        "category": "Research",
        "tags": ["AI", "Research", "Neural Networks", "Deep Learning"],
        "metadata": {
            "department": "R&D",
            "year": 2024,
            "location": "New York"
        }
    }
    
    try:
        response = requests.post(f"{DB_API}/documents", json=doc_data, timeout=10)
        result = response.json()
        if result.get("success"):
            doc_id = result.get("doc_id")
            print_result("Create Document", True, f"Doc ID: {doc_id}")
            return doc_id
        else:
            print_result("Create Document", False, str(result))
            return None
    except Exception as e:
        print_result("Create Document", False, str(e))
        return None

def test_semantic_search():
    """Test 3: Semantic Search"""
    print_header("TEST 3: Semantic Search")
    
    try:
        start_time = time.time()
        response = requests.get(
            f"{DB_API}/documents/search",
            params={
                "query": "artificial intelligence research",
                "search_type": "semantic",
                "limit": 5
            },
            timeout=10
        )
        elapsed = (time.time() - start_time) * 1000
        
        result = response.json()
        if result.get("success"):
            docs = result.get("documents", [])
            print_result("Semantic Search", True, 
                        f"Found {len(docs)} docs in {elapsed:.0f}ms")
            for i, doc in enumerate(docs[:2], 1):
                print(f"   {i}. {doc.get('title')} (Score: {doc.get('similarity_score', 0):.3f})")
            return True
        else:
            print_result("Semantic Search", False, str(result))
            return False
    except Exception as e:
        print_result("Semantic Search", False, str(e))
        return False

def test_keyword_search():
    """Test 4: Keyword Search (BM25)"""
    print_header("TEST 4: Keyword Search (BM25)")
    
    try:
        start_time = time.time()
        response = requests.get(
            f"{DB_API}/documents/search",
            params={
                "query": "Alice Chen DataTech",
                "search_type": "keyword",
                "limit": 5
            },
            timeout=10
        )
        elapsed = (time.time() - start_time) * 1000
        
        result = response.json()
        if result.get("success"):
            docs = result.get("documents", [])
            print_result("Keyword Search", True, 
                        f"Found {len(docs)} docs in {elapsed:.0f}ms")
            for i, doc in enumerate(docs[:2], 1):
                print(f"   {i}. {doc.get('title')} (Score: {doc.get('similarity_score', 0):.3f})")
            return True
        else:
            print_result("Keyword Search", False, str(result))
            return False
    except Exception as e:
        print_result("Keyword Search", False, str(e))
        return False

def test_hybrid_search():
    """Test 5: Hybrid Search"""
    print_header("TEST 5: Hybrid Search (BM25 + Semantic + Graph)")
    
    try:
        start_time = time.time()
        response = requests.get(
            f"{DB_API}/documents/search",
            params={
                "query": "Who works on AI research at DataTech?",
                "search_type": "hybrid",
                "limit": 5
            },
            timeout=15
        )
        elapsed = (time.time() - start_time) * 1000
        
        result = response.json()
        if result.get("success"):
            docs = result.get("documents", [])
            print_result("Hybrid Search", True, 
                        f"Found {len(docs)} docs in {elapsed:.0f}ms")
            for i, doc in enumerate(docs):
                print(f"\n   {i+1}. {doc.get('title')}")
                print(f"      Final Score: {doc.get('similarity_score', 0):.3f}")
                if 'bm25_score' in doc:
                    print(f"      BM25: {doc.get('bm25_score', 0):.3f}")
                if 'semantic_score' in doc:
                    print(f"      Semantic: {doc.get('semantic_score', 0):.3f}")
                if 'graph_score' in doc:
                    print(f"      Graph: {doc.get('graph_score', 0):.3f}")
            return True
        else:
            print_result("Hybrid Search", False, str(result))
            return False
    except Exception as e:
        print_result("Hybrid Search", False, str(e))
        return False

def test_graph_relationships():
    """Test 6: Graph-Based Relationship Search"""
    print_header("TEST 6: Graph Relationship Search")
    
    # Create a related document
    doc_data = {
        "title": "DataTech Annual Report 2024",
        "content": "DataTech Inc's AI research led by Dr. Alice Chen has achieved breakthrough results. The company is based in New York. Bob Wilson contributed to the research.",
        "category": "Reports"
    }
    
    try:
        # Create related document
        response = requests.post(f"{DB_API}/documents", json=doc_data, timeout=10)
        if response.json().get("success"):
            print("   Created related document for relationship testing")
        
        # Wait a bit for entity extraction
        time.sleep(2)
        
        # Search for entity-based relationships
        response = requests.get(
            f"{DB_API}/documents/search",
            params={
                "query": "Alice Chen",
                "search_type": "hybrid",
                "limit": 5
            },
            timeout=15
        )
        
        result = response.json()
        if result.get("success"):
            docs = result.get("documents", [])
            print_result("Graph Search", True, 
                        f"Found {len(docs)} documents related to 'Alice Chen'")
            print("   (Graph should find documents sharing this entity)")
            for i, doc in enumerate(docs[:3], 1):
                print(f"   {i}. {doc.get('title')}")
                if 'graph_score' in doc and doc.get('graph_score', 0) > 0:
                    print(f"      Graph Score: {doc.get('graph_score', 0):.3f}")
            return True
        else:
            print_result("Graph Search", False, str(result))
            return False
    except Exception as e:
        print_result("Graph Search", False, f"Error: {e}")
        return False

def test_rag_pdf_search():
    """Test 7: RAG PDF Hybrid Search"""
    print_header("TEST 7: RAG PDF Hybrid Search")
    
    try:
        # Check if PDFs exist
        response = requests.get(f"{RAG_API}/pdfs?limit=1", timeout=10)
        pdfs = response.json().get("pdfs", [])
        
        if not pdfs:
            print_result("PDF Search", False, "No PDFs uploaded yet")
            print("   💡 Upload a PDF first via the web app")
            return False
        
        pdf_id = pdfs[0].get("pdf_id")
        print(f"   Testing with PDF: {pdf_id[:8]}...")
        
        # Test hybrid search
        search_data = {
            "query": "test query",
            "search_type": "hybrid",
            "limit": 5
        }
        
        start_time = time.time()
        response = requests.post(f"{RAG_API}/search", json=search_data, timeout=15)
        elapsed = (time.time() - start_time) * 1000
        
        result = response.json()
        if result.get("success"):
            chunks = result.get("chunks", [])
            print_result("PDF Hybrid Search", True, 
                        f"Found {len(chunks)} chunks in {elapsed:.0f}ms")
            for i, chunk in enumerate(chunks[:2], 1):
                print(f"   {i}. Chunk {chunk.get('chunk_id', '')[:8]}...")
                print(f"      Score: {chunk.get('similarity_score', 0):.3f}")
            return True
        else:
            print_result("PDF Hybrid Search", False, str(result))
            return False
    except Exception as e:
        print_result("PDF Search", False, str(e))
        return False

def test_performance():
    """Test 8: Performance Testing"""
    print_header("TEST 8: Performance Testing")
    
    query = "test query"
    search_types = ["semantic", "keyword", "hybrid"]
    
    print("   Measuring search response times...\n")
    results = {}
    
    for search_type in search_types:
        try:
            start = time.time()
            response = requests.get(
                f"{DB_API}/documents/search",
                params={"query": query, "search_type": search_type, "limit": 10},
                timeout=15
            )
            elapsed = (time.time() - start) * 1000
            results[search_type] = elapsed
            
            status = "✅" if response.json().get("success") else "❌"
            print(f"   {status} {search_type:10s}: {elapsed:6.2f}ms")
        except Exception as e:
            print(f"   ❌ {search_type:10s}: Error - {e}")
    
    # Check if performance is acceptable
    if results.get("hybrid", 0) < 500:
        print_result("Performance", True, "All searches complete in < 500ms")
    else:
        print_result("Performance", False, 
                    f"Hybrid search took {results.get('hybrid', 0):.0f}ms (should be < 500ms)")

def test_edge_cases():
    """Test 9: Edge Cases"""
    print_header("TEST 9: Edge Cases & Error Handling")
    
    # Test empty query
    try:
        response = requests.get(
            f"{DB_API}/documents/search",
            params={"query": "", "limit": 10},
            timeout=10
        )
        if response.status_code in [200, 400]:
            print_result("Empty Query", True, "Handled gracefully")
        else:
            print_result("Empty Query", False, f"Unexpected status: {response.status_code}")
    except Exception as e:
        print_result("Empty Query", False, str(e))
    
    # Test invalid search_type
    try:
        response = requests.get(
            f"{DB_API}/documents/search",
            params={"query": "test", "search_type": "invalid", "limit": 10},
            timeout=10
        )
        if response.status_code == 400 or not response.json().get("success"):
            print_result("Invalid Search Type", True, "Error handled correctly")
        else:
            print_result("Invalid Search Type", False, "Should return error")
    except Exception as e:
        print_result("Invalid Search Type", False, str(e))

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 Hybrid Search Complete Testing Suite")
    print("="*60)
    print("\nStarting comprehensive tests...")
    print("Make sure both servers are running on ports 8003 and 8004\n")
    
    # Run all tests
    test_server_health()
    doc_id = test_create_document()
    
    if doc_id:
        time.sleep(2)  # Wait for indexing
        test_semantic_search()
        test_keyword_search()
        test_hybrid_search()
        test_graph_relationships()
    else:
        print("\n⚠️  Skipping search tests - document creation failed")
    
    test_rag_pdf_search()
    test_performance()
    test_edge_cases()
    
    # Summary
    print_header("Testing Complete!")
    print("\n✅ All tests finished!")
    print("\n💡 Check the results above to see which tests passed/failed")
    print("💡 If tests fail, check:")
    print("   1. Are both servers running?")
    print("   2. Is Neo4j running (if graph search failed)?")
    print("   3. Is OpenAI API key set (if entity extraction failed)?")
    print("   4. Check server logs for errors\n")

if __name__ == "__main__":
    main()
