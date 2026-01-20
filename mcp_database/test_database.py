"""
Test script for Database MCP Server
Run this to verify everything works!
"""
import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8003"


def print_section(title):
    """Pretty print section headers"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_server_health():
    """Test 1: Check if server is running"""
    print_section("TEST 1: Server Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is running!")
            print(f"   Status: {data.get('status')}")
            print(f"   MySQL: {data.get('mysql_status')}")
            print(f"   ChromaDB: {data.get('chroma_status')}")
            print(f"   Sync: {data.get('sync_status')}")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server!")
        print("   Make sure the server is running:")
        print("   uvicorn server:app --reload --port 8003")
        return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_root_endpoint():
    """Test 2: Check root endpoint"""
    print_section("TEST 2: Root Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Root endpoint working!")
            print(f"   Message: {data.get('message')}")
            print(f"   Service: {data.get('service')}")
            print(f"   Version: {data.get('version')}")
            return True
        else:
            print(f"❌ Failed with status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_database_stats():
    """Test 3: Get database statistics"""
    print_section("TEST 3: Database Statistics")
    
    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Stats retrieved!")
            print(f"   MySQL Connected: {data.get('mysql_connected')}")
            print(f"   ChromaDB Connected: {data.get('chroma_connected')}")
            print(f"   Total Documents: {data.get('total_documents')}")
            print(f"   MySQL Documents: {data.get('mysql_documents')}")
            print(f"   ChromaDB Documents: {data.get('chroma_documents')}")
            print(f"   Sync Status: {data.get('sync_status')}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_create_document():
    """Test 4: Create a test document"""
    print_section("TEST 4: Create Document")
    
    try:
        document = {
            "title": "Test Document from MCP",
            "content": "This is a test document created by the Database MCP test script. It demonstrates the integration between MySQL and ChromaDB for storing both relational data and vector embeddings.",
            "metadata": {
                "author": "Test Script",
                "created_by": "Database MCP Test"
            },
            "category": "test",
            "tags": ["test", "mcp", "database"]
        }
        
        print(f"📝 Creating document: {document['title']}")
        
        response = requests.post(
            f"{BASE_URL}/documents",
            json=document,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Document created!")
            print(f"   Doc ID: {data.get('doc_id')}")
            print(f"   Title: {data.get('title')}")
            print(f"   Category: {data.get('category')}")
            print(f"   MySQL ID: {data.get('mysql_id')}")
            print(f"   ChromaDB ID: {data.get('chroma_id')}")
            
            return data.get('doc_id')
        else:
            print(f"❌ Create failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_get_document(doc_id):
    """Test 5: Retrieve a document"""
    print_section("TEST 5: Get Document")
    
    if not doc_id:
        print("⚠️  Skipping - no document ID available")
        return False
    
    try:
        print(f"📖 Retrieving document: {doc_id}")
        
        response = requests.get(f"{BASE_URL}/documents/{doc_id}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Document retrieved!")
            print(f"   Title: {data.get('title')}")
            print(f"   Content length: {len(data.get('content', ''))} chars")
            print(f"   Category: {data.get('category')}")
            print(f"   Tags: {data.get('tags')}")
            return True
        else:
            print(f"❌ Get failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_search_semantic(doc_id):
    """Test 6: Semantic search"""
    print_section("TEST 6: Semantic Search")
    
    if not doc_id:
        print("⚠️  Skipping - no document ID available")
        return False
    
    try:
        query = {
            "query": "database integration and vector embeddings",
            "limit": 5,
            "search_type": "semantic"
        }
        
        print(f"🔍 Searching for: '{query['query']}'")
        
        response = requests.post(
            f"{BASE_URL}/search",
            json=query,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search completed!")
            print(f"   Query: {data.get('query')}")
            print(f"   Results found: {data.get('total_results')}")
            print(f"   Search type: {data.get('search_type')}")
            
            if data.get('results'):
                print(f"\n   Top result:")
                top = data['results'][0]
                print(f"   - Title: {top['title']}")
                print(f"   - Similarity: {top['similarity_score']:.3f}")
            
            return True
        else:
            print(f"❌ Search failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_list_documents():
    """Test 7: List all documents"""
    print_section("TEST 7: List Documents")
    
    try:
        response = requests.get(f"{BASE_URL}/documents?limit=10", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Documents listed!")
            print(f"   Total: {data.get('total')}")
            print(f"   Limit: {data.get('limit')}")
            
            if data.get('documents'):
                print(f"\n   Sample documents:")
                for doc in data['documents'][:3]:
                    print(f"   - {doc['title']} (ID: {doc['doc_id']})")
            
            return True
        else:
            print(f"❌ List failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_sync_verification():
    """Test 8: Verify sync between databases"""
    print_section("TEST 8: Sync Verification")
    
    try:
        response = requests.get(f"{BASE_URL}/sync/verify", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Sync verification complete!")
            print(f"   Status: {data.get('status')}")
            print(f"   Synced: {data.get('synced')}")
            print(f"   Failed: {data.get('failed')}")
            print(f"   Total: {data.get('total')}")
            print(f"   Message: {data.get('message')}")
            return True
        else:
            print(f"❌ Verify failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "🚀"*35)
    print("   DATABASE MCP SERVER - TEST SUITE")
    print("🚀"*35)
    print(f"\n⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📍 Server: http://localhost:8003")
    
    # Run tests
    results = []
    doc_id = None
    
    # Test 1: Health
    results.append(("Server Health", test_server_health()))
    
    if not results[0][1]:
        print("\n⚠️  Server is not running. Please start the server first!")
        print("   Command: uvicorn server:app --reload --port 8003")
        return
    
    # Test 2: Root
    results.append(("Root Endpoint", test_root_endpoint()))
    
    # Test 3: Stats
    results.append(("Database Stats", test_database_stats()))
    
    # Test 4: Create Document
    print("\n⚠️  Document creation requires both MySQL and ChromaDB to be running")
    user_input = input("   Do you want to run create/search tests? (y/n): ").lower()
    
    if user_input == 'y':
        doc_id = test_create_document()
        results.append(("Create Document", doc_id is not None))
        
        if doc_id:
            # Test 5: Get Document
            results.append(("Get Document", test_get_document(doc_id)))
            
            # Test 6: Semantic Search
            results.append(("Semantic Search", test_search_semantic(doc_id)))
            
            # Test 7: List Documents
            results.append(("List Documents", test_list_documents()))
            
            # Test 8: Sync Verification
            results.append(("Sync Verification", test_sync_verification()))
    
    # Summary
    print_section("📊 TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {test_name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! All tests passed!")
        print("   Your Database MCP Server is working perfectly!")
        print("\n💡 Next steps:")
        print("   • Try the API docs: http://localhost:8003/docs")
        print("   • Create your own documents")
        print("   • Test semantic search")
        print("   • Integrate with other MCP servers")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        print("   Common issues:")
        print("   • MySQL not running")
        print("   • ChromaDB initialization failed")
        print("   • Network timeout")
    
    print(f"\n⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "🚀"*35 + "\n")


if __name__ == "__main__":
    main()