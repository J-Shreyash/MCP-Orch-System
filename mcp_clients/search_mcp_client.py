"""
Search MCP Client - Production Ready
Connects to Google Search MCP Server (Port 8001)
Provides web search capabilities for the AI Agent System
"""
import requests
from typing import List, Dict, Optional
import json


class SearchMCPClient:
    """Client for Google Search MCP Server"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8001"):
        """
        Initialize Search MCP Client
        
        Args:
            base_url: Base URL of Search MCP Server (default: http://127.0.0.1:8001)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = 30
        print(f"🔍 Search MCP Client initialized")
        print(f"   Server: {self.base_url}")
    
    def health_check(self) -> Dict:
        """
        Check if Search MCP server is running
        
        Returns:
            Health status dictionary
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "server": "Search MCP",
                    "available": True,
                    "data": response.json()
                }
            else:
                return {
                    "status": "unhealthy",
                    "server": "Search MCP",
                    "available": False,
                    "error": f"Status code: {response.status_code}"
                }
        
        except requests.exceptions.ConnectionError:
            return {
                "status": "unavailable",
                "server": "Search MCP",
                "available": False,
                "error": "Cannot connect to server. Is it running on port 8001?"
            }
        
        except Exception as e:
            return {
                "status": "error",
                "server": "Search MCP",
                "available": False,
                "error": str(e)
            }
    
    def search(self, query: str, num_results: int = 5) -> Dict:
        """
        Perform Google search
        
        Args:
            query: Search query string
            num_results: Number of results to return (default: 5, max: 10)
            
        Returns:
            Dictionary with search results
        """
        try:
            print(f"\n🔍 Searching: '{query}'")
            print(f"   Requesting {num_results} results...")
            
            payload = {
                "query": query,
                "num_results": min(num_results, 10)
            }
            
            response = requests.post(
                f"{self.base_url}/search",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data.get('total_results', 0)} results")
                
                return {
                    "success": True,
                    "query": data.get('query'),
                    "results": data.get('results', []),
                    "total_results": data.get('total_results', 0),
                    "search_engine": data.get('search_engine', 'google')
                }
            
            else:
                print(f"❌ Search failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Search failed with status {response.status_code}",
                    "details": response.text
                }
        
        except requests.exceptions.Timeout:
            print("❌ Search timeout")
            return {
                "success": False,
                "error": "Search request timed out"
            }
        
        except requests.exceptions.ConnectionError:
            print("❌ Connection error")
            return {
                "success": False,
                "error": "Cannot connect to Search MCP server. Is it running?"
            }
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def format_results(self, search_results: Dict, max_results: int = 5) -> str:
        """Format search results into readable text"""
        if not search_results.get('success'):
            return f"❌ Search failed: {search_results.get('error', 'Unknown error')}"
        
        results = search_results.get('results', [])
        
        if not results:
            return "ℹ️ No search results found"
        
        formatted = [f"🔍 Search Results for: '{search_results.get('query')}'"]
        formatted.append(f"Found {len(results)} results\n")
        
        for i, result in enumerate(results[:max_results], 1):
            formatted.append(f"{i}. **{result.get('title', 'No title')}**")
            formatted.append(f"   {result.get('snippet', 'No description')}")
            formatted.append(f"   🔗 {result.get('url', '')}\n")
        
        return "\n".join(formatted)
    
    def get_top_result(self, query: str) -> Optional[Dict]:
        """Get only the top search result"""
        results = self.search(query, num_results=1)
        
        if results.get('success') and results.get('results'):
            return results['results'][0]
        
        return None
    
    def batch_search(self, queries: List[str], results_per_query: int = 3) -> Dict:
        """Perform multiple searches"""
        print(f"\n📚 Batch searching {len(queries)} queries...")
        
        all_results = {}
        
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Searching: {query}")
            results = self.search(query, num_results=results_per_query)
            all_results[query] = results
        
        print(f"\n✅ Batch search complete!")
        return all_results
    
    def is_available(self) -> bool:
        """Quick check if server is available"""
        health = self.health_check()
        return health.get('available', False)


def quick_search(query: str, num_results: int = 5) -> Dict:
    """Convenience function for quick searches"""
    client = SearchMCPClient()
    return client.search(query, num_results)


def test_search_client():
    """Test Search MCP Client"""
    print("\n" + "="*60)
    print("🧪 Testing Search MCP Client")
    print("="*60)
    
    client = SearchMCPClient()
    
    print("\n1️⃣ Health Check")
    health = client.health_check()
    print(f"   Status: {health.get('status')}")
    print(f"   Available: {health.get('available')}")
    
    if not health.get('available'):
        print("\n❌ Search MCP server is not available!")
        print("   Make sure it's running on port 8001")
        return
    
    print("\n2️⃣ Simple Search Test")
    results = client.search("Python programming tutorials", num_results=3)
    
    if results.get('success'):
        print(f"✅ Search successful!")
        print(f"   Query: {results.get('query')}")
        print(f"   Results: {results.get('total_results')}")
        
        if results.get('results'):
            first = results['results'][0]
            print(f"\n   Top result:")
            print(f"   Title: {first.get('title')}")
            print(f"   URL: {first.get('url')}")
    else:
        print(f"❌ Search failed: {results.get('error')}")
    
    print("\n3️⃣ Formatted Output Test")
    formatted = client.format_results(results, max_results=3)
    print(formatted)
    
    print("\n" + "="*60)
    print("✅ Search MCP Client Test Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_search_client()