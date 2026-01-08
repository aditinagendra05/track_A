from typing import List, Dict, Any
from loguru import logger
from pathway_layer.narrative_memory import NarrativeMemory

class CausalChecker:
    """Verify causal and temporal consistency of narrative claims"""
    
    def __init__(self, memory: NarrativeMemory = None):
        self.memory = memory
        logger.info("CausalChecker initialized")
    
    def check_timeline_consistency(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if events are temporally consistent
        
        Args:
            events: List of events with dates/temporal info
            
        Returns:
            Dict with consistency status and issues
        """
        logger.debug("Checking timeline consistency")
        
        issues = []
        consistent = True
        
        # Sort events by date
        dated_events = [e for e in events if 'date' in e and e['date']]
        
        if len(dated_events) < 2:
            return {
                'consistent': True,
                'issues': [],
                'message': 'Insufficient temporal data'
            }
        
        # Parse dates and sort
        parsed_events = []
        for event in dated_events:
            try:
                year = self._extract_year(event['date'])
                if year:
                    parsed_events.append({
                        'event': event.get('description', str(event)),
                        'year': year,
                        'raw_date': event['date']
                    })
            except Exception as e:
                logger.warning(f"Could not parse date: {event['date']}")
        
        parsed_events.sort(key=lambda x: x['year'])
        
        # Check for temporal impossibilities
        for i in range(len(parsed_events) - 1):
            current = parsed_events[i]
            next_event = parsed_events[i + 1]
            
            # Check if causally connected events are in wrong order
            if self._events_causally_connected(current, next_event):
                if current['year'] > next_event['year']:
                    consistent = False
                    issues.append(
                        f"Temporal violation: '{current['event']}' ({current['year']}) "
                        f"occurs after '{next_event['event']}' ({next_event['year']}) "
                        f"but should precede it"
                    )
        
        return {
            'consistent': consistent,
            'issues': issues,
            'timeline': parsed_events
        }
    
    def check_causal_coherence(
        self,
        claim: str,
        evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if cause-effect relationships make sense
        
        Args:
            claim: The claim being verified
            evidence: Supporting evidence
            
        Returns:
            Dict with coherence status
        """
        logger.debug("Checking causal coherence")
        
        # Look for causal indicators in claim
        causal_keywords = [
            'because', 'caused', 'led to', 'resulted in',
            'therefore', 'thus', 'consequently', 'due to'
        ]
        
        has_causal_claim = any(keyword in claim.lower() for keyword in causal_keywords)
        
        if not has_causal_claim:
            return {
                'coherent': True,
                'issues': [],
                'message': 'No explicit causal claims detected'
            }
        
        # Check if evidence supports causal chain
        issues = []
        
        # Simple heuristic: look for prerequisite events
        # This is a placeholder for more sophisticated causal reasoning
        
        return {
            'coherent': True,
            'issues': issues,
            'message': 'Causal analysis requires domain-specific logic'
        }
    
    def check_character_plausibility(
        self,
        character: str,
        action: str,
        context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if character action is plausible given their attributes
        
        Args:
            character: Character name
            action: Action they supposedly took
            context: Contextual information from text
            
        Returns:
            Dict with plausibility assessment
        """
        logger.debug(f"Checking plausibility: {character} -> {action}")
        
        if not self.memory:
            return {
                'plausible': True,
                'confidence': 0.5,
                'message': 'No character memory available'
            }
        
        # Get character information
        char_info = self.memory.characters.get(character, {})
        
        if not char_info:
            return {
                'plausible': True,
                'confidence': 0.3,
                'message': f'No information about character "{character}"'
            }
        
        # Check if character has necessary attributes/skills
        # This is a placeholder for more sophisticated reasoning
        
        return {
            'plausible': True,
            'confidence': 0.7,
            'mentions': len(char_info.get('mentions', [])),
            'message': f'Character appears {len(char_info.get("mentions", []))} times in text'
        }
    
    def check_world_rules(
        self,
        claim: str,
        book_context: str
    ) -> Dict[str, Any]:
        """
        Check if claim violates established world rules
        
        Args:
            claim: The claim to check
            book_context: Information about the story world
            
        Returns:
            Dict with rule compliance status
        """
        logger.debug("Checking world rules compliance")
        
        # Detect anachronisms for historical fiction
        anachronism_keywords = {
            'phone', 'computer', 'internet', 'airplane', 'email',
            'television', 'radio', 'car', 'electricity'
        }
        
        issues = []
        claim_lower = claim.lower()
        
        for keyword in anachronism_keywords:
            if keyword in claim_lower:
                # Check if book is historical (simple heuristic)
                if any(year < 1900 for year in self._extract_all_years(book_context)):
                    issues.append(
                        f"Potential anachronism: '{keyword}' in historical setting"
                    )
        
        return {
            'compliant': len(issues) == 0,
            'issues': issues
        }
    
    @staticmethod
    def _extract_year(date_str: str) -> int:
        """Extract year from date string"""
        import re
        year_match = re.search(r'\b(\d{4})\b', str(date_str))
        if year_match:
            return int(year_match.group(1))
        return 0
    
    @staticmethod
    def _extract_all_years(text: str) -> List[int]:
        """Extract all year mentions from text"""
        import re
        years = re.findall(r'\b(\d{4})\b', text)
        return [int(y) for y in years if 1000 <= int(y) <= 2100]
    
    @staticmethod
    def _events_causally_connected(event1: Dict, event2: Dict) -> bool:
        """
        Heuristic to determine if events are causally connected
        
        This is a simplified version. Real implementation would use
        NLP techniques or explicit causal markers.
        """
        # Simple heuristic: events within 10 years might be connected
        return abs(event1['year'] - event2['year']) <= 10