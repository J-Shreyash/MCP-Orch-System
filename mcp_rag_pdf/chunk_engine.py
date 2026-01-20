"""
Chunk Engine - Intelligently splits PDF content into manageable chunks
Uses semantic chunking with overlap for better context preservation
Company: Sepia ML - Production Ready
"""
from typing import List, Dict
import re
import uuid


class ChunkEngine:
    """Handles intelligent text chunking for RAG"""
    
    def __init__(self, chunk_size=500, chunk_overlap=50):
        """
        Initialize Chunk Engine
        
        Args:
            chunk_size: Target size of each chunk (in characters)
            chunk_overlap: Overlap between chunks (in characters)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        print(f"🔧 Chunk Engine initialized (size: {chunk_size}, overlap: {chunk_overlap})")
    
    def create_chunks(self, pdf_data: Dict, pdf_id: str) -> List[Dict]:
        """
        CRITICAL METHOD - Create chunks from PDF data
        This is the main entry point called by server.py
        
        Args:
            pdf_data: Dictionary with 'pages' list from pdf_handler.extract_pdf_content()
            pdf_id: PDF identifier
            
        Returns:
            List of chunk dictionaries ready for vector store
        """
        print(f"\n🔪 Creating chunks for PDF: {pdf_id}")
        print(f"   Chunk size: {self.chunk_size} chars")
        print(f"   Overlap: {self.chunk_overlap} chars\n")
        
        pages = pdf_data.get('pages', [])
        
        if not pages:
            print("⚠️ No pages found in PDF data")
            return []
        
        all_chunks = []
        chunk_index = 0
        
        for page in pages:
            page_number = page.get('page_number')
            text = page.get('text', '')
            
            if not text or not text.strip():
                continue
            
            # Chunk this page
            page_chunks = self.chunk_text(text, pdf_id, page_number)
            
            # Add chunk_id and chunk_index to each chunk
            for chunk_data in page_chunks:
                chunk_id = f"{pdf_id}_chunk_{chunk_index}"
                
                # Format for vector store
                formatted_chunk = {
                    'chunk_id': chunk_id,
                    'content': chunk_data['content'],
                    'metadata': {
                        'pdf_id': pdf_id,
                        'page_number': page_number,
                        'chunk_index': chunk_index,
                        'char_count': chunk_data['char_count']
                    }
                }
                
                all_chunks.append(formatted_chunk)
                chunk_index += 1
            
            print(f"   Page {page_number}: {len(page_chunks)} chunks created")
        
        print(f"\n✅ Total chunks created: {len(all_chunks)}\n")
        return all_chunks
    
    def chunk_text(self, text: str, pdf_id: str, page_number: int = None) -> List[Dict]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to chunk
            pdf_id: PDF identifier
            page_number: Page number (optional)
            
        Returns:
            List of chunk dictionaries
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        
        # Clean text
        text = self._clean_text(text)
        
        # Split into sentences for better chunking
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        current_chunk_sentences = []
        
        for sentence in sentences:
            # Check if adding this sentence exceeds chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Save current chunk
                chunk_dict = {
                    'content': current_chunk.strip(),
                    'pdf_id': pdf_id,
                    'page_number': page_number,
                    'char_count': len(current_chunk),
                    'sentence_count': len(current_chunk_sentences)
                }
                chunks.append(chunk_dict)
                
                # Start new chunk with overlap
                overlap_text = self._create_overlap(current_chunk_sentences)
                current_chunk = overlap_text
                current_chunk_sentences = [s for s in current_chunk_sentences[-2:]]  # Keep last 2 sentences
            
            # Add sentence to current chunk
            current_chunk += sentence + " "
            current_chunk_sentences.append(sentence)
        
        # Add final chunk
        if current_chunk.strip():
            chunk_dict = {
                'content': current_chunk.strip(),
                'pdf_id': pdf_id,
                'page_number': page_number,
                'char_count': len(current_chunk),
                'sentence_count': len(current_chunk_sentences)
            }
            chunks.append(chunk_dict)
        
        return chunks
    
    def chunk_pdf_pages(self, pages_content: List[Dict], pdf_id: str) -> List[Dict]:
        """
        Chunk all pages from a PDF (alternative method)
        
        Args:
            pages_content: List of page dictionaries with content
            pdf_id: PDF identifier
            
        Returns:
            List of all chunks from all pages
        """
        print(f"\n🔪 Chunking PDF content...")
        print(f"   Chunk size: {self.chunk_size} chars")
        print(f"   Overlap: {self.chunk_overlap} chars\n")
        
        all_chunks = []
        chunk_index = 0
        
        for page in pages_content:
            page_number = page.get('page_number')
            content = page.get('content', '')
            
            if not content:
                continue
            
            # Chunk this page
            page_chunks = self.chunk_text(content, pdf_id, page_number)
            
            # Add chunk index
            for chunk in page_chunks:
                chunk['chunk_index'] = chunk_index
                chunk_index += 1
            
            all_chunks.extend(page_chunks)
            print(f"   Page {page_number}: {len(page_chunks)} chunks")
        
        print(f"\n✅ Total chunks created: {len(all_chunks)}\n")
        return all_chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\'""]', '', text)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with NLTK)
        sentence_endings = re.compile(r'([.!?])\s+')
        sentences = sentence_endings.split(text)
        
        # Reconstruct sentences
        result = []
        for i in range(0, len(sentences)-1, 2):
            sentence = sentences[i] + sentences[i+1]
            result.append(sentence.strip())
        
        # Add last part if exists
        if len(sentences) % 2 == 1:
            result.append(sentences[-1].strip())
        
        return [s for s in result if s]
    
    def _create_overlap(self, sentences: List[str]) -> str:
        """
        Create overlap text from last few sentences
        
        Args:
            sentences: List of sentences
            
        Returns:
            Overlap text
        """
        if not sentences:
            return ""
        
        # Take last 2 sentences or until overlap size
        overlap_text = ""
        for sentence in reversed(sentences):
            if len(overlap_text) + len(sentence) <= self.chunk_overlap:
                overlap_text = sentence + " " + overlap_text
            else:
                break
        
        return overlap_text.strip()
    
    def get_chunk_stats(self, chunks: List[Dict]) -> Dict:
        """Get statistics about chunks"""
        if not chunks:
            return {
                'total_chunks': 0,
                'avg_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0,
                'total_chars': 0
            }
        
        char_counts = [c['char_count'] for c in chunks]
        
        return {
            'total_chunks': len(chunks),
            'avg_chunk_size': sum(char_counts) / len(char_counts),
            'min_chunk_size': min(char_counts),
            'max_chunk_size': max(char_counts),
            'total_chars': sum(char_counts)
        }
    
    def rechunk_if_needed(self, chunks: List[Dict], max_size: int = 1000) -> List[Dict]:
        """Rechunk if chunks are too large"""
        result = []
        
        for chunk in chunks:
            if chunk['char_count'] <= max_size:
                result.append(chunk)
            else:
                # Split large chunk
                content = chunk['content']
                sub_chunks = self.chunk_text(
                    content,
                    chunk['pdf_id'],
                    chunk.get('page_number')
                )
                result.extend(sub_chunks)
        
        return result