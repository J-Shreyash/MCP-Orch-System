"""
Vector Store - ChromaDB Handler for RAG System

"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import os
from sentence_transformers import SentenceTransformer


class VectorStore:
    """Handles vector storage and similarity search with ChromaDB"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB and embedding model"""
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection with error handling
        try:
            self.collection = self.client.get_or_create_collection(
                name="pdf_chunks",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            # Check if it's a schema error
            error_str = str(e)
            if "no such column" in error_str.lower() or "collections.topic" in error_str:
                print("⚠️ ChromaDB schema mismatch detected. Resetting database...")
                print("💡 This usually happens after ChromaDB version updates")
                
                try:
                    # Close the client first
                    self.client = None
                    import gc
                    gc.collect()
                    import time
                    
                    # Quick check: Try to delete a test file to see if directory is locked
                    sqlite_file = os.path.join(persist_directory, "chroma.sqlite3")
                    is_locked = False
                    
                    if os.path.exists(sqlite_file):
                        try:
                            # Quick attempt to rename (test if locked)
                            test_rename = sqlite_file + ".test"
                            os.rename(sqlite_file, test_rename)
                            os.rename(test_rename, sqlite_file)
                        except (PermissionError, OSError):
                            is_locked = True
                    
                    # If locked, immediately use fallback directory (skip deletion attempts)
                    if is_locked:
                        print("💡 ChromaDB directory is locked by another process")
                        print("💡 Using fallback directory to allow server to start immediately")
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        persist_directory = f"{persist_directory}_new_{timestamp}"
                        print(f"📁 New ChromaDB directory: {persist_directory}")
                        os.makedirs(persist_directory, exist_ok=True)
                        self.persist_directory = persist_directory
                    else:
                        # Not locked, try to delete normally
                        print("⏳ Attempting to reset ChromaDB directory...")
                        import shutil
                        
                        # Try once quickly
                        try:
                            if os.path.exists(sqlite_file):
                                os.remove(sqlite_file)
                                print("✅ Deleted SQLite file")
                            
                            if os.path.exists(persist_directory):
                                shutil.rmtree(persist_directory)
                                print("✅ Removed corrupted directory")
                            
                            os.makedirs(persist_directory, exist_ok=True)
                            print("✅ Directory recreated")
                        except (PermissionError, OSError) as pe:
                            # If deletion fails, use fallback
                            print(f"⚠️ Could not delete directory: {pe}")
                            print("💡 Using fallback directory to allow server to start")
                            import datetime
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            persist_directory = f"{persist_directory}_new_{timestamp}"
                            print(f"📁 New ChromaDB directory: {persist_directory}")
                            os.makedirs(persist_directory, exist_ok=True)
                            self.persist_directory = persist_directory
                    
                    # Recreate client
                    self.client = chromadb.PersistentClient(
                        path=persist_directory,
                        settings=Settings(
                            anonymized_telemetry=False,
                            allow_reset=True
                        )
                    )
                    
                    # Create new collection
                    self.collection = self.client.create_collection(
                        name="pdf_chunks",
                        metadata={"hnsw:space": "cosine"}
                    )
                    print("✅ ChromaDB database reset successfully")
                except Exception as reset_error:
                    print(f"❌ Could not reset ChromaDB: {reset_error}")
                    print("💡 Please manually delete the 'chroma_db' directory and restart the server")
                    raise
            else:
                # Re-raise if it's not a schema error
                raise
        
        # Initialize embedding model
        print("📦 Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        print("✅ ChromaDB connected successfully!")
        print(f"   Collection: pdf_chunks")
        print(f"   Items: {self.collection.count()}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        embedding = self.embedding_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    def add_chunks(self, chunks: List[Dict]) -> int:
        """
        Add multiple chunks to vector store
        Each chunk should have: chunk_id, content, metadata
        """
        try:
            if not chunks:
                return 0
            
            print(f"\n💾 Storing {len(chunks)} chunks in vector database...")
            
            # Prepare data
            chunk_ids = []
            documents = []
            metadatas = []
            embeddings = []
            
            print("   🔢 Generating embeddings...")
            for chunk in chunks:
                chunk_id = chunk['chunk_id']
                content = chunk['content']
                metadata = chunk['metadata']
                
                # Generate embedding
                embedding = self.generate_embedding(content)
                
                chunk_ids.append(chunk_id)
                documents.append(content)
                metadatas.append(metadata)
                embeddings.append(embedding)
            
            # Add to ChromaDB
            print("   📥 Adding to ChromaDB...")
            self.collection.add(
                ids=chunk_ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            
            print(f"✅ {len(chunks)} chunks stored successfully!")
            
            return len(chunks)
        
        except Exception as e:
            print(f"❌ Error adding chunks: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def search(self, query: str, limit: int = 5, pdf_id: Optional[str] = None) -> List[Dict]:
        """
        Search for similar chunks
        Returns list of chunks with similarity scores
        """
        try:
            print(f"\n🔍 Searching: '{query[:50]}...'")
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Build where clause
            where = None
            if pdf_id:
                where = {"pdf_id": pdf_id}
            
            # Search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            
            if results['ids'] and len(results['ids'][0]) > 0:
                for idx in range(len(results['ids'][0])):
                    chunk_id = results['ids'][0][idx]
                    content = results['documents'][0][idx]
                    metadata = results['metadatas'][0][idx]
                    distance = results['distances'][0][idx]
                    
                    # Convert distance to similarity (cosine distance -> similarity)
                    similarity = 1 - distance
                    
                    formatted_results.append({
                        'chunk_id': chunk_id,
                        'content': content,
                        'metadata': metadata,
                        'similarity_score': similarity,
                        'distance': distance
                    })
            
            print(f"✅ Found {len(formatted_results)} results")
            
            return formatted_results
        
        except Exception as e:
            print(f"❌ Search error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_chunks_by_pdf(self, pdf_id: str, limit: int = 50) -> List[Dict]:
        """Get all chunks for a specific PDF"""
        try:
            results = self.collection.get(
                where={"pdf_id": pdf_id},
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            formatted_results = []
            
            if results['ids']:
                for idx in range(len(results['ids'])):
                    chunk_id = results['ids'][idx]
                    content = results['documents'][idx]
                    metadata = results['metadatas'][idx]
                    
                    formatted_results.append({
                        'chunk_id': chunk_id,
                        'content': content,
                        'metadata': metadata
                    })
            
            return formatted_results
        
        except Exception as e:
            print(f"❌ Error getting chunks: {e}")
            return []
    
    def delete_pdf_chunks(self, pdf_id: str) -> int:
        """
        DELETE PDF CHUNKS - NEW METHOD
        Delete all chunks for a specific PDF
        Returns number of chunks deleted
        """
        try:
            print(f"\n🗑️ Deleting chunks for PDF: {pdf_id}")
            
            # Get all chunk IDs for this PDF first
            results = self.collection.get(
                where={"pdf_id": pdf_id},
                include=["metadatas"]
            )
            
            chunk_ids = results['ids']
            num_chunks = len(chunk_ids)
            
            if num_chunks == 0:
                print(f"ℹ️ No chunks found for PDF: {pdf_id}")
                return 0
            
            print(f"   Found {num_chunks} chunks to delete")
            
            # Delete all chunks
            self.collection.delete(
                where={"pdf_id": pdf_id}
            )
            
            print(f"✅ Deleted {num_chunks} chunks from ChromaDB")
            
            return num_chunks
        
        except Exception as e:
            print(f"❌ Error deleting chunks: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def get_total_chunks(self) -> int:
        """Get total number of chunks in collection"""
        try:
            return self.collection.count()
        except:
            return 0
    
    def reset_collection(self):
        """Reset the entire collection (USE WITH CAUTION!)"""
        try:
            print("⚠️ Resetting ChromaDB collection...")
            self.client.delete_collection("pdf_chunks")
            self.collection = self.client.create_collection(
                name="pdf_chunks",
                metadata={"hnsw:space": "cosine"}
            )
            print("✅ Collection reset successfully")
        except Exception as e:
            print(f"❌ Reset failed: {e}")