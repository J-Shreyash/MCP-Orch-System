"""
RAG PDF MCP Server 
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
from pathlib import Path
import uuid
from datetime import datetime
from dotenv import load_dotenv
import time

# Import handlers
from mysql_handler import MySQLHandler
from vector_store import VectorStore
from pdf_handler import PDFHandler
from chunk_engine import ChunkEngine
from rag_pipeline import RAGPipeline
from summarizer import Summarizer
from bm25_handler import BM25Handler
from graph_handler import GraphHandler
from entity_extractor import EntityExtractor

load_dotenv()

# Initialize FastAPI
app = FastAPI(title="RAG PDF MCP Server", version="2.2.0")

# Configuration
UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', './uploads'))
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize handlers (will be done on startup)
mysql_handler = None
vector_store = None
pdf_handler = None
chunk_engine = None
rag_pipeline = None
summarizer = None
bm25_handler = None
graph_handler = None
entity_extractor = None


@app.on_event("startup")
async def startup_event():
    """Initialize all handlers on startup"""
    global mysql_handler, vector_store, pdf_handler, chunk_engine, rag_pipeline, summarizer
    global bm25_handler, graph_handler, entity_extractor
    
    print("\n🚀 RAG PDF MCP Server initializing...")
    
    # MySQL
    print("🔌 Connecting to MySQL...")
    mysql_handler = MySQLHandler()
    
    # ChromaDB
    print("🔌 Connecting to ChromaDB...")
    chroma_dir = os.getenv('CHROMA_DIR', './chroma_db_pdf')  # Different default to avoid conflicts
    vector_store = VectorStore(persist_directory=chroma_dir)
    
    # PDF Handler
    print("📁 PDF upload directory:", UPLOAD_DIR)
    pdf_handler = PDFHandler(upload_directory=str(UPLOAD_DIR))
    
    # Chunk Engine
    chunk_size = int(os.getenv('CHUNK_SIZE', '600'))
    chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '100'))
    print(f"🔧 Chunk Engine initialized (size: {chunk_size}, overlap: {chunk_overlap})")
    chunk_engine = ChunkEngine(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    # RAG Pipeline
    rag_pipeline = RAGPipeline(vector_store, mysql_handler)
    
    # Summarizer
    summarizer = Summarizer(vector_store, mysql_handler)
    
    # BM25 Handler
    print("🔧 Initializing BM25 Handler...")
    bm25_handler = BM25Handler()
    
    # Neo4j Graph Handler (optional)
    graph_handler = None
    try:
        graph_handler = GraphHandler()
        if not graph_handler.is_connected():
            print("⚠️  Neo4j not connected, graph features disabled")
            graph_handler = None
    except Exception as e:
        print(f"⚠️  Neo4j initialization failed: {e}")
        print("   Graph features will be disabled")
    
    # Entity Extractor (optional, requires OpenAI API key)
    entity_extractor = None
    try:
        if os.getenv('OPENAI_API_KEY'):
            entity_extractor = EntityExtractor()
        else:
            print("⚠️  OPENAI_API_KEY not found, entity extraction disabled")
    except Exception as e:
        print(f"⚠️  Entity extractor initialization failed: {e}")
        print("   Entity extraction will be disabled")
    
    print("📡 All handlers ready!")


# Pydantic models
class QuestionRequest(BaseModel):
    question: str
    pdf_id: Optional[str] = None
    max_context_chunks: int = 5


class SummarizeRequest(BaseModel):
    max_length: int = 500


class SearchQuery(BaseModel):
    query: str
    limit: int = 5
    pdf_id: Optional[str] = None
    include_context: bool = False
    search_type: str = "hybrid"  # semantic, keyword, or hybrid


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RAG PDF MCP",
        "version": "2.2.0",
        "mysql_connected": mysql_handler is not None,
        "chroma_connected": vector_store is not None
    }


# Upload PDF
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process PDF"""
    print(f"\n{'='*60}")
    print(f"📨 Received PDF upload request")
    print(f"   Filename: {file.filename}")
    print(f"   Content-Type: {file.content_type}")
    print(f"{'='*60}")
    
    try:
        # Read file
        file_bytes = await file.read()
        file_size = len(file_bytes)
        print(f"   Size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
        
        # Generate unique ID
        pdf_id = str(uuid.uuid4())
        
        # Save file
        safe_filename = f"{pdf_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        
        print("🚀 Processing PDF...")
        
        # Process PDF
        start_time = time.time()
        
        print(f"\n{'='*60}")
        print(f"📚 Processing PDF: {file.filename}")
        print(f"{'='*60}\n")
        
        # Extract content
        pdf_data = pdf_handler.extract_pdf_content(str(file_path))
        page_count = pdf_data['page_count']
        full_text = pdf_data['full_text']
        
        print(f"\n✅ PDF Processing Complete!")
        print(f"   Pages: {page_count}")
        print(f"   Characters: {len(full_text):,}")
        print(f"   Size: {file_size:,} bytes\n")
        
        # Create chunks using chunk_engine.create_chunks()
        chunks = chunk_engine.create_chunks(pdf_data, pdf_id)
        chunks_count = len(chunks)
        
        # Store in vector database
        vector_store.add_chunks(chunks)
        
        # Index chunks in BM25
        if bm25_handler:
            try:
                print("📚 Indexing chunks in BM25...")
                bm25_chunks = []
                for chunk in chunks:
                    bm25_chunks.append({
                        'chunk_id': chunk['chunk_id'],
                        'pdf_id': pdf_id,
                        'content': chunk['content'],
                        'page_number': chunk.get('page_number', 0),
                        'metadata': chunk.get('metadata', {})
                    })
                bm25_handler.add_chunks(bm25_chunks)
                print("   ✅ BM25 indexing complete")
            except Exception as e:
                print(f"   ⚠️  BM25 indexing failed: {e}")
        
        # Create PDF node in Neo4j and extract entities
        if graph_handler:
            try:
                print("🔗 Creating graph nodes and extracting entities...")
                graph_handler.create_pdf_node(
                    pdf_id,
                    file.filename,
                    {'page_count': page_count, 'file_size': file_size}
                )
                
                # Extract entities from chunks (if entity extractor available)
                if entity_extractor:
                    for chunk in chunks[:50]:  # Limit to first 50 chunks to manage cost
                        try:
                            extraction_result = entity_extractor.extract_all(
                                chunk['content'],
                                chunk['chunk_id']
                            )
                            graph_handler.index_entities_and_relationships(
                                extraction_result,
                                pdf_id
                            )
                        except Exception as e:
                            print(f"   ⚠️  Entity extraction failed for chunk {chunk['chunk_id']}: {e}")
                
                print("   ✅ Graph indexing complete")
            except Exception as e:
                print(f"   ⚠️  Graph indexing failed: {e}")
        
        # Save metadata to MySQL
        mysql_handler.insert_pdf(
            pdf_id=pdf_id,
            filename=file.filename,
            file_size=file_size,
            page_count=page_count,
            chunks_count=chunks_count
        )
        
        processing_time = time.time() - start_time
        
        print(f"\n✅ PDF processed in {processing_time:.2f} seconds!")
        print(f"   Pages: {page_count}")
        print(f"   Chunks: {chunks_count}")
        
        return {
            "success": True,
            "pdf_id": pdf_id,
            "filename": file.filename,
            "page_count": page_count,
            "chunks_created": chunks_count,
            "file_size": file_size,
            "processing_time": f"{processing_time:.2f}s",
            "message": "PDF processed successfully"
        }
    
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# List PDFs
@app.get("/pdfs")
async def list_pdfs(limit: int = 100, offset: int = 0):
    """List all uploaded PDFs"""
    print(f"\n{'='*60}")
    print(f"📨 Received list PDFs request")
    print(f"   Limit: {limit}")
    print(f"{'='*60}")
    
    try:
        pdfs = mysql_handler.list_pdfs(limit=limit, offset=offset)
        total = mysql_handler.get_total_pdfs()
        
        print(f"✅ Retrieved {len(pdfs)} PDFs")
        
        return {
            "success": True,
            "pdfs": pdfs,
            "total_pdfs": total,
            "limit": limit,
            "offset": offset
        }
    
    except Exception as e:
        print(f"❌ List failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get specific PDF
@app.get("/pdfs/{pdf_id}")
async def get_pdf(pdf_id: str):
    """Get specific PDF details"""
    try:
        pdf_info = mysql_handler.get_pdf(pdf_id)
        
        if not pdf_info:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        return {
            "success": True,
            "pdf": pdf_info
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# DELETE PDF
@app.delete("/pdfs/{pdf_id}")
async def delete_pdf(pdf_id: str):
    """Delete PDF and all associated chunks"""
    print(f"\n{'='*60}")
    print(f"🗑️ Received delete request for PDF: {pdf_id}")
    print(f"{'='*60}\n")
    
    try:
        # Get PDF info first
        pdf_info = mysql_handler.get_pdf(pdf_id)
        
        if not pdf_info:
            print(f"❌ PDF not found: {pdf_id}")
            raise HTTPException(status_code=404, detail="PDF not found")
        
        pdf_filename = pdf_info.get('filename', 'Unknown')
        print(f"📄 Deleting PDF: {pdf_filename}")
        
        # Delete from vector store
        print("🗑️ Removing chunks from ChromaDB...")
        chunks_deleted = vector_store.delete_pdf_chunks(pdf_id)
        print(f"✅ Removed {chunks_deleted} chunks")
        
        # Delete from BM25
        if bm25_handler:
            try:
                print("🗑️ Removing chunks from BM25...")
                bm25_handler.remove_pdf_chunks(pdf_id)
                print(f"✅ BM25 chunks removed")
            except Exception as e:
                print(f"⚠️  BM25 deletion failed: {e}")
        
        # Delete from Neo4j
        if graph_handler:
            try:
                print("🗑️ Removing PDF from Neo4j...")
                graph_handler.delete_pdf(pdf_id)
                print(f"✅ Graph nodes removed")
            except Exception as e:
                print(f"⚠️  Graph deletion failed: {e}")
        
        # Delete from MySQL
        print("🗑️ Removing PDF record from MySQL...")
        mysql_handler.delete_pdf(pdf_id)
        print(f"✅ PDF record deleted")
        
        # Delete physical file
        try:
            file_path = UPLOAD_DIR / f"{pdf_id}_{pdf_filename}"
            if file_path.exists():
                file_path.unlink()
                print(f"✅ Physical file deleted: {file_path.name}")
        except Exception as e:
            print(f"⚠️ Could not delete physical file: {e}")
        
        # Log activity
        mysql_handler.log_activity(
            "delete_pdf",
            pdf_id,
            f"Deleted PDF: {pdf_filename}"
        )
        
        print(f"\n✅ PDF deleted successfully: {pdf_filename}\n")
        
        return {
            "success": True,
            "message": f"PDF '{pdf_filename}' deleted successfully",
            "pdf_id": pdf_id,
            "chunks_deleted": chunks_deleted
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Delete failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Ask question (RAG)
@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Answer a question using RAG"""
    print(f"\n{'='*60}")
    print(f"📨 Received RAG question")
    print(f"   Question: '{request.question}'")
    print(f"{'='*60}\n")
    
    try:
        result = rag_pipeline.ask_question(
            question=request.question,
            pdf_id=request.pdf_id,
            max_chunks=request.max_context_chunks
        )
        
        print("✅ Answer generated")
        
        return {
            "success": True,
            "answer": result['answer'],
            "sources": result['sources'],
            "confidence": result['confidence']
        }
    
    except Exception as e:
        print(f"❌ Question failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Search PDFs (Hybrid Search)
@app.post("/search")
async def search_pdfs(query: SearchQuery):
    """
    Hybrid search across PDFs (BM25 + Semantic + Graph)
    
    - **query**: Search query text
    - **limit**: Number of results (default: 5)
    - **pdf_id**: Limit search to specific PDF (optional)
    - **include_context**: Include surrounding context (optional)
    - **search_type**: "semantic", "keyword", or "hybrid" (default: hybrid)
    """
    print(f"\n{'='*60}")
    print(f"🔍 Search request")
    print(f"   Query: '{query.query}'")
    print(f"   Type: {query.search_type}")
    print(f"   Limit: {query.limit}")
    if query.pdf_id:
        print(f"   PDF ID: {query.pdf_id}")
    print(f"{'='*60}")
    
    try:
        # Perform search based on type
        if query.search_type == "semantic":
            # Semantic search only
            results = vector_store.search(
                query=query.query,
                limit=query.limit,
                pdf_id=query.pdf_id
            )
        elif query.search_type == "keyword":
            # BM25 keyword search only
            if bm25_handler:
                results = bm25_handler.search(
                    query=query.query,
                    limit=query.limit,
                    pdf_id=query.pdf_id
                )
                # Format to match vector_store format
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        'chunk_id': result['chunk_id'],
                        'content': result['content'],
                        'metadata': {
                            'pdf_id': result['pdf_id'],
                            'page_number': result['page_number']
                        },
                        'similarity_score': result['similarity_score']
                    })
                results = formatted_results
            else:
                results = []
        else:  # hybrid
            # Hybrid search: BM25 + Semantic + Graph
            results = _hybrid_search_pdfs(
                query=query.query,
                limit=query.limit,
                pdf_id=query.pdf_id
            )
        
        # Enrich with PDF metadata
        search_results = []
        for result in results:
            pdf_id = result['metadata'].get('pdf_id') if isinstance(result.get('metadata'), dict) else result.get('pdf_id')
            if not pdf_id:
                continue
                
            pdf = mysql_handler.get_pdf(pdf_id)
            
            if pdf:
                # Context is not available in current implementation
                context = None
                
                search_result = {
                    'chunk_id': result.get('chunk_id', ''),
                    'pdf_id': pdf_id,
                    'pdf_filename': pdf['filename'],
                    'content': result['content'],
                    'page_number': result['metadata'].get('page_number') if isinstance(result.get('metadata'), dict) else result.get('page_number'),
                    'similarity_score': result.get('similarity_score', 0.5),
                    'context': context
                }
                search_results.append(search_result)
        
        print(f"\n✅ Search complete! Found {len(search_results)} results\n")
        
        return {
            "success": True,
            "query": query.query,
            "results": search_results,
            "total_results": len(search_results),
            "search_type": query.search_type
        }
    
    except Exception as e:
        print(f"\n❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def _hybrid_search_pdfs(query: str, limit: int = 5, pdf_id: Optional[str] = None) -> List[Dict]:
    """
    Hybrid search combining BM25, Semantic, and Graph search
    
    Args:
        query: Search query
        limit: Maximum results
        pdf_id: Filter by PDF ID
        
    Returns:
        List of search results with weighted scores
    """
    from collections import defaultdict
    
    # Parallel queries
    bm25_results = []
    semantic_results = []
    graph_results = []
    
    # BM25 keyword search
    if bm25_handler:
        bm25_results = bm25_handler.search(query, limit=limit*2, pdf_id=pdf_id)
    
    # Semantic search
    semantic_results = vector_store.search(query, limit=limit*2, pdf_id=pdf_id)
    
    # Graph search (if available)
    if graph_handler:
        graph_results = graph_handler.query_by_query(query, limit=limit*2)
    
    # Combine and deduplicate with weighted fusion
    chunk_scores = defaultdict(lambda: {
        'bm25_score': 0.0,
        'semantic_score': 0.0,
        'graph_score': 0.0,
        'chunk_data': None
    })
    
    # Process BM25 results
    for result in bm25_results:
        chunk_id = result['chunk_id']
        chunk_scores[chunk_id]['bm25_score'] = result.get('similarity_score', result.get('bm25_score', 0.5))
        chunk_scores[chunk_id]['chunk_data'] = {
            'chunk_id': chunk_id,
            'content': result['content'],
            'metadata': {
                'pdf_id': result['pdf_id'],
                'page_number': result.get('page_number', 0)
            }
        }
    
    # Process semantic results
    for result in semantic_results:
        chunk_id = result['chunk_id']
        chunk_scores[chunk_id]['semantic_score'] = result['similarity_score']
        if not chunk_scores[chunk_id]['chunk_data']:
            chunk_scores[chunk_id]['chunk_data'] = {
                'chunk_id': chunk_id,
                'content': result['content'],
                'metadata': result['metadata']
            }
    
    # Process graph results
    for result in graph_results:
        chunk_id = result.get('chunk_id')
        if chunk_id:
            chunk_scores[chunk_id]['graph_score'] = result.get('relevance_score', 0.5)
            if not chunk_scores[chunk_id]['chunk_data']:
                # Try to get chunk from vector store or use graph result data
                try:
                    # Search for the chunk in vector store
                    chunk_results = vector_store.search("", limit=1000, pdf_id=result.get('pdf_id'))
                    for chunk_result in chunk_results:
                        if chunk_result['chunk_id'] == chunk_id:
                            chunk_scores[chunk_id]['chunk_data'] = {
                                'chunk_id': chunk_id,
                                'content': chunk_result.get('content', ''),
                                'metadata': chunk_result.get('metadata', {
                                    'pdf_id': result.get('pdf_id', ''),
                                    'page_number': 0
                                })
                            }
                            break
                except:
                    # Fallback: use graph result data
                    chunk_scores[chunk_id]['chunk_data'] = {
                        'chunk_id': chunk_id,
                        'content': '',
                        'metadata': {
                            'pdf_id': result.get('pdf_id', ''),
                            'page_number': 0
                        }
                    }
    
    # Calculate weighted fusion scores
    final_results = []
    for chunk_id, scores in chunk_scores.items():
        if scores['chunk_data']:
            # Weighted fusion: BM25 (0.3) + Semantic (0.4) + Graph (0.3)
            final_score = (
                0.3 * scores['bm25_score'] +
                0.4 * scores['semantic_score'] +
                0.3 * scores['graph_score']
            )
            
            final_results.append({
                **scores['chunk_data'],
                'similarity_score': final_score,
                'bm25_score': scores['bm25_score'],
                'semantic_score': scores['semantic_score'],
                'graph_score': scores['graph_score']
            })
    
    # Sort by final score
    final_results.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    return final_results[:limit]


# Summarize PDF
@app.post("/pdfs/{pdf_id}/summarize")
async def summarize_pdf(pdf_id: str, request: SummarizeRequest):
    """Generate PDF summary"""
    print(f"\n{'='*60}")
    print(f"📨 Received summarize request")
    print(f"   PDF ID: {pdf_id}")
    print(f"{'='*60}\n")
    
    try:
        # Check if PDF exists
        pdf_info = mysql_handler.get_pdf(pdf_id)
        if not pdf_info:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        result = summarizer.summarize_pdf(pdf_id, max_length=request.max_length)
        
        return {
            "success": True,
            "summary": result['summary'],
            "key_points": result['key_points'],
            "word_count": result['word_count'],
            "pdf_filename": pdf_info['filename']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Summarize failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Get statistics
@app.get("/stats")
async def get_stats():
    """Get system statistics"""
    try:
        mysql_stats = mysql_handler.get_stats()
        total_chunks_vector = vector_store.get_total_chunks()
        
        stats = {
            **mysql_stats,
            'total_chunks_vector': total_chunks_vector
        }
        
        return {
            "success": True,
            "stats": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)