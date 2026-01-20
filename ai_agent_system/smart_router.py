"""
Smart Intent Router - Hybrid Approach (Keyword + OpenAI)
Cost-Optimized: Uses keyword matching for 90% of queries, OpenAI for 10%
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav

STRATEGY:
- Fast keyword matching for obvious queries (free, instant)
- OpenAI for complex/ambiguous queries (smart, ~200ms, ~$0.00015)
- Caching to avoid repeated API calls
- Graceful fallback if OpenAI unavailable
"""
import re
import json
import os
from typing import Dict, Optional, List
from openai import OpenAI

# Import base router
from router import IntentRouter, MCPService


class SmartRouter:
    """
    Hybrid Smart Router
    - 90% of queries: Free keyword matching (fast, accurate for obvious queries)
    - 10% of queries: OpenAI intelligence (handles complex/ambiguous queries)
    - Caching: Avoids repeated API calls for similar queries
    """
    
    def __init__(self, use_openai: bool = True, confidence_threshold: float = 0.75):
        """
        Initialize Smart Router
        
        Args:
            use_openai: Enable OpenAI for complex queries (default: True)
            confidence_threshold: Minimum confidence to skip OpenAI (0.75 = 75%)
        """
        # Initialize base keyword router
        self.keyword_router = IntentRouter()
        
        # Configuration
        self.use_openai = use_openai
        self.confidence_threshold = confidence_threshold
        
        # OpenAI setup (optional)
        self.openai_client = None
        if use_openai:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    self.openai_client = OpenAI(api_key=api_key)
                    # Model configurable via env
                    self.model = os.getenv("SMART_ROUTER_MODEL", "gpt-4o-mini")
                    print("🧠 Smart Router: OpenAI enabled")
                except Exception as e:
                    print(f"⚠️  Smart Router: OpenAI init failed: {e}")
                    print("   Falling back to keyword-only mode")
                    self.use_openai = False
                    self.openai_client = None
            else:
                print("⚠️  Smart Router: OPENAI_API_KEY not found")
                print("   Using keyword-only mode")
                self.use_openai = False
        else:
            print("🧠 Smart Router: OpenAI disabled (keyword-only mode)")
        
        # Cache for router decisions (configurable via env)
        self._decision_cache = {}
        self.max_cache_size = int(os.getenv("SMART_ROUTER_CACHE_SIZE", "200"))
        
        # Statistics
        self.stats = {
            'total_queries': 0,
            'keyword_routes': 0,
            'openai_routes': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Load ambiguous patterns from env or use smart defaults (no hardcoding)
        ambiguous_patterns_env = os.getenv("SMART_ROUTER_AMBIGUOUS_PATTERNS")
        if ambiguous_patterns_env:
            # Load patterns from env (comma-separated regex patterns)
            self.ambiguous_patterns = [p.strip() for p in ambiguous_patterns_env.split(',')]
        else:
            # Smart default patterns (semantic-based, not hardcoded rules)
            self.ambiguous_patterns = self._generate_ambiguous_patterns()
    
    def _generate_ambiguous_patterns(self) -> List[str]:
        """Generate ambiguous patterns dynamically (semantic approach)"""
        # Complex questions pattern
        question_words = r'\b(what|which|how|why|when|where)\b.*\b(is|are|was|were|do|does|did)\b'
        
        # Descriptive queries
        descriptive = r'\b(show|tell|explain|describe)\b.*\b(about|regarding|concerning)\b'
        
        # Conditional/negation (dynamic detection)
        conditional = r'\b(find|search|look)\b.*\b(but|however|although|not|except)\b'
        logical_ops = r'\b(both|either|neither)\b.*\b(and|or)\b'
        
        # Comparison (semantic pattern)
        comparison = r'\b(compare|difference|similar|different|versus|vs)\b'
        
        # Ambiguous service indicators (context-dependent)
        uncertain = r'\b(should|would|could)\b.*\b(search|find|get|show)\b'
        
        # Complex relationships (semantic pattern)
        relationships = r'\b(all|everything|anything)\b.*\b(about|regarding|related to)\b'
        
        return [
            question_words,
            descriptive,
            conditional,
            logical_ops,
            comparison,
            uncertain,
            relationships
        ]
    
    def route(self, query: str) -> Dict:
        """
        Smart routing with hybrid approach
        
        Flow:
        1. Check cache (instant if found)
        2. Try keyword matching (fast, free)
        3. If confidence low OR query ambiguous → Use OpenAI
        4. Cache result for future use
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary with routing information (same format as IntentRouter)
        """
        self.stats['total_queries'] += 1
        
        query_normalized = query.lower().strip()
        
        # Step 1: Check cache first
        cache_key = self._get_cache_key(query_normalized)
        if cache_key in self._decision_cache:
            self.stats['cache_hits'] += 1
            result = self._decision_cache[cache_key].copy()
            result['original_query'] = query  # Preserve original
            result['method'] = 'cached'
            return result
        
        self.stats['cache_misses'] += 1
        
        # Step 2: Try keyword matching first (fast, free)
        keyword_result = self.keyword_router.route(query)
        keyword_confidence = keyword_result.get('confidence', 0.0)
        keyword_service = keyword_result.get('primary_service')
        
        self.stats['keyword_routes'] += 1
        
        # Step 3: Decide if we need OpenAI
        needs_openai = False
        
        if self.use_openai and self.openai_client:
            # Use OpenAI if:
            # 1. Confidence is below threshold
            # 2. Query matches ambiguous patterns
            # 3. Multiple services have similar scores (tied scores)
            # 4. Query is very long/complex
            
            is_low_confidence = keyword_confidence < self.confidence_threshold
            
            is_ambiguous = any(re.search(pattern, query_normalized, re.IGNORECASE) 
                             for pattern in self.ambiguous_patterns)
            
            # Check if scores are tied (multiple services with similar scores)
            query_lower = query.lower()
            scores = {
                MCPService.SEARCH: self.keyword_router._calculate_score(query_lower, MCPService.SEARCH),
                MCPService.DRIVE: self.keyword_router._calculate_score(query_lower, MCPService.DRIVE),
                MCPService.DATABASE: self.keyword_router._calculate_score(query_lower, MCPService.DATABASE),
                MCPService.RAG_PDF: self.keyword_router._calculate_score(query_lower, MCPService.RAG_PDF),
            }
            # Use configurable tie threshold
            tie_threshold = float(os.getenv("SMART_ROUTER_TIE_THRESHOLD", "3.0"))
            top_scores = sorted(scores.values(), reverse=True)
            is_tied = len(top_scores) > 1 and top_scores[0] > 0 and (top_scores[0] - top_scores[1]) < tie_threshold
            
            # Use configurable complexity threshold
            complex_word_count = int(os.getenv("SMART_ROUTER_COMPLEX_WORDS", "12"))
            is_complex = len(query.split()) > complex_word_count or '?' in query
            
            # Decision logic
            needs_openai = is_low_confidence or (is_ambiguous and is_complex) or (is_tied and is_complex)
        
        # Step 4: Use OpenAI if needed
        if needs_openai:
            openai_result = self._route_with_openai(query)
            if openai_result:
                # Cache the result
                self._cache_result(cache_key, openai_result)
                self.stats['openai_routes'] += 1
                self.stats['keyword_routes'] -= 1  # Adjust count
                openai_result['method'] = 'openai'
                return openai_result
        
        # Step 5: Use keyword result (good enough)
        self._cache_result(cache_key, keyword_result)
        keyword_result['method'] = 'keyword'
        return keyword_result
    
    def _route_with_openai(self, query: str) -> Optional[Dict]:
        """
        Use OpenAI to determine the best service for a complex query
        
        Args:
            query: User's query
            
        Returns:
            Routing result or None if OpenAI fails
        """
        if not self.openai_client:
            return None
        
        system_prompt = """You are an intelligent routing system that determines which service should handle a user's query.

Available services:
1. SEARCH - For web searches, online information, current news, internet searches, "find online", "google"
2. DRIVE - For Google Drive operations (upload, download, list files in Drive)
3. DATABASE - For notes, saved documents, creating/editing notes, "in my notes", "my saved documents"
4. RAG_PDF - For PDF documents, uploaded files, questions about PDFs, summaries of uploaded documents

Analyze the query carefully:
- "search online", "find on internet" → SEARCH
- "in my notes", "my saved" → DATABASE
- "my PDF", "uploaded document" → RAG_PDF
- "Google Drive", "upload to drive" → DRIVE

Return JSON in this exact format:
{
    "primary_service": "database",
    "intent": "search_documents",
    "confidence": 0.95,
    "reasoning": "User wants to search their saved notes"
}

Service names must be one of: "search", "drive", "database", "rag_pdf", "general"
Be precise and confident."""

        user_prompt = f"""Route this query to the appropriate service:

Query: "{query}"

Return JSON with primary_service, intent, confidence (0.0-1.0), and reasoning."""

        try:
            # OpenAI parameters configurable via env (no hardcoding)
            temperature = float(os.getenv("SMART_ROUTER_TEMPERATURE", "0.1"))
            max_tokens = int(os.getenv("SMART_ROUTER_MAX_TOKENS", "200"))
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            
            result_json = json.loads(response.choices[0].message.content)
            
            # Convert to standard format
            service_name = result_json.get("primary_service", "general").lower()
            service_map = {
                "search": MCPService.SEARCH,
                "drive": MCPService.DRIVE,
                "database": MCPService.DATABASE,
                "rag_pdf": MCPService.RAG_PDF,
                "general": MCPService.GENERAL
            }
            
            primary_service = service_map.get(service_name, MCPService.GENERAL)
            confidence = float(result_json.get("confidence", 0.8))
            intent = result_json.get("intent", "general_conversation")
            reasoning = result_json.get("reasoning", "")
            
            # Use keyword router's parameter extraction
            params = self.keyword_router._extract_parameters(query, primary_service, intent)
            
            result = {
                'primary_service': primary_service,
                'secondary_services': [],
                'intent': intent,
                'parameters': params,
                'confidence': confidence,
                'original_query': query,
                'reasoning': reasoning
            }
            
            print(f"🧠 OpenAI Router: {primary_service.value} (confidence: {confidence:.2f})")
            if reasoning:
                print(f"   Reasoning: {reasoning}")
            
            return result
        
        except json.JSONDecodeError as e:
            print(f"⚠️  OpenAI router: Invalid JSON response: {e}")
            return None
        except Exception as e:
            print(f"⚠️  OpenAI router failed: {e}")
            return None
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        # Normalize query for caching (remove extra spaces, lowercase)
        normalized = ' '.join(query.lower().split())
        # Limit length for cache efficiency
        return normalized[:150]
    
    def _cache_result(self, cache_key: str, result: Dict):
        """Cache routing result"""
        # Implement LRU-like behavior: remove oldest if cache full
        if len(self._decision_cache) >= self.max_cache_size:
            # Remove first entry (oldest)
            first_key = next(iter(self._decision_cache))
            del self._decision_cache[first_key]
        
        self._decision_cache[cache_key] = result.copy()
    
    def get_stats(self) -> Dict:
        """Get router statistics"""
        total = self.stats['total_queries']
        if total == 0:
            return self.stats.copy()
        
        cache_hit_rate = (self.stats['cache_hits'] / total) * 100
        openai_usage_rate = (self.stats['openai_routes'] / total) * 100
        keyword_usage_rate = (self.stats['keyword_routes'] / total) * 100
        
        stats = self.stats.copy()
        stats['cache_hit_rate'] = f"{cache_hit_rate:.1f}%"
        stats['openai_usage_rate'] = f"{openai_usage_rate:.1f}%"
        stats['keyword_usage_rate'] = f"{keyword_usage_rate:.1f}%"
        stats['openai_enabled'] = self.use_openai and self.openai_client is not None
        stats['cache_size'] = len(self._decision_cache)
        
        return stats
    
    def clear_cache(self):
        """Clear the decision cache"""
        self._decision_cache.clear()
        self.stats['cache_hits'] = 0
        self.stats['cache_misses'] = 0
        print("✅ Smart Router cache cleared")


# Factory function for easy integration
def create_router(use_openai: bool = None) -> SmartRouter:
    """
    Create a Smart Router instance
    
    Args:
        use_openai: Enable OpenAI (default: True, can be overridden by env var SMART_ROUTER_OPENAI)
        
    Returns:
        SmartRouter instance
    """
    # Check environment variable first
    env_openai = os.getenv("SMART_ROUTER_OPENAI", "true").lower()
    if use_openai is None:
        use_openai = env_openai in ('true', '1', 'yes', 'on')
    
    return SmartRouter(use_openai=use_openai)


if __name__ == "__main__":
    # Test the smart router
    print("\n" + "="*60)
    print("🧪 Testing Smart Router (Hybrid)")
    print("="*60 + "\n")
    
    router = create_router(use_openai=True)
    
    test_queries = [
        # Obvious queries (should use keyword - free)
        "List all my PDFs",
        "Search for Python tutorials online",
        "Create a note about the meeting",
        "Upload this file to Google Drive",
        
        # Ambiguous queries (should use OpenAI - smart)
        "What information do I have about both AI and finance?",
        "Show me documents that mention John but are not about projects",
        "Compare the findings in my PDFs with what I can find online",
        
        # Complex queries (should use OpenAI)
        "I need to find information about machine learning, but I'm not sure if it's in my notes or if I should search online. Can you help?",
    ]
    
    for query in test_queries:
        print(f"🔍 Query: {query}")
        result = router.route(query)
        print(f"   ✅ Service: {result['primary_service'].value}")
        print(f"   Method: {result.get('method', 'unknown')}")
        print(f"   Confidence: {result['confidence']:.2%}")
        if 'reasoning' in result and result['reasoning']:
            print(f"   Reasoning: {result['reasoning']}")
        print()
    
    # Show stats
    stats = router.get_stats()
    print("="*60)
    print("📊 Smart Router Statistics")
    print("="*60)
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print()
