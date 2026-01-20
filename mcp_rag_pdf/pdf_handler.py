"""
PDF Handler - Processes and extracts content from PDF files
Company: Sepia ML | Complete Production Version
"""
import PyPDF2
import pdfplumber
from pathlib import Path
import os
from typing import Dict, List, Optional, Tuple
import uuid
from datetime import datetime


class PDFHandler:
    """Handles all PDF processing operations"""
    
    def __init__(self, upload_directory="./uploads"):
        """
        Initialize PDF Handler
        
        Args:
            upload_directory: Directory to store uploaded PDFs
        """
        self.upload_directory = Path(upload_directory)
        self.upload_directory.mkdir(parents=True, exist_ok=True)
        print(f"📁 PDF upload directory: {self.upload_directory}")
    
    def extract_pdf_content(self, file_path: str) -> Dict:
        """
        CRITICAL METHOD - Extract text content from PDF
        Called by server.py for PDF processing
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with full_text, page_count, and pages list
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")
        
        print(f"📄 Extracting text from: {file_path.name}")
        
        try:
            # Try pdfplumber first (better extraction)
            pages = []
            full_text = ""
            
            try:
                with pdfplumber.open(str(file_path)) as pdf:
                    page_count = len(pdf.pages)
                    
                    for page_num, page in enumerate(pdf.pages, 1):
                        text = page.extract_text()
                        
                        if text:
                            pages.append({
                                'page_number': page_num,
                                'text': text.strip()
                            })
                            full_text += text + "\n\n"
                            print(f"   Page {page_num}: {len(text)} characters")
            except Exception as e:
                print(f"   pdfplumber failed: {e}, trying PyPDF2...")
            
            # Fallback to PyPDF2 if pdfplumber returns empty
            if not full_text.strip():
                print("   Trying PyPDF2 fallback...")
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    page_count = len(pdf_reader.pages)
                    
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        text = page.extract_text()
                        
                        if text:
                            pages.append({
                                'page_number': page_num,
                                'text': text.strip()
                            })
                            full_text += text + "\n\n"
            
            print(f"✅ Extracted {len(pages)} pages\n")
            
            return {
                'full_text': full_text.strip(),
                'page_count': len(pages),
                'pages': pages
            }
        
        except Exception as e:
            print(f"❌ PDF extraction failed: {e}")
            raise
    
    def save_pdf(self, file_content: bytes, filename: str) -> Tuple[str, str]:
        """
        Save uploaded PDF file
        
        Args:
            file_content: PDF file bytes
            filename: Original filename
            
        Returns:
            Tuple of (pdf_id, saved_path)
        """
        try:
            # Generate unique PDF ID
            pdf_id = str(uuid.uuid4())
            
            # Create safe filename
            safe_filename = f"{pdf_id}_{filename}"
            file_path = self.upload_directory / safe_filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            print(f"✅ PDF saved: {safe_filename}")
            return pdf_id, str(file_path)
        
        except Exception as e:
            print(f"❌ Failed to save PDF: {e}")
            raise
    
    def extract_text(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from PDF with page information
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of dicts with page content
        """
        pages_content = []
        
        try:
            print(f"📄 Extracting text from: {pdf_path}")
            
            # Try pdfplumber first
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, start=1):
                        text = page.extract_text()
                        
                        if text and text.strip():
                            pages_content.append({
                                'page_number': page_num,
                                'content': text.strip(),
                                'char_count': len(text)
                            })
                            print(f"   Page {page_num}: {len(text)} characters")
            except Exception as e:
                print(f"   pdfplumber failed: {e}, trying PyPDF2...")
            
            # Fallback to PyPDF2
            if not pages_content:
                print("   Trying PyPDF2 fallback...")
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        
                        if text and text.strip():
                            pages_content.append({
                                'page_number': page_num + 1,
                                'content': text.strip(),
                                'char_count': len(text)
                            })
            
            print(f"✅ Extracted {len(pages_content)} pages")
            return pages_content
        
        except Exception as e:
            print(f"❌ Text extraction failed: {e}")
            return []
    
    def get_pdf_metadata(self, pdf_path: str) -> Dict:
        """Extract PDF metadata"""
        try:
            metadata = {
                'file_size': os.path.getsize(pdf_path),
                'page_count': 0,
                'title': None,
                'author': None,
                'creation_date': None
            }
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                metadata['page_count'] = len(pdf_reader.pages)
                
                if pdf_reader.metadata:
                    metadata['title'] = pdf_reader.metadata.get('/Title')
                    metadata['author'] = pdf_reader.metadata.get('/Author')
                    metadata['creation_date'] = pdf_reader.metadata.get('/CreationDate')
            
            return metadata
        
        except Exception as e:
            print(f"⚠️  Metadata extraction failed: {e}")
            return {
                'file_size': os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0,
                'page_count': 0,
                'title': None,
                'author': None,
                'creation_date': None
            }
    
    def process_pdf(self, file_content: bytes, filename: str) -> Dict:
        """Complete PDF processing pipeline"""
        print(f"\n{'='*60}")
        print(f"📚 Processing PDF: {filename}")
        print(f"{'='*60}\n")
        
        try:
            # Save PDF
            pdf_id, pdf_path = self.save_pdf(file_content, filename)
            
            # Extract metadata
            print("📊 Extracting metadata...")
            metadata = self.get_pdf_metadata(pdf_path)
            
            # Extract text
            print("📝 Extracting text content...")
            pages_content = self.extract_text(pdf_path)
            
            if not pages_content:
                print("⚠️  No text content extracted!")
            
            # Calculate statistics
            total_chars = sum(page['char_count'] for page in pages_content)
            
            result = {
                'pdf_id': pdf_id,
                'filename': filename,
                'pdf_path': pdf_path,
                'file_size': metadata['file_size'],
                'page_count': metadata['page_count'],
                'pages_content': pages_content,
                'total_characters': total_chars,
                'metadata': metadata,
                'processed_at': datetime.now().isoformat()
            }
            
            print(f"\n✅ PDF Processing Complete!")
            print(f"   Pages: {metadata['page_count']}")
            print(f"   Characters: {total_chars:,}")
            print(f"   Size: {metadata['file_size']:,} bytes\n")
            
            return result
        
        except Exception as e:
            print(f"❌ PDF processing failed: {e}")
            raise
    
    def get_pdf_path(self, pdf_id: str, filename: str) -> Optional[str]:
        """Get the file path for a PDF"""
        safe_filename = f"{pdf_id}_{filename}"
        file_path = self.upload_directory / safe_filename
        
        if file_path.exists():
            return str(file_path)
        return None
    
    def delete_pdf_file(self, pdf_path: str) -> bool:
        """Delete a PDF file from disk"""
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                print(f"✅ PDF file deleted: {pdf_path}")
                return True
            else:
                print(f"⚠️  PDF file not found: {pdf_path}")
            return False
        except Exception as e:
            print(f"❌ Failed to delete PDF: {e}")
            return False
    
    def list_uploaded_pdfs(self) -> List[str]:
        """List all uploaded PDF files"""
        try:
            pdf_files = list(self.upload_directory.glob("*.pdf"))
            return [str(f) for f in pdf_files]
        except Exception as e:
            print(f"❌ Failed to list PDFs: {e}")
            return []
    
    def get_storage_size(self) -> float:
        """Get total storage used by PDFs in MB"""
        try:
            total_size = 0
            for pdf_file in self.upload_directory.glob("*.pdf"):
                total_size += os.path.getsize(pdf_file)
            
            return total_size / (1024 * 1024)  # Convert to MB
        except Exception as e:
            print(f"❌ Failed to calculate storage: {e}")
            return 0.0
    
    def validate_pdf(self, pdf_path: str) -> Tuple[bool, str]:
        """Validate if a file is a valid PDF"""
        try:
            if not os.path.exists(pdf_path):
                return False, "File not found"
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if len(pdf_reader.pages) == 0:
                    return False, "PDF has no pages"
                
                # Try to extract text from first page
                first_page = pdf_reader.pages[0]
                _ = first_page.extract_text()
            
            return True, "Valid PDF"
        
        except Exception as e:
            return False, f"Invalid PDF: {str(e)}"
    
    def get_page_text(self, pdf_path: str, page_number: int) -> Optional[str]:
        """Get text from a specific page"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if page_number < 1 or page_number > len(pdf_reader.pages):
                    print(f"⚠️  Invalid page number: {page_number}")
                    return None
                
                page = pdf_reader.pages[page_number - 1]
                text = page.extract_text()
                
                return text.strip() if text else None
        
        except Exception as e:
            print(f"❌ Failed to get page text: {e}")
            return None
    
    def search_text_in_pdf(self, pdf_path: str, search_term: str) -> List[Dict]:
        """Search for text in PDF"""
        matches = []
        
        try:
            pages_content = self.extract_text(pdf_path)
            
            for page_data in pages_content:
                page_num = page_data['page_number']
                content = page_data['content']
                
                if search_term.lower() in content.lower():
                    lines = content.split('\n')
                    for line_num, line in enumerate(lines, 1):
                        if search_term.lower() in line.lower():
                            matches.append({
                                'page': page_num,
                                'line': line_num,
                                'text': line.strip(),
                                'context': line.strip()
                            })
            
            print(f"🔍 Found {len(matches)} matches for '{search_term}'")
            return matches
        
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get statistics about uploaded PDFs"""
        try:
            pdf_files = self.list_uploaded_pdfs()
            total_files = len(pdf_files)
            total_size = self.get_storage_size()
            
            total_pages = 0
            for pdf_path in pdf_files:
                try:
                    metadata = self.get_pdf_metadata(pdf_path)
                    total_pages += metadata['page_count']
                except:
                    continue
            
            stats = {
                'total_pdfs': total_files,
                'total_pages': total_pages,
                'total_size_mb': round(total_size, 2),
                'average_size_mb': round(total_size / total_files, 2) if total_files > 0 else 0,
                'average_pages': round(total_pages / total_files, 1) if total_files > 0 else 0,
                'upload_directory': str(self.upload_directory)
            }
            
            return stats
        
        except Exception as e:
            print(f"❌ Failed to get statistics: {e}")
            return {
                'total_pdfs': 0,
                'total_pages': 0,
                'total_size_mb': 0,
                'average_size_mb': 0,
                'average_pages': 0,
                'upload_directory': str(self.upload_directory)
            }