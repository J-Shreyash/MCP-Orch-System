"""
Intent Router - PRODUCTION OPTIMIZED
Intelligent routing with better accuracy for document listing and PDF queries
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav

IMPROVEMENTS:
✅ Better document listing detection
✅ Improved PDF vs Notes distinction
✅ Enhanced context understanding
✅ More accurate routing scores
✅ Smart configuration (no hardcoding)
"""

import re
from typing import Dict, List, Optional
from enum import Enum

# Import smart configuration
try:
    from config_manager import ServicePatternConfig, RouterConfig
    SMART_CONFIG_AVAILABLE = True
except ImportError:
    SMART_CONFIG_AVAILABLE = False
    print("⚠️  Smart config not available, using defaults")


class MCPService(Enum):
    """Available MCP Services"""
    SEARCH = "search"
    DRIVE = "drive"
    DATABASE = "database"
    RAG_PDF = "rag_pdf"
    GENERAL = "general"


class IntentRouter:
    """
    OPTIMIZED: Intelligent router with smart configuration (no hardcoding)
    """
    
    def __init__(self):
        """Initialize Intent Router with smart configuration"""
        # Load configuration
        if SMART_CONFIG_AVAILABLE:
            self.config = RouterConfig()
            self.patterns = self._initialize_patterns_smart()
        else:
            self.config = None
            self.patterns = self._initialize_patterns()
        print("🧠 Intent Router initialized (SMART CONFIG)")
    
    def _initialize_patterns_smart(self) -> Dict:
        """Initialize patterns using smart configuration (no hardcoding)"""
        patterns = {}
        
        # Dynamically load patterns for each service
        for service in MCPService:
            if service == MCPService.GENERAL:
                continue
            
            service_name = service.value
            patterns[service] = ServicePatternConfig.get_patterns_for_service(service_name)
        
        return patterns
    
    def _initialize_patterns(self) -> Dict:
        """Fallback: Initialize enhanced keyword patterns (when config not available)"""
        return {
            MCPService.SEARCH: {
                'keywords': [
                    'search online', 'google', 'find online', 'look up online',
                    'latest', 'news', 'current', 'today', 'internet',
                    'web search', 'search the web'
                ],
                'phrases': [
                    'search for', 'search the web', 'search online',
                    'google search', 'find information online',
                    'what are the latest', 'current news', 'recent news',
                    'look up online', 'find on the internet'
                ],
                'negative_keywords': [
                    'my pdf', 'my document', 'uploaded', 'my file',
                    'my notes', 'in my'
                ]
            },
            
            MCPService.DRIVE: {
                'keywords': [
                    'drive', 'google drive', 'upload', 'download',
                    'file', 'files', 'folder'
                ],
                'phrases': [
                    'upload to drive', 'save to drive', 'upload file',
                    'list my files', 'show my files', 'files in drive',
                    'download from drive', 'get from drive'
                ],
                'negative_keywords': ['search', 'find information', 'pdf', 'note']
            },
            
            MCPService.DATABASE: {
                'keywords': [
                    'note', 'notes', 'remember', 'save note',
                    'create note', 'store note', 'add note',
                    'search notes', 'find note', 'my notes',
                    'in my notes', 'from my notes', 'budget',
                    'meeting', 'reminder', 'information'
                ],
                'phrases': [
                    'create a note', 'save this note', 'remember this',
                    'search my notes', 'find in notes', 'add to notes',
                    'in my notes', 'from my notes', 'my saved notes',
                    'what is in my notes', 'search for in notes',
                    'list all notes', 'show my notes'
                ],
                'negative_keywords': ['pdf', 'document file', 'upload', 'summarize']
            },
            
            MCPService.RAG_PDF: {
                'keywords': [
                    'pdf', 'pdfs', 'paper', 'research', 'document',
                    'upload pdf', 'analyze pdf', 'summarize', 'summary',
                    'my pdf', 'the pdf', 'this pdf', 'uploaded',
                    'findings', 'conclusion', 'book', 'article',
                    'list pdfs', 'all pdfs', 'my documents',
                    'list all documents', 'show all documents',
                    'list all my', 'show all my', 'all uploaded'
                ],
                'phrases': [
                    'upload pdf', 'upload this pdf', 'process pdf',
                    'what pdfs', 'my pdfs', 'pdf files', 'my pdf',
                    'summarize pdf', 'summarize this', 'give me a summary',
                    'what are the findings', 'what does the paper say',
                    'according to the pdf', 'in the document', 'in my pdf',
                    'ask question about', 'question about pdf',
                    'uploaded pdf', 'uploaded document',
                    'list all documents', 'show all documents',
                    'list my documents', 'all my documents',
                    'list all pdfs', 'show all pdfs', 'all uploaded',
                    'list everything', 'show everything'
                ],
                'negative_keywords': ['online', 'web search', 'google', 'internet']
            }
        }
    
    def route(self, query: str) -> Dict:
        """
        OPTIMIZED: Analyze query with better accuracy
        
        Args:
            query: User's natural language query
            
        Returns:
            Dictionary with routing information
        """
        query_lower = query.lower()
        
        # CRITICAL: Check for "list all" queries FIRST
        if self._is_list_all_query(query_lower):
            return {
                'primary_service': MCPService.RAG_PDF,
                'secondary_services': [MCPService.DATABASE],
                'intent': 'list_all_documents',
                'parameters': {'include_notes': 'note' in query_lower or 'all' in query_lower},
                'confidence': 1.0,
                'original_query': query
            }
        
        # Calculate scores for each service
        scores = {
            MCPService.SEARCH: self._calculate_score(query_lower, MCPService.SEARCH),
            MCPService.DRIVE: self._calculate_score(query_lower, MCPService.DRIVE),
            MCPService.DATABASE: self._calculate_score(query_lower, MCPService.DATABASE),
            MCPService.RAG_PDF: self._calculate_score(query_lower, MCPService.RAG_PDF)
        }
        
        # Determine primary service
        primary_service = max(scores, key=scores.get)
        primary_score = scores[primary_service]
        
        # Get thresholds from config or use defaults
        min_score = self.config.min_score_for_routing if self.config else 1.0
        secondary_threshold = self.config.secondary_service_threshold if self.config else 2.0
        confidence_divisor = self.config.confidence_divisor if self.config else 5.0
        
        # If score is too low, classify as general conversation
        if primary_score < min_score:
            primary_service = MCPService.GENERAL
        
        # Determine secondary services
        secondary_services = [
            service for service, score in scores.items()
            if score >= secondary_threshold and service != primary_service
        ]
        
        # Extract intent
        intent = self._extract_intent(query_lower, primary_service)
        
        # Extract parameters
        parameters = self._extract_parameters(query, primary_service, intent)
        
        # Use configurable confidence divisor
        confidence_divisor = self.config.confidence_divisor if self.config else 5.0
        confidence = min(primary_score / confidence_divisor, 1.0)
        
        result = {
            'primary_service': primary_service,
            'secondary_services': secondary_services,
            'intent': intent,
            'parameters': parameters,
            'confidence': confidence,
            'original_query': query
        }
        
        print(f"🎯 Routing: {primary_service.value} (confidence: {result['confidence']:.2f})")
        print(f"   Intent: {intent}")
        print(f"   Scores: PDF={scores[MCPService.RAG_PDF]:.1f}, Notes={scores[MCPService.DATABASE]:.1f}, Search={scores[MCPService.SEARCH]:.1f}, Drive={scores[MCPService.DRIVE]:.1f}")
        
        return result
    
    def _is_list_all_query(self, query: str) -> bool:
        """
        CRITICAL: Detect "list all" type queries
        """
        list_patterns = [
            r'\b(list|show)\s+(all|my|everything)\b',
            r'\ball\s+(documents|pdfs|files|notes|uploaded)\b',
            r'\bshow\s+(everything|all)\b',
            r'\blist\s+(everything|all)\b',
            r'\bmy\s+(documents|pdfs|files)\b',
            r'\buploaded\s+(documents|pdfs|files)\b'
        ]
        
        for pattern in list_patterns:
            if re.search(pattern, query):
                return True
        
        return False
    
    def _calculate_score(self, query: str, service: MCPService) -> float:
        """
        SMART: Calculate relevance score using configurable weights (no hardcoding)
        """
        score = 0.0
        patterns = self.patterns[service]
        
        # Get weights from config or use defaults
        negative_penalty = self.config.negative_penalty if self.config else 8.0
        phrase_weight = self.config.phrase_weight if self.config else 6.0
        keyword_weight = self.config.keyword_weight if self.config else 2.5
        
        # Check for negative keywords first (strong disqualifiers)
        negative_keywords = patterns.get('negative_keywords', [])
        for neg_keyword in negative_keywords:
            if neg_keyword in query:
                score -= negative_penalty
        
        # Check phrases (highest weight)
        for phrase in patterns.get('phrases', []):
            if phrase in query:
                score += phrase_weight
        
        # Check keywords (medium weight)
        for keyword in patterns.get('keywords', []):
            if re.search(rf'\b{re.escape(keyword)}\b', query):
                score += keyword_weight
        
        return max(score, 0.0)
    
    def _extract_intent(self, query: str, service: MCPService) -> str:
        """Extract specific intent for the service"""
        if service == MCPService.SEARCH:
            return "web_search"
        
        elif service == MCPService.DRIVE:
            if any(word in query for word in ['upload', 'save', 'store']):
                return "upload_file"
            elif any(word in query for word in ['list', 'show', 'files']):
                return "list_files"
            elif any(word in query for word in ['download', 'get']):
                return "download_file"
            elif any(word in query for word in ['delete', 'remove']):
                return "delete_file"
            else:
                return "list_files"
        
        elif service == MCPService.DATABASE:
            if any(word in query for word in ['create', 'add', 'store', 'save', 'remember']):
                return "create_document"
            elif any(word in query for word in ['search', 'find', 'look for']):
                return "search_documents"
            elif any(word in query for word in ['list', 'show', 'all']):
                return "list_documents"
            elif any(word in query for word in ['update', 'edit', 'modify']):
                return "update_document"
            elif any(word in query for word in ['delete', 'remove']):
                return "delete_document"
            else:
                return "search_documents"
        
        elif service == MCPService.RAG_PDF:
            if any(word in query for word in ['upload', 'add', 'process']):
                return "upload_pdf"
            elif any(word in query for word in ['summarize', 'summary']):
                return "summarize_pdf"
            elif any(word in query for word in ['list', 'show all', 'all pdfs', 'all documents']):
                return "list_pdfs"
            elif any(word in query for word in ['question', 'ask', 'what', 'how', 'why', 'explain', 'findings']):
                return "ask_question"
            elif any(word in query for word in ['search', 'find']):
                return "search_pdfs"
            else:
                return "ask_question"
        
        else:
            return "general_conversation"
    
    def _extract_parameters(self, query: str, service: MCPService, intent: str) -> Dict:
        """Extract parameters from query"""
        params = {}
        
        if service == MCPService.SEARCH:
            clean_query = query
            for trigger in ['search for', 'search', 'google', 'find online', 'look up']:
                clean_query = clean_query.replace(trigger, '', 1)
            
            params['query'] = clean_query.strip()
            params['num_results'] = 5
        
        elif service == MCPService.DATABASE:
            if intent == "search_documents":
                clean_query = query
                for trigger in ['search', 'find', 'look for', 'in my notes', 'from my notes']:
                    clean_query = clean_query.replace(trigger, '', 1)
                params['query'] = clean_query.strip()
                params['limit'] = 10
            
            elif intent == "create_document":
                params['category'] = 'general'
        
        elif service == MCPService.RAG_PDF:
            if intent == "ask_question":
                params['question'] = query
                params['max_context_chunks'] = 7
            elif intent == "list_pdfs":
                params['limit'] = 100
                params['include_notes'] = 'note' in query.lower()
        
        return params


def test_router():
    """Test the OPTIMIZED intent router"""
    print("\n" + "="*60)
    print("🧪 Testing OPTIMIZED Intent Router")
    print("="*60 + "\n")
    
    router = IntentRouter()
    
    test_queries = [
        "List all my uploaded documents",
        "Show all documents",
        "List all pdfs",
        "What are the key findings in my PDF?",
        "Search for Python programming tutorials",
        "Summarize the uploaded document",
        "What is the budget amount in my notes?",
        "Find information about quantum computing online",
        "Search my notes for meeting information"
    ]
    
    for query in test_queries:
        print(f"🔍 Query: {query}")
        result = router.route(query)
        print(f"   ✅ Service: {result['primary_service'].value}")
        print(f"   Intent: {result['intent']}")
        print(f"   Confidence: {result['confidence']:.2%}")
        if result.get('parameters'):
            print(f"   Parameters: {result['parameters']}")
        print()
    
    print("="*60)
    print("✅ Router Test Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    test_router()