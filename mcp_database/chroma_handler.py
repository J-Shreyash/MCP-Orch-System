"""
ChromaDB Handler - Manages vector database operations
Stores document embeddings for semantic search
"""
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import uuid


class ChromaHandler:
    """Handles all ChromaDB vector operations"""
    
    def __init__(self, persist_directory="./chroma_db"):
        """
        Initialize ChromaDB Handler
        
        Args:
            persist_directory: Where to store ChromaDB data
        """
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.connect()
    
    def connect(self):
        """Connect to ChromaDB and initialize embedding model"""
        try:
            print("🔌 Connecting to ChromaDB...")
            
            # Initialize ChromaDB client
            self.client = chromadb.Client(Settings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="documents",
                metadata={"description": "Document embeddings for semantic search"}
            )
            
            # Initialize embedding model
            print("📦 Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            print("✅ ChromaDB connected successfully!")
            return True
        
        except Exception as e:
            print(f"❌ ChromaDB connection failed: {e}")
            return False
    
    def add_document(self, doc_id: str, content: str, metadata: Dict = None) -> bool:
        """
        Add a document to ChromaDB with embeddings
        
        Args:
            doc_id: Unique document ID
            content: Document content to embed
            metadata: Additional metadata (should include 'title')
            
        Returns:
            Success boolean
        """
        try:
            # Get title from metadata or use doc_id
            metadata = metadata or {}
            title = metadata.get('title', doc_id)
            
            # Combine title and content for embedding
            text_to_embed = f"{title}\n\n{content}"
            
            # Generate embedding
            print(f"🔢 Generating embedding for: {doc_id}")
            embedding = self.embedding_model.encode([text_to_embed])[0]
            
            # Prepare metadata
            doc_metadata = metadata.copy()
            doc_metadata['title'] = title
            doc_metadata['length'] = len(content)
            
            # Add to ChromaDB
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding.tolist()],
                documents=[content],
                metadatas=[doc_metadata]
            )
            
            print(f"✅ Document added to ChromaDB: {doc_id}")
            return True
        
        except Exception as e:
            print(f"❌ Add document failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def search(self, query: str, n_results: int = 10, where: Dict = None) -> Dict:
        """
        Search for similar documents using semantic search
        
        Args:
            query: Search query text
            n_results: Number of results
            where: Filter conditions
            
        Returns:
            ChromaDB query results
        """
        try:
            print(f"🔍 Searching ChromaDB for: '{query}'")
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=where
            )
            
            print(f"✅ Found {len(results.get('ids', [[]])[0])} results")
            return results
        
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return {}
    
    def search_similar(self, query: str, limit: int = 10, where: Dict = None) -> List[Dict]:
        """
        Search for similar documents using semantic search (legacy method)
        
        Args:
            query: Search query text
            limit: Number of results
            where: Filter conditions
            
        Returns:
            List of similar documents with scores
        """
        try:
            print(f"🔍 Searching ChromaDB for: '{query}'")
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0]
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=limit,
                where=where
            )
            
            # Format results
            formatted_results = []
            if results and results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'doc_id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                    })
            
            print(f"✅ Found {len(formatted_results)} similar documents")
            return formatted_results
        
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Get a specific document by ID"""
        try:
            result = self.collection.get(
                ids=[doc_id],
                include=['documents', 'metadatas', 'embeddings']
            )
            
            if result and result['ids']:
                return {
                    'doc_id': result['ids'][0],
                    'content': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            
            return None
        
        except Exception as e:
            print(f"❌ Get document failed: {e}")
            return None
    
    def update_document(self, doc_id: str, title: str = None, 
                       content: str = None, metadata: Dict = None) -> bool:
        """Update a document in ChromaDB"""
        try:
            # Get existing document
            existing = self.get_document(doc_id)
            if not existing:
                print(f"⚠️  Document not found: {doc_id}")
                return False
            
            # Prepare updates
            update_content = content if content else existing['content']
            update_metadata = metadata if metadata else existing['metadata']
            
            if title:
                update_metadata['title'] = title
                text_to_embed = f"{title}\n\n{update_content}"
            else:
                text_to_embed = f"{update_metadata.get('title', '')}\n\n{update_content}"
            
            # Generate new embedding
            embedding = self.embedding_model.encode([text_to_embed])[0]
            
            # Update in ChromaDB
            self.collection.update(
                ids=[doc_id],
                embeddings=[embedding.tolist()],
                documents=[update_content],
                metadatas=[update_metadata]
            )
            
            print(f"✅ Document updated in ChromaDB: {doc_id}")
            return True
        
        except Exception as e:
            print(f"❌ Update failed: {e}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from ChromaDB"""
        try:
            self.collection.delete(ids=[doc_id])
            print(f"✅ Document deleted from ChromaDB: {doc_id}")
            return True
        
        except Exception as e:
            print(f"❌ Delete failed: {e}")
            return False
    
    def get_document_count(self) -> int:
        """Get total number of documents in collection"""
        try:
            return self.collection.count()
        except Exception as e:
            print(f"❌ Count failed: {e}")
            return 0
    
    def get_all_documents(self, limit: int = 100) -> List[Dict]:
        """Get all documents (or up to limit)"""
        try:
            result = self.collection.get(
                include=['documents', 'metadatas'],
                limit=limit
            )
            
            documents = []
            if result and result['ids']:
                for i in range(len(result['ids'])):
                    documents.append({
                        'doc_id': result['ids'][i],
                        'content': result['documents'][i],
                        'metadata': result['metadatas'][i]
                    })
            
            return documents
        
        except Exception as e:
            print(f"❌ Get all failed: {e}")
            return []
    
    def is_connected(self) -> bool:
        """Check if ChromaDB is connected"""
        try:
            return self.client is not None and self.collection is not None
        except:
            return False
    
    def get_collections(self) -> List[str]:
        """Get list of all collections"""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            print(f"❌ Get collections failed: {e}")
            return []