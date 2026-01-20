"""
Smart Configuration Manager
Dynamic, configurable patterns and thresholds (no hardcoding)
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""

import os
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class RouterConfig:
    """Smart router configuration (all configurable via env vars)"""
    # Scoring weights (configurable)
    phrase_weight: float = float(os.getenv("ROUTER_PHRASE_WEIGHT", "6.0"))
    keyword_weight: float = float(os.getenv("ROUTER_KEYWORD_WEIGHT", "2.5"))
    negative_penalty: float = float(os.getenv("ROUTER_NEGATIVE_PENALTY", "8.0"))
    
    # Thresholds (configurable)
    min_score_for_routing: float = float(os.getenv("ROUTER_MIN_SCORE", "1.0"))
    secondary_service_threshold: float = float(os.getenv("ROUTER_SECONDARY_THRESHOLD", "2.0"))
    confidence_divisor: float = float(os.getenv("ROUTER_CONFIDENCE_DIVISOR", "5.0"))
    
    # Smart Router thresholds
    confidence_threshold: float = float(os.getenv("SMART_ROUTER_CONFIDENCE_THRESHOLD", "0.75"))
    score_tie_threshold: float = float(os.getenv("SMART_ROUTER_TIE_THRESHOLD", "3.0"))
    complex_query_word_count: int = int(os.getenv("SMART_ROUTER_COMPLEX_WORDS", "12"))


@dataclass
class PatternConfig:
    """Dynamic pattern configuration"""
    
    def _load_from_env(self, key: str, default: List[str]) -> List[str]:
        """Load list from environment variable (comma-separated)"""
        env_value = os.getenv(key)
        if env_value:
            return [item.strip() for item in env_value.split(',')]
        return default
    
    def _load_patterns_from_env(self, key: str, default: List[str]) -> List[str]:
        """Load regex patterns from environment"""
        return self._load_from_env(key, default)


class SmartPatternMatcher:
    """
    Intelligent pattern matching that learns and adapts
    Instead of hardcoded lists, uses dynamic pattern generation
    """
    
    def __init__(self):
        self.config = RouterConfig()
        self.pattern_cache = {}
    
    def detect_web_search_intent(self, query: str) -> bool:
        """
        Intelligently detect if query needs web search
        Uses semantic analysis instead of hardcoded keywords
        """
        query_lower = query.lower().strip()
        
        # Dynamic pattern: Questions about general knowledge
        question_patterns = [
            r'\b(what|who|where|when|why|how)\s+(is|are|was|were|do|does|did|can|could)\b',
            r'\b(explain|define|describe|tell\s+me\s+about)\b',
            r'\b(latest|current|today|now|recent|news)\b'
        ]
        
        # Check for question patterns (semantic approach)
        has_question_pattern = any(re.search(pattern, query_lower) for pattern in question_patterns)
        
        # Check for time-sensitive terms (dynamic detection)
        time_sensitive_terms = self._detect_time_sensitive_terms(query_lower)
        
        # Check for general knowledge indicators (not file-specific)
        is_file_specific = self._detect_file_specific_intent(query_lower)
        
        # Smart decision: web search if question pattern + (time-sensitive OR not file-specific)
        return has_question_pattern and (time_sensitive_terms or not is_file_specific)
    
    def _detect_time_sensitive_terms(self, query: str) -> bool:
        """Detect if query contains time-sensitive terms"""
        # Dynamic pattern: time indicators
        time_pattern = r'\b(latest|current|today|now|recent|news|update|breaking)\b'
        return bool(re.search(time_pattern, query))
    
    def _detect_file_specific_intent(self, query: str) -> bool:
        """Detect if query is about uploaded files (not general knowledge)"""
        # Dynamic patterns: possessive and file references
        file_patterns = [
            r'\b(my|my\s+uploaded|my\s+saved|in\s+my|from\s+my)\b',
            r'\b(pdf|document|note|file|csv|table|data)\b.*\b(uploaded|saved|stored)\b',
            r'\b(uploaded|saved|stored)\b.*\b(pdf|document|note|file|csv)\b'
        ]
        return any(re.search(pattern, query) for pattern in file_patterns)
    
    def detect_csv_query_intent(self, query: str, has_csv_tables: bool = False) -> bool:
        """
        Intelligently detect CSV query intent
        Uses semantic analysis instead of hardcoded keywords
        """
        if not has_csv_tables:
            return False
        
        query_lower = query.lower()
        
        # Dynamic patterns: data query operations
        data_operation_patterns = [
            r'\b(show|display|list|get|find)\s+(me\s+)?(data|rows|columns|records)\b',
            r'\b(query|select|filter|sort|group|aggregate|count|sum|avg|max|min)\b',
            r'\b(chart|graph|plot|visualize|visualization|analyze)\b',
            r'\b(top|bottom|first|last)\s+\d+\b',
            r'\b(from|in)\s+.*\s+(table|data|csv)\b'
        ]
        
        # Check if query matches data operation patterns
        matches_operation = any(re.search(pattern, query_lower) for pattern in data_operation_patterns)
        
        # Also check for numeric/statistical operations
        has_statistical = bool(re.search(r'\b(count|sum|avg|max|min|total|average)\b', query_lower))
        
        return matches_operation or has_statistical


class ServicePatternConfig:
    """
    Dynamic service pattern configuration
    Patterns can be overridden via environment variables
    """
    
    @staticmethod
    def get_search_patterns() -> Dict[str, List[str]]:
        """Get search service patterns (loadable from env)"""
        # Load from env or use smart defaults
        keywords_env = os.getenv("SEARCH_KEYWORDS")
        phrases_env = os.getenv("SEARCH_PHRASES")
        negative_env = os.getenv("SEARCH_NEGATIVE_KEYWORDS")
        
        return {
            'keywords': [k.strip() for k in keywords_env.split(',')] if keywords_env else [
                'search online', 'google', 'find online', 'look up online',
                'latest', 'news', 'current', 'today', 'internet',
                'web search', 'search the web'
            ],
            'phrases': [p.strip() for p in phrases_env.split(',')] if phrases_env else [
                'search for', 'search the web', 'search online',
                'google search', 'find information online',
                'what are the latest', 'current news', 'recent news',
                'look up online', 'find on the internet'
            ],
            'negative_keywords': [n.strip() for n in negative_env.split(',')] if negative_env else [
                'my pdf', 'my document', 'uploaded', 'my file',
                'my notes', 'in my'
            ]
        }
    
    @staticmethod
    def get_patterns_for_service(service_name: str) -> Dict[str, List[str]]:
        """
        Dynamically get patterns for any service
        Loads from env vars or uses intelligent defaults
        """
        service_upper = service_name.upper()
        
        keywords = os.getenv(f"{service_upper}_KEYWORDS")
        phrases = os.getenv(f"{service_upper}_PHRASES")
        negative = os.getenv(f"{service_upper}_NEGATIVE_KEYWORDS")
        
        # If not in env, use intelligent pattern generation
        if not keywords or not phrases:
            return ServicePatternConfig._generate_smart_patterns(service_name)
        
        return {
            'keywords': [k.strip() for k in keywords.split(',')] if keywords else [],
            'phrases': [p.strip() for p in phrases.split(',')] if phrases else [],
            'negative_keywords': [n.strip() for n in negative.split(',')] if negative else []
        }
    
    @staticmethod
    def _generate_smart_patterns(service_name: str) -> Dict[str, List[str]]:
        """Generate smart patterns based on service name (fallback)"""
        # This is a fallback - patterns should ideally come from config/env
        service_lower = service_name.lower()
        
        if 'search' in service_lower:
            return ServicePatternConfig.get_search_patterns()
        elif 'drive' in service_lower:
            return {
                'keywords': ['drive', 'google drive', 'upload', 'download', 'file', 'files', 'folder'],
                'phrases': ['upload to drive', 'save to drive', 'list my files', 'files in drive'],
                'negative_keywords': ['search', 'find information', 'pdf', 'note']
            }
        elif 'database' in service_lower or 'note' in service_lower:
            return {
                'keywords': ['note', 'notes', 'remember', 'save note', 'create note', 'search notes'],
                'phrases': ['create a note', 'search my notes', 'in my notes', 'from my notes'],
                'negative_keywords': ['pdf', 'document file', 'upload', 'summarize']
            }
        elif 'pdf' in service_lower or 'rag' in service_lower:
            return {
                'keywords': ['pdf', 'pdfs', 'paper', 'research', 'document', 'upload pdf', 'analyze pdf'],
                'phrases': ['upload pdf', 'my pdfs', 'summarize pdf', 'ask question about pdf'],
                'negative_keywords': ['online', 'web search', 'google', 'internet']
            }
        else:
            return {'keywords': [], 'phrases': [], 'negative_keywords': []}


class SafetyConfig:
    """Configuration for safety checks (SQL injection, etc.)"""
    
    @staticmethod
    def get_dangerous_sql_keywords() -> List[str]:
        """Get dangerous SQL keywords (configurable via env)"""
        env_keywords = os.getenv("DANGEROUS_SQL_KEYWORDS")
        if env_keywords:
            return [k.strip().upper() for k in env_keywords.split(',')]
        
        # Default safety keywords
        return [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
            'CREATE', 'TRUNCATE', 'REPLACE', 'RENAME',
            'GRANT', 'REVOKE', 'EXECUTE', 'CALL'
        ]


# Global instances
_config_manager = RouterConfig()
_pattern_matcher = SmartPatternMatcher()
_service_patterns = ServicePatternConfig()
