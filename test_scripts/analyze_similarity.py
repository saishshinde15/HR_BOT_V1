#!/usr/bin/env python3
"""
Test to see keyword extraction and similarity scores for failed matches.
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from hr_bot.utils.cache import ResponseCache

def analyze_similarity():
    """Analyze why queries don't match"""
    
    print("\n" + "="*80)
    print("🔬 SIMILARITY ANALYSIS")
    print("="*80)
    
    cache = ResponseCache(
        cache_dir="storage/response_cache",
        similarity_threshold=0.75
    )
    
    # Test query that failed
    test_queries = [
        ("Tell me about sick leave", "What is the sick leave policy?"),
        ("How does sick leave work?", "What is the sick leave policy?"),
        ("What's the sick day policy?", "What is the sick leave policy?"),
        ("How to request vacation?", "How do I request vacation time?"),
        ("Tell me about paternity leave", "How do I request paternity leave?")
    ]
    
    for test_query, cached_query in test_queries:
        print(f"\n{'='*80}")
        print(f"Test Query: '{test_query}'")
        print(f"Cached Query: '{cached_query}'")
        print('-'*80)
        
        test_keywords = cache._extract_keywords(test_query)
        cached_keywords = cache._extract_keywords(cached_query)
        
        print(f"Test Keywords: {test_keywords}")
        print(f"Cached Keywords: {cached_keywords}")
        
        similarity = cache._calculate_similarity(test_keywords, cached_keywords)
        print(f"\n💯 Similarity Score: {similarity:.2%}")
        print(f"   Threshold: {cache.similarity_threshold:.2%}")
        
        if similarity >= cache.similarity_threshold:
            print("   ✅ WOULD MATCH")
        else:
            print(f"   ❌ BELOW THRESHOLD (need {(cache.similarity_threshold - similarity)*100:.1f}% more)")
        
        # Show overlap
        intersection = test_keywords.intersection(cached_keywords)
        print(f"   Common words: {intersection}")
    
    print("\n" + "="*80)
    print("💡 RECOMMENDATIONS:")
    print("="*80)
    print("Current threshold: 0.75 (75% similarity required)")
    print("Suggestion: Lower to 0.60-0.65 (60-65% similarity)")
    print("This will match more variations while maintaining quality")
    print("="*80 + "\n")

if __name__ == "__main__":
    analyze_similarity()
