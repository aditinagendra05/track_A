from typing import Dict, Any, List
from loguru import logger
import numpy as np

class ConfidenceScorer:
    """Calculate confidence scores for verdicts"""
    
    def __init__(self):
        logger.info("ConfidenceScorer initialized")
    
    def calculate_confidence(
        self,
        verdict: str,
        atomic_verdicts: List[str],
        evidence_scores: List[float],
        narrative_checks: Dict[str, Any]
    ) -> float:
        """
        Calculate overall confidence in the verdict
        
        Args:
            verdict: Final verdict (SUPPORTED/CONTRADICTED/NOT_DECIDABLE)
            atomic_verdicts: Verdicts for each atomic statement
            evidence_scores: Relevance scores of evidence used
            narrative_checks: Results from narrative logic checks
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        logger.debug(f"Calculating confidence for verdict: {verdict}")
        
        # Base confidence from atomic statements
        atomic_confidence = self._score_atomic_consistency(atomic_verdicts, verdict)
        
        # Evidence quality score
        evidence_confidence = self._score_evidence_quality(evidence_scores)
        
        # Narrative logic score
        logic_confidence = self._score_narrative_logic(narrative_checks)
        
        # Weighted combination
        weights = {
            'atomic': 0.5,
            'evidence': 0.3,
            'logic': 0.2
        }
        
        overall_confidence = (
            weights['atomic'] * atomic_confidence +
            weights['evidence'] * evidence_confidence +
            weights['logic'] * logic_confidence
        )
        
        # Apply verdict-specific adjustments
        overall_confidence = self._adjust_for_verdict(
            overall_confidence,
            verdict,
            atomic_verdicts
        )
        
        logger.debug(f"Confidence score: {overall_confidence:.3f}")
        return round(overall_confidence, 3)
    
    def _score_atomic_consistency(
        self,
        atomic_verdicts: List[str],
        final_verdict: str
    ) -> float:
        """
        Score based on atomic statement consistency
        
        High score when:
        - All atomic verdicts align with final verdict
        - No contradictions among atomic statements
        """
        if not atomic_verdicts:
            return 0.5  # Neutral
        
        # Map verdicts to numeric scores
        verdict_map = {
            'SUPPORTED': 1.0,
            'INSUFFICIENT': 0.5,
            'CONTRADICTED': 0.0
        }
        
        atomic_scores = [
            verdict_map.get(v, 0.5) for v in atomic_verdicts
        ]
        
        # Calculate consistency
        if final_verdict == 'SUPPORTED':
            # All should be SUPPORTED or INSUFFICIENT
            consistency = np.mean([s >= 0.5 for s in atomic_scores])
        elif final_verdict == 'CONTRADICTED':
            # At least one CONTRADICTED
            consistency = 1.0 if any(s == 0.0 for s in atomic_scores) else 0.3
        else:  # NOT_DECIDABLE
            # Mix of INSUFFICIENT
            consistency = np.mean([s == 0.5 for s in atomic_scores])
        
        return consistency
    
    def _score_evidence_quality(self, evidence_scores: List[float]) -> float:
        """
        Score based on quality of retrieved evidence
        
        High score when:
        - Evidence relevance scores are high
        - Multiple pieces of evidence available
        - Evidence scores are consistent
        """
        if not evidence_scores:
            return 0.0
        
        # Average relevance
        avg_relevance = np.mean(evidence_scores)
        
        # Consistency of evidence (low variance is good)
        if len(evidence_scores) > 1:
            consistency = 1.0 - min(np.std(evidence_scores), 0.3) / 0.3
        else:
            consistency = 0.8  # Single piece of evidence
        
        # Quantity bonus (more evidence is better, up to a point)
        quantity_bonus = min(len(evidence_scores) / 10, 0.2)
        
        quality_score = (
            avg_relevance * 0.6 +
            consistency * 0.3 +
            quantity_bonus * 0.1
        )
        
        return quality_score
    
    def _score_narrative_logic(self, narrative_checks: Dict[str, Any]) -> float:
        """
        Score based on narrative logic consistency
        
        High score when all logic checks pass
        """
        if not narrative_checks:
            return 0.5
        
        checks = [
            narrative_checks.get('timeline_consistent', None),
            narrative_checks.get('causally_coherent', None),
            narrative_checks.get('character_plausible', None),
            narrative_checks.get('world_rules_respected', None)
        ]
        
        # Filter out None values
        valid_checks = [c for c in checks if c is not None]
        
        if not valid_checks:
            return 0.5
        
        # Calculate percentage passing
        pass_rate = sum(valid_checks) / len(valid_checks)
        
        # Penalize if issues exist
        issues = narrative_checks.get('issues', [])
        issue_penalty = min(len(issues) * 0.1, 0.3)
        
        logic_score = max(0.0, pass_rate - issue_penalty)
        
        return logic_score
    
    def _adjust_for_verdict(
        self,
        base_confidence: float,
        verdict: str,
        atomic_verdicts: List[str]
    ) -> float:
        """
        Apply verdict-specific confidence adjustments
        
        Conservative principle: Lower confidence for edge cases
        """
        # CONTRADICTED verdicts should have high confidence
        # (we found explicit contradiction)
        if verdict == 'CONTRADICTED':
            # Boost confidence if we have strong contradiction
            if 'CONTRADICTED' in atomic_verdicts:
                return min(base_confidence + 0.1, 1.0)
        
        # NOT_DECIDABLE should have moderate confidence
        # (we're uncertain, which is appropriate)
        elif verdict == 'NOT_DECIDABLE':
            # Cap confidence for uncertain verdicts
            return min(base_confidence, 0.7)
        
        # SUPPORTED verdicts need strong evidence
        elif verdict == 'SUPPORTED':
            # Require high base confidence
            if base_confidence < 0.6:
                return base_confidence * 0.8  # Penalize weak support
        
        return base_confidence
    
    def score_explanation_quality(self, rationale: str) -> float:
        """
        Score the quality of the explanation/rationale
        
        Good explanations:
        - Cite specific evidence
        - Are appropriately length
        - Use precise language
        """
        if not rationale:
            return 0.0
        
        # Length check (not too short, not too long)
        words = rationale.split()
        length_score = min(len(words) / 100, 1.0) if len(words) < 200 else 0.8
        
        # Citation check (looks for chunk references)
        has_citations = 'chunk' in rationale.lower() or 'excerpt' in rationale.lower()
        citation_score = 1.0 if has_citations else 0.5
        
        # Precision indicators
        precision_words = ['specifically', 'explicitly', 'states', 'mentions', 'indicates']
        precision_score = min(
            sum(word in rationale.lower() for word in precision_words) / len(precision_words),
            1.0
        )
        
        explanation_quality = (
            length_score * 0.3 +
            citation_score * 0.4 +
            precision_score * 0.3
        )
        
        return explanation_quality