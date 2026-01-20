"""
Google Search Handler - ONLY Google Custom Search
"""
import requests
from typing import List, Dict
import os


class SearchHandler:
    """Handles Google Custom Search ONLY"""
    
    def __init__(self, google_api_key=None, google_cse_id=None):
        """
        Initialize Google Search Handler
        
        Args:
            google_api_key: Your Google API key
            google_cse_id: Your Custom Search Engine ID
        """
        # Get credentials from parameters or environment
        self.google_api_key = google_api_key or os.getenv('GOOGLE_API_KEY')
        self.google_cse_id = google_cse_id or os.getenv('GOOGLE_CSE_ID')
        
        print("🔍 Search Handler initialized")
        
        # Check if credentials are set
        if self.google_api_key and self.google_cse_id:
            print("✅ Google Custom Search configured")
            print(f"   API Key: {self.google_api_key[:20]}...")
            print(f"   CSE ID: {self.google_cse_id}")
        else:
            print("❌ Google API credentials missing!")
            if not self.google_api_key:
                print("   Missing: GOOGLE_API_KEY")
            if not self.google_cse_id:
                print("   Missing: GOOGLE_CSE_ID")
    
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Search using Google Custom Search API
        
        FREE TIER: 100 searches per day!
        
        Args:
            query: What to search for
            num_results: Number of results (max 10 per request)
            
        Returns:
            List of search results
        """
        print(f"\n{'='*60}")
        print(f"🔍 Starting Google Search")
        print(f"   Query: '{query}'")
        print(f"   Requested results: {num_results}")
        print(f"{'='*60}\n")
        
        # Check credentials
        if not self.google_api_key or not self.google_cse_id:
            print("❌ Cannot search - Google API credentials not set!")
            return []
        
        try:
            # Google Custom Search API endpoint
            url = "https://www.googleapis.com/customsearch/v1"
            
            # Parameters
            params = {
                'key': self.google_api_key,
                'cx': self.google_cse_id,
                'q': query,
                'num': min(num_results, 10)  # Max 10 per request
            }
            
            print(f"📡 Calling Google Custom Search API...")
            print(f"   URL: {url}")
            
            # Make the request
            response = requests.get(url, params=params, timeout=10)
            
            # Check for errors
            if response.status_code != 200:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return []
            
            data = response.json()
            
            # Check if we have results
            if 'items' not in data:
                print("⚠️  No results found")
                if 'error' in data:
                    print(f"   Error: {data['error'].get('message', 'Unknown error')}")
                return []
            
            # Process results
            results = []
            for idx, item in enumerate(data['items']):
                result = {
                    "title": item.get('title', 'No title'),
                    "url": item.get('link', ''),
                    "snippet": item.get('snippet', 'No description available'),
                    "rank": idx + 1
                }
                results.append(result)
                print(f"  ✓ {idx + 1}. {result['title'][:60]}...")
            
            print(f"\n✅ Successfully found {len(results)} results!\n")
            return results
        
        except requests.exceptions.Timeout:
            print("❌ Request timed out")
            return []
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("❌ Rate limit exceeded! (100 searches per day)")
            else:
                print(f"❌ HTTP Error: {e}")
            return []
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return []
        
        except Exception as e:
            print(f"❌ Search failed: {e}")
            import traceback
            traceback.print_exc()
            return []