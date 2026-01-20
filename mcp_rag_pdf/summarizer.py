"""
Summarizer - Generates intelligent summaries using GPT
Company: Sepia ML - Production Ready
"""
from typing import List, Dict
import os
from openai import OpenAI


class Summarizer:
    """Handles PDF summarization with GPT"""
    
    def __init__(self, vector_store, mysql_handler):
        """Initialize Summarizer"""
        self.vector_store = vector_store
        self.mysql = mysql_handler
        
        # Initialize OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        
        print("📝 Summarizer initialized with GPT-4o-mini")
    
    def summarize_pdf(self, pdf_id: str, max_length: int = 500) -> Dict:
        """
        Generate intelligent summary of a PDF using GPT
        
        Args:
            pdf_id: PDF identifier
            max_length: Maximum summary length in words
            
        Returns:
            Dictionary with summary and key points
        """
        print(f"\n{'='*60}")
        print(f"📋 Summarizing PDF: {pdf_id}")
        print(f"{'='*60}\n")
        
        try:
            # Get PDF info
            pdf_info = self.mysql.get_pdf(pdf_id)
            if not pdf_info:
                return {
                    'summary': "PDF not found",
                    'key_points': [],
                    'word_count': 0
                }
            
            # Get chunks from PDF
            print("📚 Retrieving PDF content...")
            chunks = self.vector_store.get_chunks_by_pdf(pdf_id, limit=50)
            
            if not chunks:
                return {
                    'summary': "No content available",
                    'key_points': [],
                    'word_count': 0
                }
            
            print(f"   Found {len(chunks)} chunks")
            
            # Combine content (smart sampling)
            total_chunks = len(chunks)
            selected_chunks = []
            
            if total_chunks <= 20:
                selected_chunks = chunks
            else:
                # Smart sampling: beginning, middle, end
                selected_chunks.extend(chunks[:8])
                selected_chunks.extend(chunks[total_chunks//2-4:total_chunks//2+4])
                selected_chunks.extend(chunks[-8:])
            
            combined_text = "\n\n".join([chunk['content'] for chunk in selected_chunks])
            
            # Limit text to avoid token limits
            if len(combined_text) > 25000:
                combined_text = combined_text[:25000] + "\n[... content truncated ...]"
            
            # Generate summary with GPT
            print("🤖 Generating intelligent summary with GPT...")
            
            summary_prompt = f"""Please provide a comprehensive summary of this document.

Document Title: {pdf_info['filename']}
Total Pages: {pdf_info.get('page_count', 'Unknown')}

Content:
{combined_text}

Please provide:
1. A detailed summary covering the main topics and key information
2. The summary should be well-structured with clear sections
3. Length: approximately {max_length} words
4. Use professional language

Format your response as a cohesive, readable summary."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert document summarizer. Create comprehensive, well-structured summaries that capture the essence of documents."
                    },
                    {
                        "role": "user",
                        "content": summary_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=min(max_length * 2, 2000)
            )
            
            summary = response.choices[0].message.content
            word_count = len(summary.split())
            
            # Extract key points with GPT
            print("🔑 Extracting key points...")
            
            key_points_prompt = f"""Based on this document summary, extract 5-7 key points or main takeaways.

Summary:
{summary}

Provide key points as a simple bullet list, each point should be concise (1-2 sentences)."""

            key_points_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Extract key points from summaries in a clear, concise format."
                    },
                    {
                        "role": "user",
                        "content": key_points_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse key points
            key_points_text = key_points_response.choices[0].message.content
            key_points = [
                line.strip().lstrip('•-*').strip() 
                for line in key_points_text.split('\n') 
                if line.strip() and len(line.strip()) > 10
            ][:7]
            
            print(f"\n✅ Summary generated!")
            print(f"   Words: {word_count}")
            print(f"   Key points: {len(key_points)}\n")
            
            # Log activity
            self.mysql.log_activity(
                "summarize_pdf",
                pdf_id,
                f"Generated summary: {word_count} words"
            )
            
            return {
                'summary': summary,
                'key_points': key_points,
                'word_count': word_count
            }
        
        except Exception as e:
            print(f"❌ Summarization failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'summary': f"Error generating summary: {str(e)}",
                'key_points': [],
                'word_count': 0
            }
    
    def quick_summary(self, pdf_id: str) -> str:
        """Generate brief summary (one paragraph)"""
        result = self.summarize_pdf(pdf_id, max_length=150)
        return result['summary']