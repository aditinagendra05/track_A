from typing import List, Dict, Any
from loguru import logger
from pathway_layer.indexing import VectorIndexer
from pathway_layer.narrative_memory import NarrativeMemory
from config import config

class Retriever:
    """Retrieve relevant text excerpts for claim verification"""
    
    def __init__(self, indexer: VectorIndexer, memory: NarrativeMemory = None):
        self.indexer = indexer
        self.memory = memory
        self.top_k = config.processing.top_k_retrieval
        logger.info("Retriever initialized")
    
    def retrieve(
        self,
        claim: str,
        book_id: str = None,
        atomic_statements: List[Dict[str, str]] = None,
        entities: Dict[str, List[str]] = None,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant excerpts for claim verification
        
        Args:
            claim: Main claim text
            book_id: Optional book filter
            atomic_statements: Decomposed atomic statements
            entities: Extracted entities (characters, dates, etc.)
            top_k: Number of results
            
        Returns:
            List of excerpts with relevance scores
        """
        if top_k is None:
            top_k = self.top_k
        
        logger.info(f"Retrieving excerpts for claim (top_k={top_k})")
        
        # Strategy 1: Search for main claim
        main_results = self.indexer.search(claim, book_id=book_id, top_k=top_k)
        
        # Strategy 2: Search for each atomic statement
        atomic_results = []
        if atomic_statements:
            for stmt in atomic_statements:
                stmt_results = self.indexer.search(
                    stmt['text'],
                    book_id=book_id,
                    top_k=max(3, top_k // len(atomic_statements))
                )
                atomic_results.extend(stmt_results)
        
        # Strategy 3: Entity-based retrieval
        entity_results = []
        if entities:
            for entity_type, entity_list in entities.items():
                for entity in entity_list:
                    ent_results = self.indexer.search(
                        entity,
                        book_id=book_id,
                        top_k=2
                    )
                    entity_results.extend(ent_results)
        
        # Strategy 4: Temporal context (if dates mentioned)
        temporal_results = []
        if self.memory and entities and entities.get('dates'):
            for date in entities['dates']:
                temporal_events = self.memory.get_temporal_context(date, window=3)
                for event in temporal_events:
                    # Fetch chunks related to temporal events
                    event_results = self.indexer.search(
                        event['event'],
                        book_id=book_id,
                        top_k=2
                    )
                    temporal_results.extend(event_results)
        
        # Combine and deduplicate results
        all_results = main_results + atomic_results + entity_results + temporal_results
        unique_results = self._deduplicate(all_results)
        
        # Rerank by relevance
        ranked_results = self._rerank(unique_results, claim)
        
        # Return top_k results
        final_results = ranked_results[:top_k]
        
        logger.success(f"Retrieved {len(final_results)} unique excerpts")
        return final_results
    
    def _deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate chunks"""
        seen_ids = set()
        unique = []
        
        for result in results:
            chunk_id = result['chunk_id']
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique.append(result)
        
        return unique
    
    def _rerank(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Rerank results by relevance
        
        Simple reranking based on:
        - Original relevance score
        - Text length (prefer substantial excerpts)
        - Keyword overlap
        """
        query_words = set(query.lower().split())
        
        for result in results:
            text_words = set(result['text'].lower().split())
            keyword_overlap = len(query_words & text_words) / len(query_words) if query_words else 0
            
            # Combined score
            result['rerank_score'] = (
                result['relevance_score'] * 0.6 +
                keyword_overlap * 0.3 +
                min(len(result['text']) / 1000, 1.0) * 0.1
            )
        
        # Sort by rerank score
        results.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        return results
    
    def retrieve_character_context(self, character_name: str, book_id: str = None) -> List[Dict[str, Any]]:
        """Retrieve all mentions of a specific character"""
        logger.debug(f"Retrieving context for character: {character_name}")
        
        results = self.indexer.search(
            character_name,
            book_id=book_id,
            top_k=20
        )
        
        return results
    
    def retrieve_event_context(self, event_description: str, book_id: str = None) -> List[Dict[str, Any]]:
        """Retrieve context around a specific event"""
        logger.debug(f"Retrieving context for event: {event_description}")
        
        results = self.indexer.search(
            event_description,
            book_id=book_id,
            top_k=15
        )
        
        return results