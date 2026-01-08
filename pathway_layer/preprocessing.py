import pathway as pw
import re
from typing import List, Dict
from loguru import logger
from config import config

class TextPreprocessor:
    """Clean and chunk text for indexing"""
    
    def __init__(self):
        self.chunk_size = config.processing.chunk_size
        self.chunk_overlap = config.processing.chunk_overlap
        
    def process_books(self, books_table: pw.Table) -> pw.Table:
        """
        Clean and chunk book content
        
        Args:
            books_table: Table with book_id, title, content
            
        Returns:
            Table with book_id, chunk_id, chunk_text, metadata
        """
        logger.info("Processing books: cleaning and chunking")
        
        # Apply cleaning
        cleaned_table = books_table.select(
            book_id=pw.this.book_id,
            title=pw.this.title,
            content=pw.apply(self._clean_text, pw.this.content)
        )
        
        # Apply chunking
        chunked_table = cleaned_table.select(
            book_id=pw.this.book_id,
            title=pw.this.title,
            chunks=pw.apply(self._chunk_text, pw.this.content)
        )
        
        # Flatten chunks into separate rows
        exploded_table = chunked_table.flatten(pw.this.chunks)
        
        # Add chunk IDs and metadata
        final_table = exploded_table.select(
            book_id=pw.this.book_id,
            chunk_id=pw.apply(
                lambda bid, idx: f"{bid}_chunk_{idx}",
                pw.this.book_id,
                pw.this.id
            ),
            chunk_text=pw.this.chunks,
            title=pw.this.title
        )
        
        logger.success("Book processing complete")
        return final_table
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean text content"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers
        text = re.sub(r'Page \d+', '', text)
        text = re.sub(r'Chapter [IVXLCDM]+', '', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text.strip()
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Full text content
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        
        i = 0
        while i < len(words):
            # Take chunk_size words
            chunk_words = words[i:i + self.chunk_size]
            chunk = ' '.join(chunk_words)
            chunks.append(chunk)
            
            # Move forward by (chunk_size - overlap)
            i += (self.chunk_size - self.chunk_overlap)
        
        logger.debug(f"Created {len(chunks)} chunks from {len(words)} words")
        return chunks