# Search MCP Server

A Model Context Protocol (MCP) server that provides web search capabilities using Google Custom Search API.

## 🎯 Features

- ✅ Google Custom Search integration
- ✅ RESTful API with FastAPI
- ✅ Interactive API documentation (Swagger UI)
- ✅ Clean error handling and logging
- ✅ Easy to integrate with other systems

## 📋 Prerequisites

- Python 3.10 or higher
- Google Cloud account (free tier)
- Google Custom Search API key
- Custom Search Engine ID

## 🚀 Quick Start

### 1. Clone/Download the Project
```bash
cd mcp-search-server
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file:
```properties
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CSE_ID=your_cse_id_here
```

### 5. Run the Server
```bash
python -m uvicorn mcp_google_search.server:app --reload --port 8001
```

### 6. Access API Documentation

Open your browser: http://localhost:8001/docs

### How to Check if its running correctly.

✅ METHOD : Open Browser (Easiest - 30 seconds)
Just click these links:

1. Quick Test (Shows instant results!)
👉 http://localhost:8001/test
2. API Documentation (Interactive testing!)
👉 http://localhost:8001/docs

Click "POST /search"
Click "Try it out"
______________________________________________________________________________
You'll see a JSON request body:

json   {
     "query": "string",
     "num_results": 5
   }
------------------------------------------------------------------------------
Change it to something like:

json   {
     "query": "Python programming tutorials",
     "num_results": 3
   }
_____________________________________________________________________________   
Click "Execute"
See live results!

3. Health Check
👉 http://localhost:8001/health


## 🔑 Getting API Credentials

### Google API Key:
1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable "Custom Search API"
4. Create credentials → API key

### Custom Search Engine ID:
1. Go to https://programmablesearchengine.google.com/
2. Create a new search engine
3. Select "Search the entire web"
4. Copy your Search Engine ID

## 📡 API Endpoints

### Search
```
POST /search
```

**Request:**
```json
{
  "query": "Python programming",
  "num_results": 5
}
```

**Response:**
```json
{
  "query": "Python programming",
  "results": [
    {
      "title": "Welcome to Python.org",
      "url": "https://www.python.org/",
      "snippet": "The official home...",
      "rank": 1
    }
  ],
  "total_results": 5,
  "search_engine": "google"
}
```

### Health Check
```
GET /health
```

Returns server status.

## 🧪 Testing

Run the test file:
```bash
python test_search.py
```

## 📊 Usage Limits

- **Free Tier:** 100 searches per day
- **Upgrade:** Available if needed for production

## 🏗️ Project Structure
```
mcp-search-server/
├── mcp_google_search/
│   ├── __init__.py
│   ├── models.py          # Data models
│   ├── search_handler.py  # Search logic
│   └── server.py          # FastAPI server
├── .env                   # Configuration
├── requirements.txt       # Dependencies
├── test_search.py        # Test script
└── README.md             # This file
```

## 🔧 Troubleshooting

**API Key Invalid:**
- Verify your API key is correct
- Check it's enabled for Custom Search API

**No Results:**
- Ensure CSE ID is correct
- Verify "Search the entire web" is enabled

**Rate Limit:**
- Free tier: 100 searches/day
- Wait 24 hours or upgrade plan

## 📝 License

MIT License - Free to use and modify

## 👥 Author

By Shreyash Shankarrao Jadhav