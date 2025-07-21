import ebooklib
from ebooklib import epub
import fitz  # PyMuPDF
import re
from typing import Dict, List
from bs4 import BeautifulSoup
import os

class BookParser:
    def parse_book(self, file_path: str, filename: str) -> Dict:
        """Parse EPUB or PDF and extract chapters"""
        if filename.lower().endswith('.epub'):
            return self._parse_epub(file_path)
        elif filename.lower().endswith('.pdf'):
            return self._parse_pdf(file_path)
        else:
            raise ValueError("Unsupported file format")
    
    def _parse_epub(self, file_path: str) -> Dict:
        """Parse EPUB file and extract chapters"""
        try:
            book = epub.read_epub(file_path)
            
            # Get metadata
            title = book.get_metadata('DC', 'title')
            title = title[0][0] if title else "Unknown Title"
            
            chapters = []
            
            # Get all items that are actual content (not CSS, images, etc.)
            items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
            
            for i, item in enumerate(items):
                # Parse HTML content
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                
                # Extract text content
                text = soup.get_text()
                
                # Clean up text
                text = re.sub(r'\s+', ' ', text).strip()
                
                # Skip very short chapters (likely navigation or metadata)
                if len(text) < 100:
                    continue
                
                # Try to extract chapter title
                chapter_title = self._extract_chapter_title(soup, text)
                if not chapter_title:
                    chapter_title = f"Chapter {len(chapters) + 1}"
                
                chapters.append({
                    "title": chapter_title,
                    "content": text
                })
            
            return {
                "title": title,
                "chapters": chapters
            }
            
        except Exception as e:
            raise ValueError(f"Error parsing EPUB: {str(e)}")
    
    def _parse_pdf(self, file_path: str) -> Dict:
        """Parse PDF file and extract chapters"""
        try:
            doc = fitz.open(file_path)
            
            # Get metadata
            metadata = doc.metadata
            title = metadata.get('title', 'Unknown Title')
            
            # Extract all text
            full_text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                full_text += page.get_text()
            
            doc.close()
            
            # Split into chapters based on common patterns
            chapters = self._split_pdf_into_chapters(full_text)
            
            return {
                "title": title,
                "chapters": chapters
            }
            
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {str(e)}")
    
    def _extract_chapter_title(self, soup: BeautifulSoup, text: str) -> str:
        """Extract chapter title from HTML or text"""
        # Look for heading tags first
        for tag in ['h1', 'h2', 'h3']:
            heading = soup.find(tag)
            if heading:
                title = heading.get_text().strip()
                if title and len(title) < 100:
                    return title
        
        # Fallback: look for "Chapter" pattern in first few lines
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            if re.match(r'^(Chapter|CHAPTER)\s+\d+', line):
                return line
            if re.match(r'^\d+\.\s+', line) and len(line) < 50:
                return line
        
        return ""
    
    def _split_pdf_into_chapters(self, text: str) -> List[Dict]:
        """Split PDF text into chapters based on patterns"""
        # Common chapter patterns
        chapter_patterns = [
            r'\n\s*Chapter\s+\d+[:\.\s]',
            r'\n\s*CHAPTER\s+\d+[:\.\s]',
            r'\n\s*\d+\.\s+[A-Z][a-z]+',
            r'\n\s*[IVX]+\.\s+[A-Z][a-z]+',
        ]
        
        # Find potential chapter breaks
        breaks = [0]  # Start of document
        
        for pattern in chapter_patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE))
            for match in matches:
                breaks.append(match.start())
        
        # Remove duplicates and sort
        breaks = sorted(list(set(breaks)))
        
        # If no chapters found, split by page breaks or length
        if len(breaks) <= 1:
            return self._split_by_length(text)
        
        chapters = []
        for i in range(len(breaks)):
            start = breaks[i]
            end = breaks[i + 1] if i + 1 < len(breaks) else len(text)
            
            chunk = text[start:end].strip()
            if len(chunk) < 100:  # Skip very short chunks
                continue
            
            # Extract title from beginning of chunk
            lines = chunk.split('\n')[:3]
            title = self._extract_title_from_lines(lines)
            if not title:
                title = f"Chapter {len(chapters) + 1}"
            
            chapters.append({
                "title": title,
                "content": chunk
            })
        
        return chapters
    
    def _split_by_length(self, text: str, target_length: int = 5000) -> List[Dict]:
        """Split text into chunks of roughly equal length"""
        words = text.split()
        chapters = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            current_chunk.append(word)
            current_length += len(word) + 1
            
            if current_length >= target_length:
                chapters.append({
                    "title": f"Section {len(chapters) + 1}",
                    "content": " ".join(current_chunk)
                })
                current_chunk = []
                current_length = 0
        
        # Add remaining content
        if current_chunk:
            chapters.append({
                "title": f"Section {len(chapters) + 1}",
                "content": " ".join(current_chunk)
            })
        
        return chapters
    
    def _extract_title_from_lines(self, lines: List[str]) -> str:
        """Extract title from first few lines of text"""
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for chapter patterns
            if re.match(r'^(Chapter|CHAPTER)\s+\d+', line):
                return line
            
            # Look for numbered sections
            if re.match(r'^\d+\.\s+', line) and len(line) < 50:
                return line
            
            # Look for short lines that might be titles
            if len(line) < 50 and len(line) > 5:
                return line
        
        return ""