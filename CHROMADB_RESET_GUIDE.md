# ChromaDB Reset Guide

## Issue: `no such column: collections.topic`

This error occurs when ChromaDB database schema is outdated (created with older ChromaDB version).

## Automatic Fix

The servers will **automatically detect and reset** the database when this error occurs. However, if the database file is locked, you may need to manually reset it.

## Manual Reset (If Automatic Fails)

### Option 1: Use Reset Scripts

**For Database MCP:**
```bash
cd mcp_database
python reset_chromadb.py
```

**For RAG PDF MCP:**
```bash
cd mcp_rag_pdf
python reset_chromadb.py
```

### Option 2: Manual Deletion

1. **Stop ALL running servers** (Database MCP, RAG PDF MCP, AI Agent System)
2. **Close any Python processes** that might be using ChromaDB
3. **Delete the ChromaDB directory:**
   - Database MCP: `mcp_database\chroma_db`
   - RAG PDF MCP: `mcp_rag_pdf\chroma_db`
4. **Restart the servers**

### Option 3: Use Different Directories

You can configure different ChromaDB directories in `.env`:

```env
# For Database MCP
CHROMA_DIR=./chroma_db

# For RAG PDF MCP (if needed)
CHROMA_DIR=./chroma_db_pdf
```

## Prevention

After resetting, the database will be recreated with the correct schema. This is a one-time operation.

## Note

⚠️ **Resetting ChromaDB will DELETE all stored embeddings and documents!**
- Database MCP: All document embeddings will be lost
- RAG PDF MCP: All PDF chunk embeddings will be lost

You'll need to re-upload/re-index your documents after reset.
