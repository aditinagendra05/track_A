import anthropic
from typing import List, Dict, Any
from loguru import logger
from config import config
import json

class ClaimExtractor:
    """Decompose claims into atomic factual statements"""
    
    DECOMPOSITION_PROMPT = """You are a precise claim analyzer. Decompose the given claim into atomic factual statements that can be independently verified.

Each atomic statement should:
1. Be a single, verifiable fact
2. Contain no conjunctions (and, or, but)
3. Be self-contained and clear
4. Be testable against source text

Example:
Claim: "Edmond Dantès escaped prison in 1829 using a body bag"

Atomic Statements:
A1: Edmond Dantès was imprisoned
A2: Edmond Dantès escaped from prison
A3: The escape occurred in 1829
A4: The escape method involved a body bag

Now decompose this claim:

Claim: {claim}

Respond ONLY with a JSON object in this format:
{{
  "atomic_statements": [
    {{"id": "A1", "text": "statement text"}},
    {{"id": "A2", "text": "statement text"}}
  ]
}}"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=config.models.anthropic_api_key)
        self.model = config.models.llm_model
        logger.info("ClaimExtractor initialized")
    
    def extract(self, claim: str) -> List[Dict[str, str]]:
        """
        Decompose claim into atomic statements
        
        Args:
            claim: The narrative claim to decompose
            
        Returns:
            List of dicts with 'id' and 'text' for each atomic statement
        """
        logger.info(f"Decomposing claim: {claim[:100]}...")
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": self.DECOMPOSITION_PROMPT.format(claim=claim)
                }]
            )
            
            # Parse JSON response
            content = response.content[0].text
            
            # Clean markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            atomic_statements = result.get('atomic_statements', [])
            
            logger.success(f"Extracted {len(atomic_statements)} atomic statements")
            return atomic_statements
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {content}")
            # Fallback: treat entire claim as single statement
            return [{"id": "A1", "text": claim}]
            
        except Exception as e:
            logger.error(f"Error in claim extraction: {e}")
            return [{"id": "A1", "text": claim}]
    
    def extract_entities(self, claim: str) -> Dict[str, List[str]]:
        """
        Extract key entities from claim for targeted retrieval
        
        Returns:
            Dict with entity types: {characters, locations, dates, events}
        """
        logger.debug("Extracting entities from claim")
        
        entity_prompt = f"""Extract key entities from this narrative claim:

Claim: {claim}

Identify:
- Characters (people names)
- Locations (places)
- Dates (temporal references)
- Events (actions, occurrences)

Respond ONLY with JSON:
{{
  "characters": ["name1", "name2"],
  "locations": ["place1"],
  "dates": ["1829", "spring"],
  "events": ["escaped", "married"]
}}"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0,
                messages=[{"role": "user", "content": entity_prompt}]
            )
            
            content = response.content[0].text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            entities = json.loads(content)
            logger.debug(f"Extracted entities: {entities}")
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {
                "characters": [],
                "locations": [],
                "dates": [],
                "events": []
            }