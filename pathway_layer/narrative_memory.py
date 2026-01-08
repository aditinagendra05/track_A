import pathway as pw
from typing import Dict, List, Any
from loguru import logger
import re
from datetime import datetime

class NarrativeMemory:
    """
    Maintain structured narrative knowledge:
    - Timeline of events
    - Character registry
    - Location registry
    - Relationship graph
    """
    
    def __init__(self):
        self.timeline = []
        self.characters = {}
        self.locations = {}
        self.relationships = []
        
        logger.info("Narrative memory initialized")
    
    def extract_timeline(self, chunks_table: pw.Table) -> List[Dict[str, Any]]:
        """
        Extract temporal events from text
        
        Returns:
            List of events with: {event, date, book_id, chunk_id}
        """
        logger.info("Extracting timeline from narrative")
        
        events = []
        
        # Date patterns to look for
        date_patterns = [
            r'\b\d{4}\b',  # Year (e.g., 1815)
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
        ]
        
        for row in chunks_table:
            text = row['chunk_text']
            chunk_id = row['chunk_id']
            book_id = row['book_id']
            
            for pattern in date_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    date_str = match.group()
                    context = self._get_context(text, match.start(), match.end())
                    
                    events.append({
                        'date': date_str,
                        'event': context,
                        'book_id': book_id,
                        'chunk_id': chunk_id
                    })
        
        # Sort by date
        self.timeline = sorted(events, key=lambda x: self._parse_date(x['date']))
        
        logger.success(f"Extracted {len(self.timeline)} temporal events")
        return self.timeline
    
    def extract_characters(self, chunks_table: pw.Table) -> Dict[str, Any]:
        """
        Extract character mentions and attributes
        
        Returns:
            Dict of {character_name: {mentions, attributes, book_id}}
        """
        logger.info("Extracting character information")
        
        # Simple capitalized word detection (can be enhanced with NER)
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        
        for row in chunks_table:
            text = row['chunk_text']
            book_id = row['book_id']
            chunk_id = row['chunk_id']
            
            names = re.findall(name_pattern, text)
            
            for name in names:
                # Filter out common false positives
                if name in ['The', 'Chapter', 'Book', 'Page']:
                    continue
                
                if name not in self.characters:
                    self.characters[name] = {
                        'mentions': [],
                        'attributes': set(),
                        'books': set()
                    }
                
                self.characters[name]['mentions'].append({
                    'chunk_id': chunk_id,
                    'context': text[:200]
                })
                self.characters[name]['books'].add(book_id)
        
        logger.success(f"Extracted {len(self.characters)} character entities")
        return self.characters
    
    def get_character_timeline(self, character_name: str) -> List[Dict[str, Any]]:
        """Get all timeline events involving a character"""
        return [
            event for event in self.timeline
            if character_name.lower() in event['event'].lower()
        ]
    
    def get_temporal_context(self, date_str: str, window: int = 5) -> List[Dict[str, Any]]:
        """
        Get events near a specific date
        
        Args:
            date_str: Date string to search around
            window: Number of events before/after to return
            
        Returns:
            List of events in temporal window
        """
        target_date = self._parse_date(date_str)
        
        # Find closest event
        closest_idx = 0
        min_diff = float('inf')
        
        for i, event in enumerate(self.timeline):
            event_date = self._parse_date(event['date'])
            diff = abs(event_date - target_date)
            if diff < min_diff:
                min_diff = diff
                closest_idx = i
        
        # Return window around closest event
        start_idx = max(0, closest_idx - window)
        end_idx = min(len(self.timeline), closest_idx + window + 1)
        
        return self.timeline[start_idx:end_idx]
    
    @staticmethod
    def _get_context(text: str, start: int, end: int, window: int = 100) -> str:
        """Extract context around a match"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    @staticmethod
    def _parse_date(date_str: str) -> int:
        """Parse date string to comparable integer"""
        # Extract year
        year_match = re.search(r'\b(\d{4})\b', date_str)
        if year_match:
            return int(year_match.group(1))
        return 0