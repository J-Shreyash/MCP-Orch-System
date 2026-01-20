"""
BM25 Handler - Free, Production-Ready Keyword Search for PDFs
Uses BM25 ranking algorithm for accurate keyword search on PDF chunks
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""
from rank_bm25 import BM25Okapi
from typing import List, Dict, Optional
import re
from collections import defaultdict


class BM25Handler:
    """Handles BM25 keyword search operations for PDF chunks"""
    
    def __init__(self):
        """Initialize BM25 Handler"""
        self.bm25_index = None
        self.chunks = []  # Store chunk texts
        self.chunk_metadata = {}  # Map chunk_id to metadata
        self.tokenized_chunks = []  # Tokenized chunks for BM25
        print("✅ BM25 Handler initialized for PDFs")
    
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
    
    def add_chunks(self, chunks: List[Dict]):
        """
        Index chunks for BM25 search
        
        Args:
            chunks: List of dicts with 'chunk_id', 'pdf_id', 'content', 'page_number'
        """
        print(f"📚 Indexing {len(chunks)} chunks for BM25...")
        
        self.chunks = []
        self.tokenized_chunks = []
        self.chunk_metadata = {}
        
        for chunk in chunks:
            chunk_id = chunk['chunk_id']
            content = chunk.get('content', '')
            pdf_id = chunk.get('pdf_id', '')
            page_number = chunk.get('page_number', 0)
            
            # Use content as searchable text
            searchable_text = content
            
            self.chunks.append({
                'chunk_id': chunk_id,
                'pdf_id': pdf_id,
                'content': content,
                'page_number': page_number,
                'full_text': searchable_text
            })
            
            # Tokenize for BM25
            tokens = self.tokenize(searchable_text)
            self.tokenized_chunks.append(tokens)
            
            # Store metadata
            self.chunk_metadata[chunk_id] = {
                'chunk_id': chunk_id,
                'pdf_id': pdf_id,
                'content': content,
                'page_number': page_number,
                'metadata': chunk.get('metadata', {})
            }
        
        # Build BM25 index
        if self.tokenized_chunks:
            self.bm25_index = BM25Okapi(self.tokenized_chunks)
            print(f"✅ BM25 index built with {len(self.chunks)} chunks")
        else:
            print("⚠️  No chunks to index")
            self.bm25_index = None
    
    def search(self, query: str, limit: int = 10, 
               pdf_id: Optional[str] = None) -> List[Dict]:
        """
        Search chunks using BM25
        
        Args:
            query: Search query text
            limit: Number of results
            pdf_id: Filter by PDF ID (optional)
            
        Returns:
            List of search results with BM25 scores
        """
        if not self.bm25_index or not self.chunks:
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
            chunk = self.chunks[idx]
            chunk_id = chunk['chunk_id']
            metadata = self.chunk_metadata[chunk_id]
            
            # Filter by PDF ID if specified
            if pdf_id and metadata['pdf_id'] != pdf_id:
                continue
            
            # Normalize score (BM25 scores can vary, normalize to 0-1)
            # BM25 scores are typically 0-20, normalize to 0-1
            normalized_score = min(score / 20.0, 1.0) if score > 0 else 0.0
            
            results.append({
                'chunk_id': chunk_id,
                'pdf_id': metadata['pdf_id'],
                'content': metadata['content'],
                'page_number': metadata['page_number'],
                'bm25_score': float(score),
                'similarity_score': normalized_score,
                'metadata': metadata['metadata']
            })
        
        # Sort by BM25 score (descending)
        results.sort(key=lambda x: x['bm25_score'], reverse=True)
        
        # Return top results
        return results[:limit]
    
    def add_chunk(self, chunk_id: str, pdf_id: str, content: str,
                  page_number: int = 0, metadata: Dict = None):
        """
        Add a single chunk to BM25 index
        
        Args:
            chunk_id: Chunk ID
            pdf_id: PDF ID
            content: Chunk content
            page_number: Page number
            metadata: Additional metadata
        """
        chunk = {
            'chunk_id': chunk_id,
            'pdf_id': pdf_id,
            'content': content,
            'page_number': page_number,
            'metadata': metadata or {}
        }
        self.add_chunks([chunk])
    
    def update_chunk(self, chunk_id: str, content: str = None, **kwargs):
        """
        Update a chunk in BM25 index
        
        Args:
            chunk_id: Chunk ID
            content: New content (optional)
            **kwargs: Other fields to update
        """
        if chunk_id in self.chunk_metadata:
            if content:
                self.chunk_metadata[chunk_id]['content'] = content
            
            # Update other fields
            for key, value in kwargs.items():
                if key in self.chunk_metadata[chunk_id]:
                    self.chunk_metadata[chunk_id][key] = value
            
            # Find chunk in list and update
            for idx, chunk in enumerate(self.chunks):
                if chunk['chunk_id'] == chunk_id:
                    # Rebuild searchable text
                    content_text = content or chunk['content']
                    
                    self.chunks[idx]['content'] = content_text
                    self.chunks[idx]['full_text'] = content_text
                    self.tokenized_chunks[idx] = self.tokenize(content_text)
                    break
            
            # Rebuild BM25 index
            if self.tokenized_chunks:
                self.bm25_index = BM25Okapi(self.tokenized_chunks)
                print(f"✅ BM25 index updated for chunk: {chunk_id}")
    
    def remove_chunk(self, chunk_id: str):
        """
        Remove a chunk from BM25 index
        
        Args:
            chunk_id: Chunk ID to remove
        """
        # Find and remove
        for idx, chunk in enumerate(self.chunks):
            if chunk['chunk_id'] == chunk_id:
                self.chunks.pop(idx)
                self.tokenized_chunks.pop(idx)
                break
        
        # Remove from metadata
        if chunk_id in self.chunk_metadata:
            del self.chunk_metadata[chunk_id]
        
        # Rebuild index
        if self.tokenized_chunks:
            self.bm25_index = BM25Okapi(self.tokenized_chunks)
            print(f"✅ Chunk removed from BM25 index: {chunk_id}")
        else:
            self.bm25_index = None
            print("✅ BM25 index cleared (no chunks)")
    
    def remove_pdf_chunks(self, pdf_id: str):
        """
        Remove all chunks for a PDF from BM25 index
        
        Args:
            pdf_id: PDF ID
        """
        chunk_ids_to_remove = [
            chunk_id for chunk_id, metadata in self.chunk_metadata.items()
            if metadata['pdf_id'] == pdf_id
        ]
        
        for chunk_id in chunk_ids_to_remove:
            self.remove_chunk(chunk_id)
    
    def get_stats(self) -> Dict:
        """
        Get BM25 index statistics
        
        Returns:
            Dictionary with index statistics
        """
        return {
            'indexed_chunks': len(self.chunks),
            'index_built': self.bm25_index is not None
        }
