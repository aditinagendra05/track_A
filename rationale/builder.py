from typing import Dict, Any, List
from loguru import logger
import json
from datetime import datetime
from pathlib import Path
from config import config

class RationaleBuilder:
    """Build comprehensive dossiers with evidence and reasoning"""
    
    def __init__(self):
        self.dossiers_path = config.paths.dossiers
        logger.info("RationaleBuilder initialized")
    
    def build_dossier(
        self,
        case_id: str,
        claim: str,
        book_id: str,
        atomic_statements: List[Dict[str, str]],
        validation_result: Dict[str, Any],
        excerpts: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Build complete verification dossier
        
        Args:
            case_id: Unique case identifier
            claim: Original claim
            book_id: Source book identifier
            atomic_statements: Decomposed statements
            validation_result: Result from validator
            excerpts: Retrieved evidence excerpts
            metadata: Additional metadata
            
        Returns:
            Complete dossier dict
        """
        logger.info(f"Building dossier for case: {case_id}")
        
        dossier = {
            'case_id': case_id,
            'timestamp': datetime.now().isoformat(),
            'claim': {
                'original': claim,
                'book_id': book_id,
                'atomic_statements': atomic_statements
            },
            'verdict': {
                'decision': validation_result.get('verdict', 'NOT_DECIDABLE'),
                'confidence': validation_result.get('confidence', 0.0),
                'rationale': validation_result.get('rationale', '')
            },
            'evidence': {
                'excerpts': self._format_excerpts_for_dossier(excerpts),
                'total_retrieved': len(excerpts),
                'avg_relevance': self._calculate_avg_relevance(excerpts)
            },
            'analysis': {
                'atomic_verdicts': validation_result.get('atomic_statements', []),
                'narrative_logic': validation_result.get('narrative_logic_checks', {}),
                'critical_gaps': validation_result.get('critical_gaps', [])
            },
            'metadata': metadata or {}
        }
        
        logger.success(f"Dossier built for {case_id}")
        return dossier
    
    def save_dossier(self, dossier: Dict[str, Any]) -> Path:
        """
        Save dossier to JSON file
        
        Args:
            dossier: Complete dossier dict
            
        Returns:
            Path to saved file
        """
        case_id = dossier['case_id']
        filepath = self.dossiers_path / f"{case_id}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dossier, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Dossier saved: {filepath}")
        return filepath
    
    def build_prediction(
        self,
        case_id: str,
        verdict: str,
        confidence: float
    ) -> Dict[str, Any]:
        """
        Build simple prediction for submission
        
        Args:
            case_id: Case identifier
            verdict: Final verdict
            confidence: Confidence score
            
        Returns:
            Prediction dict
        """
        return {
            'id': case_id,
            'prediction': verdict,
            'confidence': confidence
        }
    
    def save_predictions(
        self,
        predictions: List[Dict[str, Any]],
        filename: str = 'predictions.json'
    ) -> Path:
        """
        Save all predictions to file
        
        Args:
            predictions: List of prediction dicts
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        filepath = config.paths.outputs / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(predictions, f, indent=2)
        
        logger.success(f"Saved {len(predictions)} predictions to {filepath}")
        return filepath
    
    def generate_summary_report(
        self,
        dossiers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics across all dossiers
        
        Args:
            dossiers: List of dossier dicts
            
        Returns:
            Summary report
        """
        logger.info("Generating summary report")
        
        if not dossiers:
            return {'message': 'No dossiers to summarize'}
        
        verdicts = [d['verdict']['decision'] for d in dossiers]
        confidences = [d['verdict']['confidence'] for d in dossiers]
        
        summary = {
            'total_cases': len(dossiers),
            'verdict_distribution': {
                'SUPPORTED': verdicts.count('SUPPORTED'),
                'CONTRADICTED': verdicts.count('CONTRADICTED'),
                'NOT_DECIDABLE': verdicts.count('NOT_DECIDABLE')
            },
            'confidence_stats': {
                'mean': sum(confidences) / len(confidences),
                'min': min(confidences),
                'max': max(confidences),
                'median': sorted(confidences)[len(confidences) // 2]
            },
            'avg_excerpts_per_case': sum(
                d['evidence']['total_retrieved'] for d in dossiers
            ) / len(dossiers)
        }
        
        logger.success("Summary report generated")
        return summary
    
    @staticmethod
    def _format_excerpts_for_dossier(
        excerpts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format excerpts for dossier output"""
        formatted = []
        for excerpt in excerpts:
            formatted.append({
                'chunk_id': excerpt['chunk_id'],
                'book_id': excerpt.get('book_id', ''),
                'text': excerpt['text'],
                'relevance_score': excerpt['relevance_score']
            })
        return formatted
    
    @staticmethod
    def _calculate_avg_relevance(excerpts: List[Dict[str, Any]]) -> float:
        """Calculate average relevance score"""
        if not excerpts:
            return 0.0
        scores = [e['relevance_score'] for e in excerpts]
        return sum(scores) / len(scores)
    
    def load_dossier(self, case_id: str) -> Dict[str, Any]:
        """Load existing dossier from file"""
        filepath = self.dossiers_path / f"{case_id}.json"
        
        if not filepath.exists():
            logger.error(f"Dossier not found: {filepath}")
            return {}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            dossier = json.load(f)
        
        logger.info(f"Loaded dossier: {case_id}")
        return dossier