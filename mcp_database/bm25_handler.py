"""
BM25 Handler - Free, Production-Ready Keyword Search
Uses BM25 ranking algorithm for accurate keyword search
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""
from rank_bm25 import BM25Okapi
from typing import List, Dict, Optional
import re
from collections import defaultdict


class BM25Handler:
    """Handles BM25 keyword search operations"""
    
    def __init__(self):
        """Initialize BM25 Handler"""
        self.bm25_index = None
        self.documents = []  # Store document texts
        self.doc_metadata = {}  # Map doc_id to metadata
        self.tokenized_docs = []  # Tokenized documents for BM25
        print("✅ BM25 Handler initialized")
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25
        Simple tokenization - can be enhanced with better tokenizers
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        # Convert to lowercase and split on whitespace/punctuation
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def add_documents(self, documents: List[Dict]):
        """
        Index documents for BM25 search
        
        Args:
            documents: List of dicts with 'doc_id', 'title', 'content'
        """
        print(f"📚 Indexing {len(documents)} documents for BM25...")
        
        self.documents = []
        self.tokenized_docs = []
        self.doc_metadata = {}
        
        for doc in documents:
            doc_id = doc['doc_id']
            title = doc.get('title', '')
            content = doc.get('content', '')
            
            # Combine title and content (title weighted more)
            # Title appears 3x to boost title matches
            searchable_text = f"{title} {title} {title} {content}"
            
            self.documents.append({
                'doc_id': doc_id,
                'title': title,
                'content': content,
                'full_text': searchable_text
            })
            
            # Tokenize for BM25
            tokens = self.tokenize(searchable_text)
            self.tokenized_docs.append(tokens)
            
            # Store metadata
            self.doc_metadata[doc_id] = {
                'title': title,
                'content': content,
                'metadata': doc.get('metadata', {}),
                'category': doc.get('category', 'general'),
                'tags': doc.get('tags', [])
            }
        
        # Build BM25 index
        if self.tokenized_docs:
            self.bm25_index = BM25Okapi(self.tokenized_docs)
            print(f"✅ BM25 index built with {len(self.documents)} documents")
        else:
            print("⚠️  No documents to index")
            self.bm25_index = None
    
    def search(self, query: str, limit: int = 10, 
               category: Optional[str] = None) -> List[Dict]:
        """
        Search documents using BM25
        
        Args:
            query: Search query text
            limit: Number of results
            category: Filter by category (optional)
            
        Returns:
            List of search results with BM25 scores
        """
        if not self.bm25_index or not self.documents:
            print("⚠️  BM25 index not built yet")
            return []
        
        # Tokenize query
        query_tokens = self.tokenize(query)
        
        if not query_tokens:
            return []
        
        # Get BM25 scores
        scores = self.bm25_index.get_scores(query_tokens)
        
        # Create results with scores
        results = []
        for idx, score in enumerate(scores):
            doc = self.documents[idx]
            doc_id = doc['doc_id']
            metadata = self.doc_metadata[doc_id]
            
            # Filter by category if specified
            if category and metadata['category'] != category:
                continue
            
            # Normalize score (BM25 scores can vary, normalize to 0-1)
            # BM25 scores are typically 0-20, normalize to 0-1
            normalized_score = min(score / 20.0, 1.0) if score > 0 else 0.0
            
            results.append({
                'doc_id': doc_id,
                'title': metadata['title'],
                'content': metadata['content'],
                'bm25_score': float(score),
                'similarity_score': normalized_score,
                'metadata': metadata['metadata'],
                'category': metadata['category'],
                'tags': metadata['tags']
            })
        
        # Sort by BM25 score (descending)
        results.sort(key=lambda x: x['bm25_score'], reverse=True)
        
        # Return top results
        return results[:limit]
    
    def add_document(self, doc_id: str, title: str, content: str,
                    metadata: Dict = None, category: str = "general",
                    tags: List[str] = None):
        """
        Add a single document to BM25 index
        
        Args:
            doc_id: Document ID
            title: Document title
            content: Document content
            metadata: Additional metadata
            category: Document category
            tags: Document tags
        """
        doc = {
            'doc_id': doc_id,
            'title': title,
            'content': content,
            'metadata': metadata or {},
            'category': category,
            'tags': tags or []
        }
        self.add_documents([doc])
    
    def update_document(self, doc_id: str, title: str = None, 
                       content: str = None, **kwargs):
        """
        Update a document in BM25 index
        Note: For efficiency, you might want to rebuild index periodically
        
        Args:
            doc_id: Document ID
            title: New title (optional)
            content: New content (optional)
            **kwargs: Other fields to update
        """
        if doc_id in self.doc_metadata:
            if title:
                self.doc_metadata[doc_id]['title'] = title
            if content:
                self.doc_metadata[doc_id]['content'] = content
            
            # Update other fields
            for key, value in kwargs.items():
                if key in self.doc_metadata[doc_id]:
                    self.doc_metadata[doc_id][key] = value
            
            # Find document in list and update
            for idx, doc in enumerate(self.documents):
                if doc['doc_id'] == doc_id:
                    # Rebuild searchable text
                    title_text = title or doc['title']
                    content_text = content or doc['content']
                    searchable_text = f"{title_text} {title_text} {title_text} {content_text}"
                    
                    self.documents[idx]['full_text'] = searchable_text
                    self.documents[idx]['title'] = title_text
                    self.documents[idx]['content'] = content_text
                    self.tokenized_docs[idx] = self.tokenize(searchable_text)
                    break
            
            # Rebuild BM25 index
            if self.tokenized_docs:
                self.bm25_index = BM25Okapi(self.tokenized_docs)
                print(f"✅ BM25 index updated for document: {doc_id}")
    
    def remove_document(self, doc_id: str):
        """
        Remove a document from BM25 index
        
        Args:
            doc_id: Document ID to remove
        """
        # Find and remove
        for idx, doc in enumerate(self.documents):
            if doc['doc_id'] == doc_id:
                self.documents.pop(idx)
                self.tokenized_docs.pop(idx)
                break
        
        # Remove from metadata
        if doc_id in self.doc_metadata:
            del self.doc_metadata[doc_id]
        
        # Rebuild index
        if self.tokenized_docs:
            self.bm25_index = BM25Okapi(self.tokenized_docs)
            print(f"✅ Document removed from BM25 index: {doc_id}")
        else:
            self.bm25_index = None
            print("✅ BM25 index cleared (no documents)")
    
    def get_stats(self) -> Dict:
        """
        Get BM25 index statistics
        
        Returns:
            Dictionary with index statistics
        """
        return {
            'indexed_documents': len(self.documents),
            'index_built': self.bm25_index is not None
        }
