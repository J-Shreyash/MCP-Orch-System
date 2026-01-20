# Google Drive MCP Server

A standalone Model Context Protocol (MCP) server that provides complete Google Drive file management through a REST API.

## 🎯 Features

- ✅ Upload files to Google Drive
- ✅ List files with metadata
- ✅ Download files
- ✅ Delete files
- ✅ Get file information
- ✅ RESTful API with FastAPI
- ✅ Interactive API documentation (Swagger UI)
- ✅ OAuth 2.0 authentication
- ✅ Comprehensive testing suite

## 📋 Prerequisites

- Python 3.10 or higher
- Google Cloud account (free)
- Google Drive API enabled
- OAuth 2.0 credentials

## 🚀 Quick Start

### Step 1: Get Google Drive API Credentials

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable "Google Drive API"
4. Create OAuth 2.0 credentials:
   - Application type: Desktop app
   - Download credentials as `credentials.json`
5. Place `credentials.json` in the `mcp_google_drive` folder

### Step 2: Setup Project

```bash
# Navigate to project folder
cd mcp_google_drive

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Run the Server

```bash
uvicorn server:app --reload --port 8002
```

### Step 4: Authenticate

On first run, your browser will open for Google authentication:
1. Select your Google account
2. Click "Allow" to grant Drive access
3. Browser will show "Authentication successful"
4. Return to terminal - server is ready!

### Step 5: Access API Documentation

Open your browser: http://localhost:8002/docs

## 📡 API Endpoints

### 1. Upload File
```
POST /upload
```
Upload a file to Google Drive.

**Request:** multipart/form-data with file

**Response:**
```json
{
  "file_id": "1abc...",
  "file_name": "example.pdf",
  "size": 12345,
  "mime_type": "application/pdf",
  "web_view_link": "https://drive.google.com/...",
  "message": "File uploaded successfully"
}
```

### 2. List Files
```
GET /files?max_results=10
```
List files in Google Drive.

**Response:**
```json
{
  "files": [
    {
      "file_id": "1abc...",
      "name": "example.pdf",
      "mime_type": "application/pdf",
      "size": 12345,
      "created_time": "2024-01-01T00:00:00Z",
      "modified_time": "2024-01-01T00:00:00Z",
      "web_view_link": "https://drive.google.com/..."
    }
  ],
  "total_files": 1,
  "message": "Found 1 files"
}
```

### 3. Get File Info
```
GET /files/{file_id}
```
Get detailed information about a specific file.

### 4. Download File
```
GET /download/{file_id}
```
Download a file from Google Drive.

### 5. Delete File
```
DELETE /files/{file_id}
```
Delete a file from Google Drive.

**Response:**
```json
{
  "file_id": "1abc...",
  "file_name": "example.pdf",
  "message": "File deleted successfully",
  "success": true
}
```

### 6. Health Check
```
GET /health
```
Check server status and Google Drive connection.

## 🧪 Testing

### Run Test Suite
```bash
python test_drive.py
```

This will test:
- ✅ Server health
- ✅ API endpoints
- ✅ Google Drive connection
- ✅ File operations (optional)

### Manual Testing via Browser

1. **Interactive API Docs**: http://localhost:8002/docs
2. **Health Check**: http://localhost:8002/health

## 🏗️ Project Structure

```
mcp_google_drive/
├── .venv/                    # Virtual environment
├── credentials.json          # OAuth credentials (you create this)
├── token.pickle             # Saved auth token (auto-generated)
├── __init__.py              # Package marker
├── models.py                # Data models
├── drive_handler.py         # Google Drive operations
├── server.py                # FastAPI server
├── test_drive.py            # Test script
├── requirements.txt         # Dependencies
└── README.md                # This file
```

## 🔐 Authentication

This server uses OAuth 2.0 for secure authentication:

1. **First run**: Browser opens for authentication
2. **Subsequent runs**: Uses saved token (`token.pickle`)
3. **Token expiry**: Automatically refreshes when needed

**Security Notes:**
- `credentials.json` - Keep secure, don't commit to git
- `token.pickle` - Auto-generated, safe to delete if issues occur
- Both files are in `.gitignore`

## 🔧 Troubleshooting

### "credentials.json not found"
**Solution:** Download OAuth credentials from Google Cloud Console and place in project folder.

### "Authentication failed"
**Solution:** 
1. Delete `token.pickle`
2. Restart server
3. Re-authenticate

### "Permission denied"
**Solution:** Make sure you granted Drive access during authentication.

### "Cannot connect to server"
**Solution:** Make sure server is running on port 8002.

## 📊 Usage Examples

### Using curl

**Upload a file:**
```bash
curl -X POST "http://localhost:8002/upload" \
  -F "file=@/path/to/file.pdf"
```

**List files:**
```bash
curl "http://localhost:8002/files?max_results=5"
```

**Delete a file:**
```bash
curl -X DELETE "http://localhost:8002/files/FILE_ID_HERE"
```

### Using Python

```python
import requests

# List files
response = requests.get("http://localhost:8002/files?max_results=10")
files = response.json()

# Upload file
with open('document.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post("http://localhost:8002/upload", files=files)
    print(response.json())

# Download file
file_id = "1abc..."
response = requests.get(f"http://localhost:8002/download/{file_id}")
with open('downloaded.pdf', 'wb') as f:
    f.write(response.content)

# Delete file
response = requests.delete(f"http://localhost:8002/files/{file_id}")
print(response.json())
```

## 🌐 Integration with Other MCP Servers

This server runs on port 8002 to avoid conflicts:
- Google Search MCP: Port 8001
- **Google Drive MCP: Port 8002** (this server)
- Database MCP: Port 8003 (upcoming)
- RAG PDF MCP: Port 8004 (upcoming)

All servers can run simultaneously for complete MCP orchestration.

## 🔒 Security Best Practices

1. **Keep credentials secure**: Never commit `credentials.json` to version control
2. **Use environment variables**: For additional configuration
3. **HTTPS in production**: Use reverse proxy (nginx/Apache) with SSL
4. **Rate limiting**: Implement rate limiting for production use
5. **API keys**: Add API key authentication for production

## 📝 Environment Variables (Optional)

Create `.env` file for additional configuration:

```env
# Port configuration
PORT=8002

# Google Drive folder ID (optional)
DRIVE_FOLDER_ID=your_folder_id_here
```

## 🚀 Next Steps

After getting this working:
1. Test all endpoints through API docs
2. Upload and manage your files
3. Integrate with Google Search MCP
4. Build Database MCP next
5. Create orchestration layer

## 📜 License

MIT License - Free to use and modify

## 👤 Author

By Shreyash Shankarrao Jadhav

## 🆘 Need Help?

1. Check the troubleshooting section
2. Review API docs at http://localhost:8002/docs
3. Run test script: `python test_drive.py`
4. Check server logs in terminal

---

**Your Google Drive MCP Server is ready! Happy coding! 🎉**