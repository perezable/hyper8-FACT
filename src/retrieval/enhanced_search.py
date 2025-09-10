"""
Enhanced Search Module for FACT System

Optimized for small knowledge bases (<20MB) with ultra-low latency
requirements for voice agent integration. Combines multiple retrieval
strategies for high precision.
"""

import re
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict, Counter
import numpy as np
import structlog
from difflib import SequenceMatcher
from functools import lru_cache

logger = structlog.get_logger(__name__)


@dataclass
class SearchResult:
    """Represents a search result with scoring details."""
    id: int
    question: str
    answer: str
    category: str
    state: Optional[str]
    score: float
    match_type: str  # exact, fuzzy, semantic, keyword
    confidence: float
    retrieval_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class QueryPreprocessor:
    """Preprocess and normalize queries for better matching."""
    
    def __init__(self):
        """Initialize the preprocessor with common patterns."""
        # Common abbreviations and their expansions
        self.abbreviations = {
            "lic": "license",
            "req": "requirements",
            "reqs": "requirements",
            "gc": "general contractor",
            "ga": "georgia",
            "ca": "california",
            "fl": "florida",
            "tx": "texas",
            "ny": "new york",
            "exam": "examination",
            "info": "information",
            "cert": "certification",
            "app": "application",
            "exp": "experience",
            "ins": "insurance",
            "bond": "bonding"
        }
        
        # Common synonyms for contractor licensing domain
        self.synonyms = {
            "license": ["permit", "certification", "credential", "authorization", "licensing"],
            "requirements": ["prerequisites", "qualifications", "criteria", "needs"],
            "contractor": ["builder", "construction professional", "tradesperson"],
            "cost": ["fee", "price", "expense", "charge", "payment", "costs"],
            "test": ["exam", "examination", "assessment", "evaluation"],
            "get": ["obtain", "acquire", "secure", "receive"],
            "need": ["require", "must have", "necessary", "essential"],
            "help": ["assist", "guide", "support", "aid"],
            "state": ["location", "jurisdiction", "region", "area"],
            "roi": ["return", "investment", "payback", "profit"],
            "diy": ["yourself", "self", "own"],
            "workers": ["worker", "workman", "workmans"],
            "comp": ["compensation", "insurance"],
            "fail": ["failure", "failed", "failing", "unsuccessful"]
        }
        
        # Stop words to remove for keyword extraction
        self.stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "can", "shall", "i", "me",
            "my", "you", "your", "he", "she", "it", "we", "they", "what", "which",
            "who", "when", "where", "why", "how", "this", "that", "these", "those"
        }
        
        # Common question patterns
        self.question_patterns = [
            (r"^(what|what's|whats)\s+(are|is)\s+(.+)", r"\3"),
            (r"^(how)\s+(do|does|can)\s+i\s+(.+)", r"\3"),
            (r"^(tell|show)\s+me\s+about\s+(.+)", r"\2"),
            (r"^i\s+need\s+(help|info|information)\s+(with|about|on)\s+(.+)", r"\3"),
            (r"^(can|could)\s+you\s+(explain|tell)\s+(.+)", r"\3")
        ]
    
    def normalize(self, text: str) -> str:
        """Normalize text for consistent matching."""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation except hyphens in words
        text = re.sub(r'[^\w\s-]|(?<!\w)-(?!\w)', ' ', text)
        
        # Expand abbreviations
        for abbrev, expansion in self.abbreviations.items():
            text = re.sub(r'\b' + abbrev + r'\b', expansion, text)
        
        return text.strip()
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        normalized = self.normalize(text)
        words = normalized.split()
        
        # Remove stop words
        keywords = [w for w in words if w not in self.stop_words and len(w) > 2]
        
        # Add synonyms for important keywords
        expanded_keywords = []
        for keyword in keywords:
            expanded_keywords.append(keyword)
            if keyword in self.synonyms:
                expanded_keywords.extend(self.synonyms[keyword][:2])  # Add top 2 synonyms
        
        return list(set(expanded_keywords))
    
    def simplify_question(self, text: str) -> str:
        """Simplify question by removing common patterns."""
        normalized = self.normalize(text)
        
        for pattern, replacement in self.question_patterns:
            match = re.match(pattern, normalized)
            if match:
                return match.expand(replacement).strip()
        
        return normalized
    
    def generate_query_variations(self, query: str) -> List[str]:
        """Generate variations of a query for better matching."""
        variations = [query]
        normalized = self.normalize(query)
        variations.append(normalized)
        
        # Simplified version
        simplified = self.simplify_question(query)
        if simplified != normalized:
            variations.append(simplified)
        
        # Keywords only
        keywords = self.extract_keywords(query)
        if keywords:
            variations.append(" ".join(keywords))
        
        # With synonyms
        for word, syns in self.synonyms.items():
            if word in normalized:
                for syn in syns[:1]:  # Use top synonym
                    variation = normalized.replace(word, syn)
                    variations.append(variation)
        
        return list(set(variations))


class FuzzyMatcher:
    """Fuzzy string matching for typo tolerance."""
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return FuzzyMatcher.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def similarity_ratio(s1: str, s2: str) -> float:
        """Calculate similarity ratio between two strings (0-1)."""
        return SequenceMatcher(None, s1, s2).ratio()
    
    @staticmethod
    def token_similarity(s1: str, s2: str) -> float:
        """Calculate token-based similarity."""
        tokens1 = set(s1.lower().split())
        tokens2 = set(s2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def fuzzy_match_score(query: str, text: str, threshold: float = 0.3) -> float:
        """
        Calculate fuzzy match score combining multiple metrics.
        
        Returns score between 0 and 1, where 1 is perfect match.
        """
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Exact match
        if query_lower == text_lower:
            return 1.0
        
        # Substring match
        if query_lower in text_lower:
            return 0.9
        
        # Calculate different similarity metrics
        ratio = FuzzyMatcher.similarity_ratio(query_lower, text_lower)
        token_sim = FuzzyMatcher.token_similarity(query_lower, text_lower)
        
        # Check if all query tokens are in text
        query_tokens = set(query_lower.split())
        text_tokens = set(text_lower.split())
        all_tokens_present = query_tokens.issubset(text_tokens)
        
        # Weighted combination
        if all_tokens_present:
            score = 0.8
        else:
            score = (ratio * 0.6 + token_sim * 0.4)
        
        return score if score >= threshold else 0.0


class InMemoryIndex:
    """
    In-memory index for ultra-fast retrieval.
    Perfect for small knowledge bases that fit in memory.
    """
    
    def __init__(self):
        """Initialize the in-memory index."""
        self.entries = []  # List of all entries
        self.keyword_index = defaultdict(set)  # keyword -> set of entry IDs
        self.category_index = defaultdict(set)  # category -> set of entry IDs
        self.state_index = defaultdict(set)  # state -> set of entry IDs
        self.id_to_index = {}  # entry ID -> index in entries list
        self.preprocessor = QueryPreprocessor()
        self.fuzzy_matcher = FuzzyMatcher()
        self._initialized = False
    
    def build_index(self, entries: List[Dict[str, Any]]):
        """Build in-memory index from entries."""
        logger.info(f"Building in-memory index for {len(entries)} entries")
        
        self.entries = entries
        self.keyword_index.clear()
        self.category_index.clear()
        self.state_index.clear()
        self.id_to_index.clear()
        
        for idx, entry in enumerate(entries):
            entry_id = entry['id']
            self.id_to_index[entry_id] = idx
            
            # Index by category
            if entry.get('category'):
                self.category_index[entry['category'].lower()].add(entry_id)
            
            # Index by state
            if entry.get('state'):
                self.state_index[entry['state'].upper()].add(entry_id)
            
            # Extract and index keywords
            text = f"{entry.get('question', '')} {entry.get('answer', '')} {entry.get('tags', '')}"
            keywords = self.preprocessor.extract_keywords(text)
            
            for keyword in keywords:
                self.keyword_index[keyword].add(entry_id)
        
        self._initialized = True
        logger.info(f"Index built with {len(self.keyword_index)} unique keywords")
    
    def search(self, query: str, category: Optional[str] = None,
               state: Optional[str] = None, limit: int = 5) -> List[SearchResult]:
        """
        Search the in-memory index with multiple strategies.
        
        Returns top results sorted by relevance score.
        """
        if not self._initialized:
            return []
        
        import time
        start_time = time.time()
        
        # Generate query variations
        query_variations = self.preprocessor.generate_query_variations(query)
        query_keywords = self.preprocessor.extract_keywords(query)
        
        # Add individual words from query as keywords if short query
        query_words = query.lower().split()
        if len(query_words) <= 5:
            for word in query_words:
                if word not in self.preprocessor.stop_words and len(word) > 2:
                    if word not in query_keywords:
                        query_keywords.append(word)
        
        # Score each entry
        scores = defaultdict(float)
        match_types = {}
        
        # Get candidate entries based on filters
        candidate_ids = set(range(len(self.entries)))
        
        # Check if query mentions a state
        query_lower = query.lower()
        mentioned_state = None
        state_names = {
            'georgia': 'GA', 'california': 'CA', 'florida': 'FL', 
            'texas': 'TX', 'new york': 'NY', 'nevada': 'NV',
            'arizona': 'AZ', 'utah': 'UT', 'oregon': 'OR'
        }
        for state_name, state_code in state_names.items():
            if state_name in query_lower:
                mentioned_state = state_code
                break
        
        if category:
            category_ids = {self.id_to_index[id_] for id_ in self.category_index.get(category.lower(), set())}
            candidate_ids &= category_ids
        
        if state:
            state_ids = {self.id_to_index[id_] for id_ in self.state_index.get(state.upper(), set())}
            candidate_ids &= state_ids
        
        # Score each candidate
        for idx in candidate_ids:
            entry = self.entries[idx]
            entry_id = entry['id']
            
            # Check exact match
            if query.lower() == entry.get('question', '').lower():
                scores[entry_id] = 1.0
                match_types[entry_id] = 'exact'
                continue
            
            # Fuzzy matching on question
            question_score = self.fuzzy_matcher.fuzzy_match_score(
                query, entry.get('question', ''), threshold=0.3
            )
            
            # Also check fuzzy matching on answer
            answer_score = self.fuzzy_matcher.fuzzy_match_score(
                query, entry.get('answer', ''), threshold=0.3
            )
            
            # Keyword matching on combined text
            entry_text = f"{entry.get('question', '')} {entry.get('answer', '')} {entry.get('tags', '')}"
            keyword_score = self._calculate_keyword_score(query_keywords, entry_text)
            
            # Check for query variations
            variation_score = 0.0
            for variation in query_variations:
                if variation.lower() in entry_text.lower():
                    variation_score = max(variation_score, 0.7)
            
            # Combine scores - include answer score
            total_score = (
                max(question_score, answer_score) * 0.4 +
                keyword_score * 0.4 +
                variation_score * 0.2
            )
            
            # Boost score if state matches
            if mentioned_state and entry.get('state') == mentioned_state:
                total_score *= 1.5
            
            if total_score > 0.1:  # Very low threshold to catch more results
                scores[entry_id] = total_score
                if question_score > 0.7:
                    match_types[entry_id] = 'fuzzy'
                elif keyword_score > 0.5:
                    match_types[entry_id] = 'keyword'
                else:
                    match_types[entry_id] = 'partial'
        
        # Sort by score and create results
        # Return more results if scores are close
        sorted_entries = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # If we have results but low scores, include more
        if sorted_entries and sorted_entries[0][1] < 0.5:
            sorted_entries = sorted_entries[:min(limit * 2, len(sorted_entries))]
        else:
            sorted_entries = sorted_entries[:limit]
        
        results = []
        elapsed_ms = (time.time() - start_time) * 1000
        
        for entry_id, score in sorted_entries:
            idx = self.id_to_index[entry_id]
            entry = self.entries[idx]
            
            results.append(SearchResult(
                id=entry_id,
                question=entry['question'],
                answer=entry['answer'],
                category=entry['category'],
                state=entry.get('state'),
                score=score,
                match_type=match_types.get(entry_id, 'partial'),
                confidence=min(score * 1.2, 1.0),  # Boost confidence slightly
                retrieval_time_ms=elapsed_ms / len(sorted_entries) if sorted_entries else elapsed_ms,
                metadata={
                    'keywords_matched': len([k for k in query_keywords if k in entry.get('question', '').lower()]),
                    'query_variations_used': len(query_variations)
                }
            ))
        
        return results
    
    def _calculate_keyword_score(self, query_keywords: List[str], text: str) -> float:
        """Calculate keyword-based relevance score."""
        if not query_keywords:
            return 0.0
        
        text_lower = text.lower()
        text_words = set(text_lower.split())
        matched = 0
        partial_matched = 0
        
        for keyword in query_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text_lower:
                matched += 1
            else:
                # Check for partial matches
                for word in text_words:
                    if keyword_lower in word or word in keyword_lower:
                        partial_matched += 0.5
                        break
        
        total_score = (matched + partial_matched) / len(query_keywords)
        return min(total_score, 1.0)


class EnhancedRetriever:
    """
    Enhanced retriever combining multiple search strategies.
    Optimized for voice agent use cases with <20MB knowledge bases.
    """
    
    def __init__(self, db_manager=None):
        """Initialize the enhanced retriever."""
        self.db_manager = db_manager
        self.in_memory_index = InMemoryIndex()
        self.preprocessor = QueryPreprocessor()
        self.fuzzy_matcher = FuzzyMatcher()
        self._cache = {}  # Simple query cache
        self._cache_ttl = timedelta(minutes=5)
        self._last_cache_clear = datetime.now()
        
    async def initialize(self):
        """Load knowledge base into memory for fast retrieval."""
        try:
            logger.info("Enhanced retriever initialize() called")
            
            # Try PostgreSQL first if available
            try:
                from db.postgres_adapter import postgres_adapter
                if postgres_adapter and postgres_adapter.initialized:
                    logger.info("Loading from PostgreSQL")
                    entries = await postgres_adapter.get_all_entries()
                    
                    if entries:
                        # Build in-memory index
                        self.in_memory_index.build_index(entries)
                        logger.info(f"Enhanced retriever initialized with {len(entries)} entries from PostgreSQL")
                        return
            except ImportError:
                pass
            
            # Load all entries from database
            if self.db_manager:
                logger.info("Using db_manager for connection")
                async with self.db_manager.get_connection() as conn:
                    cursor = await conn.execute("""
                        SELECT id, question, answer, category, tags, state, priority, difficulty
                        FROM knowledge_base
                    """)
                    rows = await cursor.fetchall()
            else:
                logger.info("No db_manager, using direct connection")
                # Direct SQLite connection if no db_manager
                try:
                    import aiosqlite
                    import os
                    db_path = os.getenv("DATABASE_PATH", "data/fact_system.db")
                    logger.info(f"Trying aiosqlite with path: {db_path}")
                    
                    # Check if database file exists
                    if not os.path.exists(db_path):
                        logger.warning(f"Database file not found at {db_path}")
                        # Try without data/ prefix for Railway
                        db_path = "fact_system.db"
                        logger.info(f"Trying alternative path: {db_path}")
                    
                    async with aiosqlite.connect(db_path) as conn:
                        cursor = await conn.execute("""
                            SELECT id, question, answer, category, tags, state, priority, difficulty
                            FROM knowledge_base
                        """)
                        rows = await cursor.fetchall()
                        logger.info(f"Loaded {len(rows)} rows with aiosqlite")
                except ImportError as e:
                    logger.warning(f"aiosqlite not available: {e}")
                    # Fallback to sync sqlite if aiosqlite not available
                    import sqlite3
                    import os
                    db_path = os.getenv("DATABASE_PATH", "data/fact_system.db")
                    
                    # Check if database file exists
                    if not os.path.exists(db_path):
                        db_path = "fact_system.db"
                        logger.info(f"Using alternative path: {db_path}")
                    
                    logger.info(f"Using sync sqlite3 with path: {db_path}")
                    conn = sqlite3.connect(db_path)
                    cursor = conn.execute("""
                        SELECT id, question, answer, category, tags, state, priority, difficulty
                        FROM knowledge_base
                    """)
                    rows = cursor.fetchall()
                    conn.close()
                    logger.info(f"Loaded {len(rows)} rows with sqlite3")
                
                entries = []
                for row in rows:
                    entries.append({
                        'id': row[0],
                        'question': row[1],
                        'answer': row[2],
                        'category': row[3],
                        'tags': row[4],
                        'state': row[5],
                        'priority': row[6],
                        'difficulty': row[7]
                    })
                
                # Build in-memory index
                self.in_memory_index.build_index(entries)
                logger.info(f"Enhanced retriever initialized with {len(entries)} entries")
                
        except Exception as e:
            logger.error(f"Failed to initialize enhanced retriever: {e}")
            raise
    
    def _get_cache_key(self, query: str, **kwargs) -> str:
        """Generate cache key for query."""
        params = json.dumps(kwargs, sort_keys=True)
        key_string = f"{query}:{params}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _clear_expired_cache(self):
        """Clear expired cache entries."""
        now = datetime.now()
        if now - self._last_cache_clear > timedelta(minutes=1):
            expired_keys = [
                key for key, (timestamp, _) in self._cache.items()
                if now - timestamp > self._cache_ttl
            ]
            for key in expired_keys:
                del self._cache[key]
            self._last_cache_clear = now
    
    async def search(self, query: str, category: Optional[str] = None,
                    state: Optional[str] = None, limit: int = 5,
                    use_cache: bool = True) -> List[SearchResult]:
        """
        Enhanced search with multiple retrieval strategies.
        
        Optimized for voice agents with:
        - Ultra-low latency (<10ms typical)
        - High precision for common variations
        - Graceful degradation for edge cases
        """
        # Check cache
        if use_cache:
            self._clear_expired_cache()
            cache_key = self._get_cache_key(query, category=category, state=state, limit=limit)
            if cache_key in self._cache:
                timestamp, results = self._cache[cache_key]
                logger.debug(f"Cache hit for query: {query[:50]}")
                return results
        
        # Perform search using in-memory index
        results = self.in_memory_index.search(query, category, state, limit)
        
        # Cache results
        if use_cache and results:
            cache_key = self._get_cache_key(query, category=category, state=state, limit=limit)
            self._cache[cache_key] = (datetime.now(), results)
        
        return results
    
    async def get_similar_questions(self, question: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Find similar questions for suggestion/autocomplete."""
        results = await self.search(question, limit=limit)
        return [
            {
                'question': r.question,
                'similarity': r.score,
                'category': r.category
            }
            for r in results
        ]
    
    async def refresh_index(self):
        """Refresh the in-memory index with latest data."""
        await self.initialize()
        self._cache.clear()
        logger.info("Enhanced retriever index refreshed")


# Convenience function for testing
async def test_enhanced_search():
    """Test the enhanced search functionality."""
    from db.connection import DatabaseManager
    
    db_manager = DatabaseManager("data/fact_system.db")
    retriever = EnhancedRetriever(db_manager)
    
    await retriever.initialize()
    
    # Test queries
    test_queries = [
        "Georgia contractor license requirements",
        "how do i get a license in georgia",
        "GA licence reqs",  # With typo and abbreviation
        "contractor permit georgia",  # Using synonym
        "what's needed for georgia GC"  # Casual with abbreviation
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        results = await retriever.search(query, limit=3)
        for r in results:
            print(f"  [{r.score:.2f}] {r.question[:60]}... ({r.match_type})")
    
    await db_manager.cleanup()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enhanced_search())