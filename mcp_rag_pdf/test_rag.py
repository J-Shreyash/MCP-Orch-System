"""
Test script for RAG PDF MCP Server
Comprehensive testing suite for all endpoints
"""
import requests
import json
from datetime import datetime
from pathlib import Path


BASE_URL = "http://localhost:8004"


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
            print(f"   Total PDFs: {data.get('total_pdfs')}")
            print(f"   Total Chunks: {data.get('total_chunks')}")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server!")
        print("   Make sure the server is running:")
        print("   uvicorn server:app --reload --port 8004")
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
            
            if data.get('endpoints'):
                print(f"\n   Available endpoints:")
                for key, desc in list(data['endpoints'].items())[:5]:
                    print(f"   • {desc}")
            
            return True
        else:
            print(f"❌ Failed with status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_stats_endpoint():
    """Test 3: Get statistics"""
    print_section("TEST 3: Statistics")
    
    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Stats retrieved!")
            print(f"   Total PDFs: {data.get('total_pdfs')}")
            print(f"   Total Chunks: {data.get('total_chunks')}")
            print(f"   Total Pages: {data.get('total_pages')}")
            print(f"   MySQL Connected: {data.get('mysql_connected')}")
            print(f"   ChromaDB Connected: {data.get('chroma_connected')}")
            print(f"   Storage Used: {data.get('storage_used_mb', 0):.2f} MB")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def create_sample_pdf():
    """Create a sample PDF for testing"""
    print("📝 Creating sample PDF...")
    
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        filename = "test_sample.pdf"
        c = canvas.Canvas(filename, pagesize=letter)
        
        # Page 1
        c.drawString(100, 750, "Machine Learning Overview")
        c.drawString(100, 700, "Machine learning is a subset of artificial intelligence that")
        c.drawString(100, 680, "enables systems to learn and improve from experience without")
        c.drawString(100, 660, "being explicitly programmed.")
        c.drawString(100, 620, "Key Concepts:")
        c.drawString(120, 600, "- Supervised Learning")
        c.drawString(120, 580, "- Unsupervised Learning")
        c.drawString(120, 560, "- Reinforcement Learning")
        c.showPage()
        
        # Page 2
        c.drawString(100, 750, "Deep Learning")
        c.drawString(100, 700, "Deep learning is a subset of machine learning based on")
        c.drawString(100, 680, "artificial neural networks. It enables computers to learn")
        c.drawString(100, 660, "from large amounts of data.")
        c.showPage()
        
        c.save()
        print(f"✅ Created sample PDF: {filename}")
        return filename
    
    except ImportError:
        print("⚠️  reportlab not installed, using text-based PDF simulation")
        return None
    except Exception as e:
        print(f"⚠️  Could not create PDF: {e}")
        return None


def test_upload_pdf():
    """Test 4: Upload a PDF"""
    print_section("TEST 4: Upload PDF")
    
    # Check if user has a PDF
    print("📂 PDF Upload Test")
    print("\nOptions:")
    print("1. Create sample PDF (requires reportlab)")
    print("2. Use your own PDF file")
    print("3. Skip this test")
    
    choice = input("\nChoice (1-3): ").strip()
    
    pdf_path = None
    
    if choice == '1':
        pdf_path = create_sample_pdf()
    elif choice == '2':
        pdf_path = input("Enter PDF file path: ").strip()
        if not Path(pdf_path).exists():
            print(f"❌ File not found: {pdf_path}")
            return None
    else:
        print("⚠️  Skipping PDF upload test")
        return None
    
    if not pdf_path:
        return None
    
    try:
        print(f"\n📤 Uploading: {pdf_path}")
        
        with open(pdf_path, 'rb') as f:
            files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
            response = requests.post(
                f"{BASE_URL}/upload",
                files=files,
                timeout=60  # PDF processing can take time
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload successful!")
            print(f"   PDF ID: {data.get('pdf_id')}")
            print(f"   Filename: {data.get('filename')}")
            print(f"   Pages: {data.get('page_count')}")
            print(f"   File Size: {data.get('file_size')} bytes")
            print(f"   Chunks Created: {data.get('chunks_created')}")
            print(f"   Message: {data.get('message')}")
            
            # Clean up sample PDF
            if choice == '1' and Path(pdf_path).exists():
                try:
                    Path(pdf_path).unlink()
                    print(f"   🧹 Cleaned up sample PDF")
                except:
                    pass
            
            return data.get('pdf_id')
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_list_pdfs():
    """Test 5: List all PDFs"""
    print_section("TEST 5: List PDFs")
    
    try:
        response = requests.get(f"{BASE_URL}/pdfs", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PDFs listed!")
            print(f"   Total PDFs: {data.get('total_pdfs')}")
            
            if data.get('pdfs'):
                print(f"\n   📚 PDFs:")
                for pdf in data['pdfs'][:5]:  # Show first 5
                    print(f"\n   📄 {pdf['filename']}")
                    print(f"      ID: {pdf['pdf_id']}")
                    print(f"      Pages: {pdf['page_count']}")
                    print(f"      Chunks: {pdf['chunks_count']}")
                    print(f"      Uploaded: {pdf['uploaded_at']}")
            else:
                print("   📭 No PDFs uploaded yet")
            
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_search_pdf(pdf_id=None):
    """Test 6: Search in PDFs"""
    print_section("TEST 6: Search PDFs")
    
    if not pdf_id:
        print("⚠️  No PDF ID provided, searching all PDFs")
    
    query = input("\n🔍 Enter search query (or press Enter for default): ").strip()
    if not query:
        query = "machine learning"
    
    try:
        search_data = {
            "query": query,
            "limit": 5,
            "include_context": True
        }
        
        if pdf_id:
            search_data["pdf_id"] = pdf_id
        
        print(f"\n🔍 Searching for: '{query}'")
        
        response = requests.post(
            f"{BASE_URL}/search",
            json=search_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search completed!")
            print(f"   Query: {data.get('query')}")
            print(f"   Results found: {data.get('total_results')}")
            
            if data.get('results'):
                print(f"\n   📋 Results:")
                for i, result in enumerate(data['results'], 1):
                    print(f"\n   {i}. {result['pdf_filename']}")
                    print(f"      Page: {result.get('page_number', 'N/A')}")
                    print(f"      Similarity: {result['similarity_score']:.3f}")
                    print(f"      Content: {result['content'][:100]}...")
            else:
                print("   No results found")
            
            return True
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_rag_query(pdf_id=None):
    """Test 7: RAG Question Answering"""
    print_section("TEST 7: RAG Question Answering")
    
    question = input("\n❓ Enter your question (or press Enter for default): ").strip()
    if not question:
        question = "What is machine learning?"
    
    try:
        rag_data = {
            "question": question,
            "max_context_chunks": 5,
            "include_sources": True
        }
        
        if pdf_id:
            rag_data["pdf_id"] = pdf_id
        
        print(f"\n🤖 Processing question: '{question}'")
        print("   (This may take a moment...)")
        
        response = requests.post(
            f"{BASE_URL}/rag/ask",
            json=rag_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Answer generated!")
            print(f"\n📝 Question: {data.get('question')}")
            print(f"\n💡 Answer:")
            print(f"   {data.get('answer')}")
            print(f"\n📊 Confidence: {data.get('confidence', 0):.2%}")
            print(f"📚 Sources used: {len(data.get('sources', []))}")
            
            if data.get('sources'):
                print(f"\n📖 Source documents:")
                for i, source in enumerate(data['sources'][:3], 1):
                    print(f"\n   {i}. {source['pdf_filename']} (Page {source.get('page_number', 'N/A')})")
                    print(f"      Relevance: {source['similarity_score']:.3f}")
            
            return True
        else:
            print(f"❌ RAG query failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_summarize_pdf(pdf_id):
    """Test 8: PDF Summarization"""
    print_section("TEST 8: PDF Summarization")
    
    if not pdf_id:
        print("⚠️  No PDF ID provided, cannot test summarization")
        return False
    
    try:
        summary_data = {
            "pdf_id": pdf_id,
            "summary_type": "extractive",
            "max_length": 200
        }
        
        print(f"\n📋 Generating summary for PDF: {pdf_id}")
        print("   (This may take a moment...)")
        
        response = requests.post(
            f"{BASE_URL}/summarize",
            json=summary_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Summary generated!")
            print(f"\n📄 PDF: {data.get('pdf_filename')}")
            print(f"\n📝 Summary ({data.get('word_count')} words):")
            print(f"   {data.get('summary')}")
            
            if data.get('key_points'):
                print(f"\n🔑 Key Points:")
                for i, point in enumerate(data['key_points'], 1):
                    print(f"   {i}. {point}")
            
            return True
        else:
            print(f"❌ Summarization failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "🚀"*35)
    print("   RAG PDF MCP SERVER - TEST SUITE")
    print("🚀"*35)
    print(f"\n⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📍 Server: http://localhost:8004")
    
    # Run basic tests
    results = []
    pdf_id = None
    
    # Test 1: Health
    results.append(("Server Health", test_server_health()))
    
    if not results[0][1]:
        print("\n⚠️  Server is not running. Please start the server first!")
        print("   Command: uvicorn server:app --reload --port 8004")
        return
    
    # Test 2: Root
    results.append(("Root Endpoint", test_root_endpoint()))
    
    # Test 3: Stats
    results.append(("Statistics", test_stats_endpoint()))
    
    # Test 4: List PDFs
    results.append(("List PDFs", test_list_pdfs()))
    
    # Ask if user wants to test PDF operations
    print("\n" + "="*70)
    print("PDF OPERATIONS TESTS")
    print("="*70)
    print("\nThe following tests require PDF upload and processing:")
    print("• Upload PDF")
    print("• Search PDF content")
    print("• RAG question answering")
    print("• PDF summarization")
    
    user_input = input("\nDo you want to run PDF operation tests? (y/n): ").lower()
    
    if user_input == 'y':
        # Test 5: Upload
        pdf_id = test_upload_pdf()
        results.append(("Upload PDF", pdf_id is not None))
        
        if pdf_id:
            # Test 6: Search
            results.append(("Search PDFs", test_search_pdf(pdf_id)))
            
            # Test 7: RAG
            results.append(("RAG Query", test_rag_query(pdf_id)))
            
            # Test 8: Summarize
            results.append(("Summarize PDF", test_summarize_pdf(pdf_id)))
    
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
        print("   Your RAG PDF MCP Server is working perfectly!")
        print("\n💡 Next steps:")
        print("   • Try the API docs: http://localhost:8004/docs")
        print("   • Upload your own PDFs")
        print("   • Test RAG question answering")
        print("   • Integrate with other MCP servers")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        print("   Common issues:")
        print("   • MySQL not running or not configured")
        print("   • ChromaDB initialization failed")
        print("   • PDF processing dependencies missing")
    
    print(f"\n⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "🚀"*35 + "\n")


if __name__ == "__main__":
    main()