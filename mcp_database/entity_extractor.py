"""
Entity Extractor - Hybrid NER + GPT-4o-mini Approach
Extracts entities using NER, relationships using GPT-4o-mini
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""
import spacy
from openai import OpenAI
from typing import List, Dict, Optional
import json
import os
import re


class EntityExtractor:
    """Hybrid entity and relationship extractor using NER + GPT-4o-mini"""
    
    def __init__(self):
        """Initialize Entity Extractor with NER and GPT-4o-mini"""
        # Initialize NER model (spaCy)
        print("📦 Loading spaCy NER model...")
        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy NER model loaded")
        except OSError:
            print("⚠️  spaCy model not found. Please install: python -m spacy download en_core_web_sm")
            print("   Falling back to basic tokenization...")
            self.nlp = None
        
        # Initialize GPT-4o-mini
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.gpt_client = OpenAI(api_key=api_key)
        self.gpt_model = "gpt-4o-mini"
        
        print("✅ Entity Extractor initialized (NER + GPT-4o-mini)")
    
    def extract_entities_ner(self, content: str) -> Dict:
        """
        Step 1: Fast entity detection using NER
        Returns: entities with types
        
        Args:
            content: Text content to extract entities from
            
        Returns:
            Dictionary with categorized entities
        """
        if not self.nlp:
            # Fallback to basic extraction if spaCy not available
            return self._basic_entity_extraction(content)
        
        doc = self.nlp(content)
        
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'other': []
        }
        
        for ent in doc.ents:
            entity_data = {
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': 0.9  # NER confidence
            }
            
            if ent.label_ == 'PERSON':
                entities['persons'].append(entity_data)
            elif ent.label_ == 'ORG':
                entities['organizations'].append(entity_data)
            elif ent.label_ == 'GPE' or ent.label_ == 'LOC':
                entities['locations'].append(entity_data)
            elif ent.label_ == 'DATE':
                entities['dates'].append(entity_data)
            else:
                entities['other'].append(entity_data)
        
        return entities
    
    def _basic_entity_extraction(self, content: str) -> Dict:
        """Basic entity extraction fallback if spaCy not available"""
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': [],
            'other': []
        }
        
        # Basic pattern matching (very simple fallback)
        # This is not as good as NER, but works if spaCy unavailable
        words = re.findall(r'\b[A-Z][a-z]+\b', content)
        
        return entities
    
    def extract_relationships_gpt(self, content: str, entities: Dict) -> List[Dict]:
        """
        Step 2: Relationship extraction using GPT-4o-mini
        Uses NER entities as hints for better accuracy
        
        Args:
            content: Text content to extract relationships from
            entities: Entities found by NER
            
        Returns:
            List of relationships with source, target, and type
        """
        # Prepare entity list for GPT
        entity_list = []
        for category, items in entities.items():
            for item in items[:10]:  # Limit to avoid token waste
                entity_list.append(f"{item['text']} ({item['label']})")
        
        entity_context = ", ".join(entity_list[:20]) if entity_list else "None found"
        
        # Limit content to manage tokens (keep first 4000 chars)
        content_snippet = content[:4000] if len(content) > 4000 else content
        
        system_prompt = """You are an expert at extracting relationships from text.
Your task is to identify relationships between entities mentioned in the text.

Return a JSON object with a "relationships" array in this exact format:
{
    "relationships": [
        {
            "source_entity": "John Smith",
            "source_type": "Person",
            "relationship": "WORKS_ON",
            "target_entity": "AI Project",
            "target_type": "Project",
            "confidence": 0.9,
            "context": "brief context from text"
        }
    ]
}

Relationship types to look for:
- WORKS_ON: Person works on Project/Task
- MENTIONS: Document mentions Topic/Entity
- AUTHORED_BY: Document authored by Person
- RELATED_TO: Entity related to another Entity
- CONTAINS: Document/Project contains Topic
- COLLABORATES_WITH: Person collaborates with Person
- LOCATED_IN: Entity located in Location
- OCCURRED_ON: Event occurred on Date
- MANAGES: Person manages Project/Team
- PART_OF: Entity is part of Organization/Project

Only extract relationships that are EXPLICITLY stated or STRONGLY implied.
Be conservative with confidence scores (0.7-1.0 for explicit, 0.5-0.7 for implied).
Return empty array if no clear relationships found."""

        user_prompt = f"""Extract relationships from this text:

TEXT:
{content_snippet}

ENTITIES FOUND (for reference):
{entity_context}

Extract all relationships between entities. Return JSON object with "relationships" array only."""

        try:
            response = self.gpt_client.chat.completions.create(
                model=self.gpt_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Low temperature for consistency
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Handle response format
            if isinstance(result, dict) and 'relationships' in result:
                return result['relationships']
            elif isinstance(result, list):
                return result
            else:
                return []
        
        except json.JSONDecodeError as e:
            print(f"⚠️  GPT returned invalid JSON: {e}")
            return []
        except Exception as e:
            print(f"⚠️  GPT relationship extraction failed: {e}")
            return []
    
    def extract_all(self, content: str, doc_id: str) -> Dict:
        """
        Complete extraction pipeline: NER → GPT → Combined result
        
        Args:
            content: Document content
            doc_id: Document ID
            
        Returns:
            Dictionary with entities and relationships
        """
        print(f"\n{'='*60}")
        print(f"🔍 Extracting entities and relationships")
        print(f"   Document ID: {doc_id}")
        print(f"   Content length: {len(content)} chars")
        print(f"{'='*60}\n")
        
        # Step 1: NER (fast)
        print("📌 Step 1: NER entity detection...")
        entities = self.extract_entities_ner(content)
        total_entities = sum(len(v) for v in entities.values())
        print(f"   ✅ Found {total_entities} entities")
        
        # Step 2: GPT relationships (slower, but accurate)
        # Only if we found entities (cost optimization)
        relationships = []
        if total_entities > 0:
            print("🔗 Step 2: GPT relationship extraction...")
            relationships = self.extract_relationships_gpt(content, entities)
            print(f"   ✅ Found {len(relationships)} relationships")
        else:
            print("   ⏭️  Skipping GPT (no entities found)")
        
        return {
            'doc_id': doc_id,
            'entities': entities,
            'relationships': relationships,
            'extraction_method': 'hybrid_ner_gpt',
            'total_entities': total_entities,
            'total_relationships': len(relationships)
        }
    
    def extract_from_chunk(self, chunk_content: str, chunk_id: str) -> Dict:
        """
        Extract entities and relationships from a text chunk
        Useful for PDF chunks or document sections
        
        Args:
            chunk_content: Chunk text content
            chunk_id: Chunk identifier
            
        Returns:
            Dictionary with entities and relationships
        """
        return self.extract_all(chunk_content, chunk_id)
