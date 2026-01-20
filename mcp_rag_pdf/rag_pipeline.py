"""
RAG Pipeline - Production Ready Question-Answering System
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""
from typing import List, Dict, Optional
import os
from openai import OpenAI


class RAGPipeline:
    """Handles RAG question-answering with GPT"""
    
    def __init__(self, vector_store, mysql_handler):
        """Initialize RAG Pipeline"""
        self.vector_store = vector_store
        self.mysql = mysql_handler
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        
        print("🤖 RAG Pipeline initialized with GPT-4o-mini")
    
    def ask_question(self, question: str, pdf_id: Optional[str] = None, 
                    max_chunks: int = 5) -> Dict:
        """
        Answer a question using RAG - FIXED CONFIDENCE
        """
        print(f"\n{'='*60}")
        print(f"❓ RAG Question: '{question}'")
        if pdf_id:
            print(f"   Limited to PDF: {pdf_id}")
        print(f"{'='*60}\n")
        
        try:
            # Step 1: Retrieve relevant chunks
            print("🔍 Searching for relevant content...")
            search_results = self.vector_store.search(
                query=question,
                limit=max_chunks,
                pdf_id=pdf_id
            )
            
            if not search_results:
                return {
                    'answer': "I couldn't find any relevant information in the uploaded PDFs to answer your question.",
                    'sources': [],
                    'confidence': 0.0
                }
            
            print(f"✅ Found {len(search_results)} relevant chunks")
            
            # Step 2: Build context from chunks
            context_parts = []
            sources = []
            
            for idx, result in enumerate(search_results, 1):
                # Get PDF info
                pdf_info = self.mysql.get_pdf(result['metadata']['pdf_id'])
                
                if pdf_info:
                    chunk_text = result['content']
                    pdf_name = pdf_info['filename']
                    page_num = result['metadata'].get('page_number', 'Unknown')
                    
                    context_parts.append(
                        f"[Source {idx}: {pdf_name}, Page {page_num}]\n{chunk_text}\n"
                    )
                    
                    sources.append({
                        'chunk_id': result['chunk_id'],
                        'pdf_id': result['metadata']['pdf_id'],
                        'pdf_filename': pdf_name,
                        'content': chunk_text[:200] + "...",
                        'page_number': page_num,
                        'similarity_score': result['similarity_score']
                    })
            
            combined_context = "\n---\n".join(context_parts)
            
            # Step 3: Generate answer with GPT
            print("🤖 Generating answer with GPT-4o-mini...")
            
            system_prompt = """You are an intelligent AI assistant that answers questions based on PDF documents.

Your task:
1. Read the provided context from PDF documents carefully
2. Answer the user's question accurately using ONLY the information from the context
3. If the context doesn't contain enough information, say so honestly
4. Provide detailed, well-structured answers when possible
5. Reference specific sources when making claims
6. Use clear formatting with bullet points, numbered lists, or paragraphs as appropriate

Guidelines:
- Be comprehensive but concise
- Use professional language
- If answering about a book, provide structured summaries with sections
- Always stay factual - never make up information
- If uncertain, express appropriate confidence levels"""

            user_prompt = f"""Based on the following context from PDF documents, please answer this question:

QUESTION: {question}

CONTEXT FROM PDFs:
{combined_context}

Please provide a comprehensive answer based on the context above. Structure your response clearly and reference the sources when relevant."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            answer = response.choices[0].message.content
            
            # Calculate confidence properly
            if sources:
                # Get average similarity score
                avg_similarity = sum(s['similarity_score'] for s in sources) / len(sources)
                
                # Ensure confidence is between 0 and 1
                if avg_similarity < 0:
                    # Convert from range [-1, 1] to [0, 1]
                    confidence = (avg_similarity + 1) / 2
                else:
                    # Already in [0, 1] range
                    confidence = min(avg_similarity, 1.0)
                
                # Boost slightly if multiple high-quality sources
                if len(sources) >= 3 and confidence > 0.5:
                    confidence = min(confidence * 1.1, 1.0)
            else:
                confidence = 0.0
            
            print(f"\n✅ Answer generated!")
            print(f"   Confidence: {confidence:.2%}")
            print(f"   Sources used: {len(sources)}")
            
            # Log activity
            self.mysql.log_activity(
                "rag_question",
                pdf_id or "multiple",
                f"Q: {question[:50]}... | Confidence: {confidence:.2%}"
            )
            
            return {
                'answer': answer,
                'sources': sources,
                'confidence': confidence
            }
        
        except Exception as e:
            print(f"❌ RAG failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'answer': f"I encountered an error while processing your question: {str(e)}",
                'sources': [],
                'confidence': 0.0
            }
    
    def summarize_pdf_intelligent(self, pdf_id: str) -> Dict:
        """Generate intelligent summary using GPT"""
        try:
            # Get PDF info
            pdf_info = self.mysql.get_pdf(pdf_id)
            if not pdf_info:
                return {'summary': 'PDF not found', 'key_points': []}
            
            # Get all chunks
            chunks = self.vector_store.get_chunks_by_pdf(pdf_id, limit=50)
            
            if not chunks:
                return {'summary': 'No content available', 'key_points': []}
            
            # Combine content (limit to avoid token limits)
            combined_text = "\n\n".join([chunk['content'] for chunk in chunks[:20]])
            
            prompt = f"""Please provide a comprehensive summary of this document.

Document: {pdf_info['filename']}

Content:
{combined_text}

Provide:
1. A detailed summary (2-3 paragraphs)
2. Key topics covered
3. Main insights or findings

Format your response clearly with sections."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert document summarizer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            summary = response.choices[0].message.content
            
            return {
                'summary': summary,
                'key_points': [],
                'word_count': len(summary.split())
            }
        
        except Exception as e:
            print(f"❌ Summary failed: {e}")
            return {
                'summary': f"Error: {str(e)}",
                'key_points': [],
                'word_count': 0
            }