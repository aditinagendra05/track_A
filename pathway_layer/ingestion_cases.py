import pathway as pw
import pandas as pd
from pathlib import Path
from loguru import logger
from config import config

class CaseIngestionPipeline:
    """Ingest test cases from CSV files"""
    
    def __init__(self):
        self.splits_path = config.paths.splits
        
    def ingest_train(self) -> pw.Table:
        """Load training cases"""
        return self._load_csv("train.csv")
    
    def ingest_test(self) -> pw.Table:
        """Load test cases"""
        return self._load_csv("test.csv")
    
    def _load_csv(self, filename: str) -> pw.Table:
        """
        Load cases from CSV file
        
        Expected CSV columns:
        - id: unique case identifier
        - book_id: reference to source book
        - claim: the statement to verify
        - label: ground truth (SUPPORTED/CONTRADICTED/NOT_DECIDABLE) - optional for test
        
        Returns:
            Pathway table with case data
        """
        filepath = self.splits_path / filename
        
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return self._empty_table()
        
        try:
            df = pd.read_csv(filepath)
            logger.info(f"Loaded {len(df)} cases from {filename}")
            
            # Validate required columns
            required_cols = ['id', 'book_id', 'claim']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                return self._empty_table()
            
            # Convert to Pathway table
            table = pw.debug.table_from_pandas(df)
            
            return table
            
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return self._empty_table()
    
    @staticmethod
    def _empty_table() -> pw.Table:
        """Create empty table with correct schema"""
        class CaseSchema(pw.Schema):
            id: str
            book_id: str
            claim: str
            label: str = ""
        
        return pw.debug.table_from_rows(schema=CaseSchema, rows=[])
    
    def watch_csv(self, filename: str) -> pw.Table:
        """
        Watch CSV file for real-time updates
        
        Args:
            filename: CSV file to watch
            
        Returns:
            Streaming Pathway table
        """
        filepath = self.splits_path / filename
        logger.info(f"Watching CSV: {filepath}")
        
        table = pw.io.csv.read(
            path=str(filepath),
            mode='streaming',
            autocommit_duration_ms=1000
        )
        
        return table