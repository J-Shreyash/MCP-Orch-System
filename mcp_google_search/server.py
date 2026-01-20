"""
This is your MCP SERVER!
It creates a web API that other programs can talk to
"""
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import os

# Import from current directory (no parent folder needed!)
from models import SearchRequest, SearchResponse, SearchResult
from search_handler import SearchHandler

# Load environment variables from .env file
load_dotenv()

# Create the FastAPI app
app = FastAPI(
    title="Search MCP Server",
    description="Your first MCP server - provides web search!",
    version="1.0.0"
)

# Create search handler WITH credentials (ONLY ONCE!)
search_handler = SearchHandler(
    google_api_key=os.getenv('GOOGLE_API_KEY'),
    google_cse_id=os.getenv('GOOGLE_CSE_ID')
)

print("🚀 Search MCP Server initializing...")
print("📡 Search handler ready!")


@app.get("/")
async def root():
    """
    This runs when someone visits http://localhost:8001/
    It's like the homepage of your API
    """
    return {
        "message": "🎉 Search MCP Server is running!",
        "service": "Search MCP",
        "version": "1.0.0",
        "endpoints": {
            "search": "POST /search - Perform a web search",
            "health": "GET /health - Check server health",
            "docs": "GET /docs - Interactive API documentation"
        },
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    Other services can ping this to see if we're alive
    """
    return {
        "status": "healthy",
        "service": "Search MCP",
        "timestamp": "operational"
    }


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    This is the MAIN endpoint - it performs web searches!
    
    When someone sends a POST request to /search with a query,
    this function runs and returns search results
    """
    print(f"\n{'='*60}")
    print(f"📨 Received search request")
    print(f"   Query: {request.query}")
    print(f"   Num results: {request.num_results}")
    print(f"{'='*60}")
    
    try:
        # Use our search handler to perform the search
        raw_results = search_handler.search(
            query=request.query,
            num_results=request.num_results
        )
        
        # Check if we got results
        if not raw_results:
            print("⚠️  No results found")
            return SearchResponse(
                query=request.query,
                results=[],
                total_results=0,
                search_engine="google"
            )
        
        # Convert raw results to SearchResult objects
        search_results = [
            SearchResult(**result) for result in raw_results
        ]
        
        # Create response
        response = SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            search_engine="google"
        )
        
        print(f"✅ Returning {len(search_results)} results\n")
        return response
    
    except Exception as e:
        print(f"❌ Error during search: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/test")
async def test_search():
    """
    Quick test endpoint - searches for "Python programming"
    Visit http://localhost:8001/test in your browser to try it!
    """
    print("\n🧪 Running test search...")
    
    # Create a test request
    test_request = SearchRequest(
        query="Python programming",
        num_results=3
    )
    
    # Use the search endpoint
    result = await search(test_request)
    
    return {
        "test": "success",
        "message": "Test search completed!",
        "results": result
    }


# This runs when you start the server
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Starting Search MCP Server...")
    print("📍 Server will run on: http://localhost:8001")
    print("📚 API Docs available at: http://localhost:8001/docs")
    print("🧪 Quick test at: http://localhost:8001/test")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)