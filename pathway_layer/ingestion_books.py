import pathway as pw
from pathlib import Path
from loguru import logger
from typing import Dict, Any
from config import config

class BookIngestionPipeline:
    """Ingest novels from data/books/ directory"""
    
    def __init__(self):
        self.books_path = config.paths.books
        
    def ingest(self) -> pw.Table:
        """
        Stream novels from the books directory
        
        Returns:
            Pathway table with columns: book_id, title, content
        """
        logger.info(f"Ingesting books from {self.books_path}")
        
        # Define schema for book data
        class BookSchema(pw.Schema):
            book_id: str
            title: str
            content: str
            filepath: str
            
        # Read all .txt files from books directory
        books_data = []
        for filepath in self.books_path.glob("*.txt"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                book_id = filepath.stem
                title = self._format_title(book_id)
                
                books_data.append({
                    'book_id': book_id,
                    'title': title,
                    'content': content,
                    'filepath': str(filepath)
                })
                
                logger.info(f"Loaded book: {title} ({len(content)} chars)")
                
            except Exception as e:
                logger.error(f"Error loading {filepath}: {e}")
        
        # Create Pathway table from the data
        if books_data:
            table = pw.debug.table_from_rows(
                schema=BookSchema,
                rows=books_data
            )
            logger.success(f"Ingested {len(books_data)} books")
            return table
        else:
            logger.warning("No books found")
            return pw.debug.table_from_rows(schema=BookSchema, rows=[])
    
    @staticmethod
    def _format_title(book_id: str) -> str:
        """Convert filename to readable title"""
        return book_id.replace('_', ' ').title()

    def watch_directory(self) -> pw.Table:
        """
        Watch books directory for changes (real-time streaming)
        
        Returns:
            Pathway table that updates when files change
        """
        logger.info(f"Watching directory: {self.books_path}")
        
        # Use Pathway's file connector for streaming
        table = pw.io.fs.read(
            path=str(self.books_path),
            format='binary',
            mode='streaming',
            with_metadata=True
        )
        
        return table