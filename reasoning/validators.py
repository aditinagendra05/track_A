import anthropic
from typing import List, Dict, Any
from loguru import logger
from config import config
import json

class NarrativeValidator:
    """Validate claims against canon using forensic analysis"""
    
    SYSTEM_PROMPT = """You are a canonical narrative forensic analyzer. Your sole purpose is to verify whether claims about fictional narratives align with, contradict, or cannot be determined from the source text. You operate with the rigor of a legal expert examining evidence, never introducing external knowledge or assumptions.

## Analysis Protocol

### Phase 1: Claim Decomposition
The claim has already been decomposed into atomic statements. You will verify each one.

### Phase 2: Evidence Grounding
For each atomic statement, perform forensic text matching:

**SUPPORTED** - Direct textual evidence exists:
- Quote exact phrases from excerpts
- Cite chunk_id
- Explain inferential steps if needed

**CONTRADICTED** - Text explicitly refutes the claim:
- Quote conflicting passages
- Explain the logical contradiction
- Note: Absence of evidence ≠ contradiction

**INSUFFICIENT** - Neither supported nor contradicted:
- State what specific evidence is missing
- Do NOT assume silence equals falsification

### Phase 3: Narrative Logic Verification

#### Timeline Consistency
- Do dates/sequences align across excerpts?
- Are there temporal impossibilities?

#### Causal Coherence
- Do claimed causes plausibly produce stated effects?
- Are there prerequisite events that must have occurred?

#### Character Knowledge & Traits
- Could the character plausibly know/do this given their background?
- Does behavior align with established personality?

#### World Rules
- Does the claim violate established rules of the fictional universe?

### Phase 4: Final Verdict

**SUPPORTED**: All atomic statements are supported OR reasonably inferable, no logic failures
**CONTRADICTED**: Any atomic statement has explicit contradictory evidence OR logic violations
**NOT_DECIDABLE**: Insufficient evidence for key statements OR ambiguous/conflicting evidence

## Output Format

Respond ONLY with valid JSON:

```json
{
  "verdict": "SUPPORTED | CONTRADICTED | NOT_DECIDABLE",
  "confidence": 0.0-1.0,
  "atomic_statements": [
    {
      "id": "A1",
      "text": "statement text",
      "verdict": "SUPPORTED | CONTRADICTED | INSUFFICIENT",
      "evidence": [
        {
          "chunk_id": "identifier",
          "quote": "exact text from source",
          "reasoning": "why this supports/contradicts"
        }
      ]
    }
  ],
  "narrative_logic_checks": {
    "timeline_consistent": true/false,
    "causally_coherent": true/false,
    "character_plausible": true/false,
    "world_rules_respected": true/false,
    "issues": ["specific problems if any"]
  },
  "rationale": "Concise evidence-grounded explanation",
  "critical_gaps": ["What information would change verdict"]
}
```

## Forbidden Actions
❌ Never use external knowledge about the books
❌ Never assume events not in excerpts
❌ Never treat missing information as contradiction
❌ Never insert personal interpretations

## Required Actions
✅ Always quote exact text when claiming support/contradiction
✅ Always cite chunk_id for evidence
✅ Always explain inferential leaps explicitly
✅ Always distinguish "not mentioned" from "contradicted"
✅ Always acknowledge limitations of excerpts

Analyze strictly from the provided text. Treat this as forensic analysis of story canon."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.models.anthropic_api_key)
        self.model = config.models.llm_model
        logger.info("NarrativeValidator initialized")
    
    def validate(
        self,
        claim: str,
        atomic_statements: List[Dict[str, str]],
        excerpts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate claim against excerpts using forensic analysis
        
        Args:
            claim: Original claim
            atomic_statements: Decomposed atomic statements
            excerpts: Retrieved text excerpts with relevance scores
            
        Returns:
            Validation result with verdict, confidence, and rationale
        """
        logger.info("Validating claim against canon")
        
        # Format excerpts for the prompt
        formatted_excerpts = self._format_excerpts(excerpts)
        
        # Format atomic statements
        formatted_statements = self._format_atomic_statements(atomic_statements)
        
        # Build user message
        user_message = f"""**Original Claim:**
{claim}

**Atomic Statements to Verify:**
{formatted_statements}

**Retrieved Excerpts from Source Text:**
{formatted_excerpts}

Analyze each atomic statement against the excerpts and provide your forensic verdict."""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0,
                system=self.SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": user_message
                }]
            )
            
            # Parse JSON response
            content = response.content[0].text
            
            # Clean markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            
            logger.success(f"Validation complete: {result['verdict']}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse validation response: {e}")
            logger.debug(f"Raw response: {content}")
            
            # Fallback response
            return {
                "verdict": "NOT_DECIDABLE",
                "confidence": 0.0,
                "atomic_statements": [],
                "narrative_logic_checks": {
                    "timeline_consistent": None,
                    "causally_coherent": None,
                    "character_plausible": None,
                    "world_rules_respected": None,
                    "issues": ["Failed to parse response"]
                },
                "rationale": "System error during validation",
                "critical_gaps": ["Unable to complete analysis"]
            }
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return {
                "verdict": "NOT_DECIDABLE",
                "confidence": 0.0,
                "rationale": f"Error: {str(e)}",
                "critical_gaps": []
            }
    
    @staticmethod
    def _format_excerpts(excerpts: List[Dict[str, Any]]) -> str:
        """Format excerpts for prompt"""
        formatted = []
        for i, excerpt in enumerate(excerpts, 1):
            formatted.append(f"""
[Excerpt {i}]
Chunk ID: {excerpt['chunk_id']}
Book: {excerpt.get('title', excerpt.get('book_id', 'Unknown'))}
Relevance: {excerpt['relevance_score']:.2f}
Text: {excerpt['text']}
---""")
        return "\n".join(formatted)
    
    @staticmethod
    def _format_atomic_statements(statements: List[Dict[str, str]]) -> str:
        """Format atomic statements for prompt"""
        formatted = []
        for stmt in statements:
            formatted.append(f"{stmt['id']}: {stmt['text']}")
        return "\n".join(formatted)