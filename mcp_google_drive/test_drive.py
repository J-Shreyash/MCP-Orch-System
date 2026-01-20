"""
Test script for Google Drive MCP Server
Run this to test if everything works!
"""
import requests
import os
from datetime import datetime


BASE_URL = "http://localhost:8002"


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
            print(f"   Service: {data.get('service')}")
            print(f"   Google Drive Connected: {data.get('google_drive_connected')}")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server!")
        print("   Make sure the server is running:")
        print("   uvicorn server:app --reload --port 8002")
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


def test_list_files():
    """Test 3: List files in Google Drive"""
    print_section("TEST 3: List Files")
    
    try:
        response = requests.get(f"{BASE_URL}/files?max_results=5", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ List successful!")
            print(f"   Total files: {data.get('total_files')}")
            print(f"   Message: {data.get('message')}")
            
            if data.get('files'):
                print("\n📋 Files:")
                for file in data['files'][:3]:  # Show first 3
                    print(f"\n   📄 {file['name']}")
                    print(f"      ID: {file['file_id']}")
                    print(f"      Size: {file['size']} bytes")
                    print(f"      Type: {file['mime_type']}")
            else:
                print("   No files in Google Drive yet")
            
            return True
        else:
            print(f"❌ List failed: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_upload_file():
    """Test 4: Upload a test file"""
    print_section("TEST 4: Upload File")
    
    try:
        # Create a test file
        test_filename = "mcp_test_file.txt"
        test_content = f"Test file created by MCP Google Drive Server\nTimestamp: {datetime.now()}"
        
        with open(test_filename, 'w') as f:
            f.write(test_content)
        
        print(f"📝 Created test file: {test_filename}")
        
        # Upload it
        print(f"📤 Uploading to Google Drive...")
        
        with open(test_filename, 'rb') as f:
            files = {'file': (test_filename, f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=30)
        
        # Clean up local file
        os.remove(test_filename)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload successful!")
            print(f"   File ID: {data.get('file_id')}")
            print(f"   File Name: {data.get('file_name')}")
            print(f"   Size: {data.get('size')} bytes")
            print(f"   View Link: {data.get('web_view_link')}")
            
            # Save file ID for other tests
            return data.get('file_id')
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests"""
    print("\n" + "🚀"*35)
    print("   GOOGLE DRIVE MCP SERVER - TEST SUITE")
    print("🚀"*35)
    print(f"\n⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📍 Server: http://localhost:8002")
    
    # Run tests
    results = []
    
    # Test 1: Health
    results.append(("Server Health", test_server_health()))
    
    # Test 2: Root
    if results[0][1]:
        results.append(("Root Endpoint", test_root_endpoint()))
    
    # Test 3: List Files
    if results[0][1]:
        results.append(("List Files", test_list_files()))
    
    # Test 4: Upload (optional - requires authentication)
    if results[0][1]:
        print("\n⚠️  Upload test requires Google Drive authentication")
        print("   This test will create a test file in your Google Drive")
        user_input = input("   Do you want to run the upload test? (y/n): ").lower()
        
        if user_input == 'y':
            file_id = test_upload_file()
            results.append(("Upload File", file_id is not None))
            
            if file_id:
                print(f"\n💡 File uploaded with ID: {file_id}")
                print("   You can delete it later from Google Drive or use the /delete endpoint")
    
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
        print("   Your Google Drive MCP Server is working perfectly!")
        print("\n💡 Next steps:")
        print("   • Try the API docs: http://localhost:8002/docs")
        print("   • Upload your own files")
        print("   • Integrate with other MCP servers")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
    
    print(f"\n⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "🚀"*35 + "\n")


if __name__ == "__main__":
    main()