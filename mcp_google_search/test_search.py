"""
Test script for Search MCP Server
Run this to test if everything works!
"""
import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Server URL
BASE_URL = "http://localhost:8001"


def print_section(title):
    """Pretty print section headers"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_server_running():
    """Test 1: Check if server is running"""
    print_section("TEST 1: Server Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Server is running!")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server!")
        print("   Make sure the server is running:")
        print("   uvicorn server:app --reload --port 8001")
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


def test_search():
    """Test 3: Perform actual search"""
    print_section("TEST 3: Search Functionality")
    
    # Check if API credentials are set
    api_key = os.getenv('GOOGLE_API_KEY')
    cse_id = os.getenv('GOOGLE_CSE_ID')
    
    if not api_key or not cse_id:
        print("⚠️  Warning: Google API credentials not set in .env file")
        print("   This test will likely fail")
    
    try:
        # Prepare search request
        search_data = {
            "query": "Python programming",
            "num_results": 3
        }
        
        print(f"🔍 Searching for: '{search_data['query']}'")
        print(f"   Requesting {search_data['num_results']} results...")
        
        # Make the request
        response = requests.post(
            f"{BASE_URL}/search",
            json=search_data,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Search successful!")
            print(f"   Query: {data['query']}")
            print(f"   Total results: {data['total_results']}")
            print(f"   Search engine: {data['search_engine']}")
            
            if data['results']:
                print("\n📋 Results:")
                for result in data['results']:
                    print(f"\n   {result['rank']}. {result['title']}")
                    print(f"      URL: {result['url']}")
                    print(f"      Snippet: {result['snippet'][:100]}...")
            else:
                print("   No results returned")
            
            return True
        else:
            print(f"❌ Search failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        print("   The search took too long to complete")
        return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quick_test_endpoint():
    """Test 4: Try the built-in test endpoint"""
    print_section("TEST 4: Quick Test Endpoint")
    
    try:
        print("🧪 Running built-in test...")
        response = requests.get(f"{BASE_URL}/test", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Test endpoint working!")
            
            if data.get('test') == 'success':
                results = data.get('results', {})
                total = results.get('total_results', 0)
                print(f"   Found {total} results")
                return True
            else:
                print("⚠️  Test completed but with unexpected results")
                return False
        else:
            print(f"❌ Failed with status: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 SEARCH MCP SERVER - TEST SUITE")
    print("="*60)
    
    # Run all tests
    tests = [
        ("Server Health", test_server_running),
        ("Root Endpoint", test_root_endpoint),
        ("Search Functionality", test_search),
        ("Quick Test Endpoint", test_quick_test_endpoint)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status}: {name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()